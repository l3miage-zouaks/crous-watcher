#!/usr/bin/env python3
"""
Surveille une page de recherche de logement CROUS et envoie une notification
WhatsApp (via CallMeBot) dès qu'un nouveau logement apparaît.

Etat persistant : state.json (liste des IDs de logements déjà vus).
Ce fichier est commité dans le repo par le workflow GitHub Actions entre
deux exécutions, donc la mémoire persiste d'une exécution à l'autre.
"""

import json
import os
import re
import sys
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

# --- Configuration ---------------------------------------------------------

SEARCH_URL = os.environ.get(
    "CROUS_SEARCH_URL",
    "https://trouverunlogement.lescrous.fr/tools/47/search?"
    "bounds=5.703277587890625_45.79960567470238_6.087112426757813_45.46205707250824",
)

STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

ACCOMMODATION_RE = re.compile(r"/tools/\d+/accommodations/(\d+)")


# --- Scraping ---------------------------------------------------------------

def fetch_listings(url: str):
    """Retourne un dict {id_logement: infos} pour la page donnée."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    listings = {}
    for a in soup.find_all("a", href=True):
        m = ACCOMMODATION_RE.search(a["href"])
        if not m:
            continue
        listing_id = m.group(1)
        if listing_id in listings:
            continue

        # Le lien encadre généralement toute la "carte" du logement.
        container = a
        text = container.get_text(" ", strip=True)

        # Nom = souvent dans un titre à l'intérieur du lien
        title_tag = container.find(["h2", "h3"])
        name = title_tag.get_text(" ", strip=True) if title_tag else text[:60]

        full_url = urllib.parse.urljoin(url, a["href"])

        listings[listing_id] = {
            "name": name,
            "url": full_url,
            "raw_text": text[:300],
        }

    return listings


# --- Etat --------------------------------------------------------------------

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# --- Notification Telegram ---------------------------------------------------

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID manquants, notif non envoyée.")
        print("Message qui aurait été envoyé:\n", message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, data=payload, timeout=30)
        print("Telegram status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Erreur envoi Telegram:", e)


# --- Main ---------------------------------------------------------------------

def main():
    print(f"Vérification de {SEARCH_URL}")

    try:
        current = fetch_listings(SEARCH_URL)
    except Exception as e:
        print("Erreur lors de la récupération de la page:", e)
        sys.exit(0)  # on ne fait pas échouer le workflow pour un souci réseau ponctuel

    print(f"{len(current)} logement(s) trouvé(s) sur la page.")

    previous = load_state()
    previous_ids = set(previous.keys())
    current_ids = set(current.keys())

    new_ids = current_ids - previous_ids

    if new_ids:
        print(f"{len(new_ids)} nouveau(x) logement(s) détecté(s) : {new_ids}")
        lines = ["🏠 Nouveau(x) logement(s) CROUS disponible(s) !"]
        for lid in new_ids:
            info = current[lid]
            lines.append(f"- {info['name']}\n{info['url']}")
        message = "\n".join(lines)
        send_telegram(message)
    else:
        print("Aucun nouveau logement.")

    save_state(current)


if __name__ == "__main__":
    main()
