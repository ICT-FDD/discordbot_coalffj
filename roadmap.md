# Roadmap

## Contexte général

Ce projet consiste à développer un bot Discord capable de :
- Surveiller certains canaux, classer et résumer les messages.
- Envoyer des rapports quotidiens par e-mail.
- Permettre la configuration dynamique de canaux importants / exclus, etc.

Ce fichier détaille les différentes étapes et fonctionnalités prévues (ou déjà implémentées).

---

## Étape 1 : Structure de base & Configuration

- [x] **Chargement des variables d'environnement** via `.env` (DISCORD_TOKEN, EMAIL_ADDRESS, etc.).
- [x] **Séparation du code** en modules (core, channel_lists, summarizer, mails_management, etc.).
- [x] **Tests unitaires** de base (lecture `.env`, lecture/écriture canaux, résumé de texte, envoi d'e-mails mocké).

**Statut** : Terminé ✓

---

## Étape 2 : Fonctionnalités Discord de base

- [x] **Connexion au bot** (on_ready, events).
- [x] **Collecte des messages** par canal (important vs général).
- [x] **Tâche planifiée** (daily_summary) pour envoyer un mail à heure fixe (23h UTC).
- [x] **Commandes** `!send_daily_summary`, `!preview_mail`, etc.

**Statut** : Terminé ✓  
**Reste à faire** : ajuster le fuseau horaire si besoin.

---

## Étape 3 : Paramétrages dynamiques via commandes

- [x] **Listes de canaux** importants/exclus chargées depuis des fichiers `.txt`.
- [x] **Commandes** `!add_important`, `!remove_important`, `!add_excluded`, `!remove_excluded`.
- [ ] Vérifier la **persistance** (si le service est relancé, on ne perd pas la config).  
  - **Option** : prévoir un volume persistant ou une base de données simple.

**Statut** : En cours

---

## Étape 4 : Améliorations & Bonus

- [ ] **Résumé plus intelligent** (modèles NLP, classement par sujets, etc.).
- [ ] **Interface web** minimaliste pour gérer la configuration (optionnel).
- [ ] **Multi-langue** (si besoin).
- [ ] **Gestion des erreurs** plus robuste (logs, alertes, etc.).

**Statut** : À planifier

---

## Étape 5 : Déploiement & Maintenance

- [ ] **Mise en prod** sur Railway (ou autre hébergeur), configuration du Dockerfile et du `railway.toml`.
- [ ] **Surveillance** (logs, redémarrages automatiques, etc.).
- [ ] **Documentation utilisateur** (README, tutoriels).

**Statut** : Planifié

---

### Prochaines étapes immédiates

1. Finaliser la persistance des canaux importants/exclus (fichiers ou base de données).
2. Vérifier la gestion des fuseaux horaires (pour l’envoi à 23h heure locale vs UTC).
3. Améliorer les tests d’intégration (simulateur de messages).

---

## Historique

- **v0.1** : premier prototype (bot.py monolithique).
- **v0.2** : architecture modulaire, tests unitaires de base.
- **v0.3** : ajout des commandes Discord, TDD plus complet.
- **v0.4** : déploiement sur Railway, correctifs Poetry/pip, etc.

*(À adapter et mettre à jour au fil du temps.)*
