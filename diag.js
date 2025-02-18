sequenceDiagram
    participant User as Discord User
    participant Core as core.py
    participant Cmds as discord_bot_commands.py
    participant Env as env_config.py
    participant Lists as channel_lists.py
    participant Summ as summarizer.py
    participant Mail as mails_management.py

    User->>Core: (1) Lancement: python -m bot.core
    note over Core: 1) core.py exécute run_bot()

    Core->>Env: get_discord_token() <br/> (lit .env)
    Core->>Lists: load_channels() <br/> (important_channels.txt, etc.)
    Core->>Cmds: setup_bot_commands(bot, messages, important, excluded)
    note over Cmds: Enregistre !ping, !send_daily_summary, etc.
    
    Core->>Core: bot.run(token)
    note over Core: Boucle d'événements Discord commence
    
    User->>Core: (2) on_message() appelé pour chaque message
    Core->>Core: Classer le message en important/general
    
    User->>Core: (3) Taper !ping dans Discord
    note over Core: bot.process_commands() intercepte la commande
    Core->>Cmds: ping_command(ctx)
    Cmds->>User: Répond "Pong!"

    User->>Core: (4) Taper !send_daily_summary
    note over Core: bot.process_commands() → send_daily_summary_cmd(ctx)
    Cmds->>Summ: (optionnel) get_messages_last_24h(...)
    Cmds->>Mail: format_messages_for_email(...), send_email(...)
    Mail->>Env: get_email_address(), get_email_password(), etc.
    Mail->>Mail: smtplib.SMTP(...).starttls(), sendmail()
    Mail->>Cmds: (retour OK)
    Cmds->>User: "Résumé envoyé!"
