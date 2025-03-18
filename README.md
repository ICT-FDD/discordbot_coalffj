# discordbot_coalffj
Bot discord qui résume les nouveau message du serveur Coalition FFJ et les envois par mail sur coalition_ffj@femmesdedroit.be (mailing list)


├─ requirements.txt						(librairies python nécessaires)
├─ Dockerfile							(configuration du conteneur)
├─ railway.toml							(configuration railway)
├─ .env									(variables d'environnement et tokens secret)
├─ bot/
│	├─ core.py							(script principal)
│	├─ channel_lists.py					(gestion des canaux importants / exclus)
│	├─ summarizer.py					(fonctionnalités de résumé)
│	├─ discord_bot_commands.py			(commandes du bot via Discord)
│	├─ mails_managment.py				(fonctions pour gérer les envois de mails prod/test)
│
├─ tests/
│  ├─ test_env.py						(fonctions de tests et controle)
│  ├─ test_channel_lists.py
│  ├─ test_summarizer.py
│  ├─ test_mails.py
│  └─ test_bot_integration.py
│
├─ data/
│   ├─ important_channels.txt			(liste des canaux important - messages intégrals)
│   ├─ excluded_channels.txt			(liste des canaux non surveillés)
│   ├─ daily_summary.txt				(daily report)
│   └─ weekly_summary.txt				(weekly report)

