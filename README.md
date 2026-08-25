# CROUS Watcher — alerte Telegram

Surveille une page de recherche de logement sur trouverunlogement.lescrous.fr
et t'envoie un message Telegram dès qu'un **nouveau** logement apparaît.
Tourne sur GitHub Actions (gratuit), donc ça fonctionne même PC éteint.

## 1. Créer ton bot Telegram (2 minutes)

1. Ouvre Telegram, cherche le contact **@BotFather** (c'est le bot officiel
   de Telegram pour créer des bots).
2. Envoie-lui `/newbot`, puis suis les instructions (il te demande un nom
   et un nom d'utilisateur se terminant par "bot").
3. BotFather te donne un **token**, un texte du genre
   `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. C'est ton
   `TELEGRAM_BOT_TOKEN`. Garde-le précieusement, c'est un secret.
4. Cherche maintenant **ton propre bot** dans Telegram (avec le nom
   d'utilisateur que tu viens de choisir) et envoie-lui n'importe quel
   message, par exemple `salut`. C'est nécessaire pour qu'il puisse
   ensuite t'écrire.
5. Récupère ton `chat_id` en ouvrant cette URL dans un navigateur
   (remplace `<TOKEN>` par ton token) :
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Tu verras un JSON contenant `"chat":{"id":123456789,...}` — ce nombre
   est ton `TELEGRAM_CHAT_ID`.

C'est tout, pas besoin d'app tierce ni de service non-officiel : c'est
l'API officielle Telegram, gratuite et stable.

## 2. Créer le repo GitHub

1. Crée un compte GitHub gratuit si tu n'en as pas : https://github.com/join
2. Crée un nouveau repo (peut être **privé**), par exemple `crous-watcher`.
3. Mets-y tous les fichiers de ce dossier (monitor.py, requirements.txt,
   state.json, .github/workflows/monitor.yml, README.md).

   Le plus simple : depuis ton PC,
   ```
   cd crous-watcher
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TON_USER/crous-watcher.git
   git push -u origin main
   ```
   (Ou utilise l'upload de fichiers directement dans l'interface web de GitHub,
   sans ligne de commande.)

## 3. Configurer les secrets

Dans le repo GitHub : **Settings > Secrets and variables > Actions**

- Onglet **Secrets** → *New repository secret* :
  - `TELEGRAM_BOT_TOKEN` = le token reçu de BotFather
  - `TELEGRAM_CHAT_ID` = le chat_id récupéré via getUpdates

- Onglet **Variables** → *New repository variable* (optionnel, sinon l'URL
  par défaut dans monitor.py est utilisée) :
  - `CROUS_SEARCH_URL` = ton lien de recherche CROUS complet, ex :
    `https://trouverunlogement.lescrous.fr/tools/47/search?bounds=5.703277587890625_45.79960567470238_6.087112426757813_45.46205707250824`

## 4. Activer les Actions et tester

1. Va dans l'onglet **Actions** du repo, active les workflows si demandé.
2. Clique sur le workflow "Surveillance logement CROUS" → **Run workflow**
   pour le tester manuellement tout de suite.
3. Regarde les logs : tu dois voir le nombre de logements trouvés. Comme
   `state.json` est vide au départ, **le premier lancement va considérer tous
   les logements actuels comme "nouveaux"** et t'envoyer une notif pour
   chacun — c'est normal, c'est juste l'initialisation. Après ça, tu ne
   recevras une notif que pour les vrais nouveaux logements.

Ensuite ça tourne tout seul toutes les 10 minutes, 24h/24, même PC éteint.

## Notes importantes

- GitHub désactive automatiquement les workflows planifiés (cron) après
  **60 jours d'inactivité du repo** (aucun commit). Il suffira de refaire un
  petit commit ou de relancer manuellement si ça arrive.
- Le cron GitHub Actions n'est pas garanti à la minute près (peut avoir
  quelques minutes de retard en cas de forte charge sur GitHub), mais reste
  fiable pour ce type d'usage.
- Pense à modifier `CROUS_SEARCH_URL` si tu changes de zone de recherche.
