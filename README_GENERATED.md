# 🤖 Bot Discord Python – Déploiement Dockerisé avec CI/CD

Ce projet met en œuvre un bot Discord écrit en Python, déployé de manière totalement conteneurisée avec **Docker** et **Docker Compose**, et maintenu automatiquement à jour via une pipeline CI/CD libre avec **Woodpecker CI**. Il s’intègre dans une architecture GLO (Gratuite, Libre, Open-source), orientée vers la reproductibilité, la supervision et la portabilité.

---

## 🚀 Fonctionnalités principales

- Écrit en Python avec `discord.py`
- Conteneurisation via Docker (compatible ARM pour Raspberry Pi)
- Déploiement automatique via Git (CI/CD avec Woodpecker)
- Supervision avec **Uptime Kuma**
- Notifications via Webhooks Discord
- Interface de contrôle possible avec NiceGUI (optionnel)
- Script Bash pour installation rapide

---

## 📁 Arborescence du projet

```
.
├── docker-compose.yml
├── Dockerfile
├── bot/
│   ├── core.py
│   ├── discord_bot_commands.py
│   ├── env_config.py
│   ├── file_utils.py
│   ├── requirements.txt
│   └── .env
├── .woodpecker.yml
├── roadmap.md
├── TROUBLESHOOTING.md
├── init_bot_stack.sh
└── README.md
```

---

## 🐳 Lancer le projet

### 1. Cloner le dépôt

```bash
git clone https://github.com/seb-baudoux/discord-bot.git
cd discord-bot
```

### 2. Lancer la stack Docker

```bash
docker compose up -d --build
```

Les services suivants seront disponibles :

- **Bot Discord** en tâche de fond
- **Woodpecker CI** : http://localhost:8000
- **Uptime Kuma** : http://localhost:3001
- **Gitea (Git)** : http://localhost:3000

---

## 🔁 Pipeline CI/CD (Woodpecker)

Le pipeline est défini dans `.woodpecker.yml`. Il :

1. Exécute les tests unitaires (si présents)
2. Reconstruit l’image Docker
3. Redémarre les services automatiquement

Déclenché à chaque `git push` sur le dépôt Gitea.

---

## ✅ Script d’installation (optionnel)

Pour un Raspberry Pi ou serveur fraîchement installé :

```bash
chmod +x init_bot_stack.sh
./init_bot_stack.sh
```

---

## 📊 Supervision (Uptime Kuma)

Interface web accessible via : http://localhost:3001  
Permet de surveiller le statut du bot et d’être notifié en cas de panne.

---

## 🧪 Tests unitaires (facultatif mais recommandé)

Tu peux ajouter tes tests dans un fichier comme `test_core.py` et les intégrer au CI :

```bash
python -m unittest discover -s bot
```

---

## 🛠️ À faire (extrait de roadmap.md)

- Ajouter une interface web admin (NiceGUI ?)
- Centralisation des logs
- Ajout de tests automatisés
- Documentation des commandes du bot

---

## 🧭 Fichiers utiles

- `README.md` → Ce guide
- `TROUBLESHOOTING.md` → Résolution des problèmes courants
- `roadmap.md` → Suivi des idées et évolutions
- `.env` → Variables d’environnement du bot
- `docker-compose.yml` → Orchestration de tous les services

---

## 🧑‍💻 Auteur

Projet développé et maintenu par Sébastien Baudoux.

---

## 📝 Licence

Ce projet est distribué sous licence libre. Voir fichier `LICENSE`.