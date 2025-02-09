#bot/core.py

"""
Description:
    Fichier principal (core) qui initialise le bot Discord, charge les ressources
    nécessaires (variables d'environnement, listes de canaux), déclare les événements
    globaux et lance le bot.
Uses:
    - env_config (lecture des variables d'environnement)
    - channel_lists (charge la liste des canaux importants / exclus)
    - discord_bot_commands (enregistre les commandes ! du bot)
    - mails_management, summarizer (si nécessaire pour la logique interne)

---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime

# Imports internes
from bot.env_config import (
    get_discord_token,
    get_email_address,
    get_email_password,
    get_recipient_email
)
from bot.channel_lists import load_channels
from bot.discord_bot_commands import setup_bot_commands
from bot.summarizer import summarize_message  # Si besoin dans on_message
from bot.mails_management import send_email, format_messages_for_email  # Ex si tu gères l'envoi ici

# Fichiers pour la configuration des canaux
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE = "data/excluded_channels.txt"

# Chargement des listes de canaux
important_channels = load_channels(IMPORTANT_CHANNELS_FILE)  # ex: ["canal1", "canal2"]
excluded_channels = load_channels(EXCLUDED_CHANNELS_FILE)    # ex: ["tests-bot", ...]

# Structure de stockage des messages
messages_by_channel = {
    "important": {},
    "general": {}
}

# Configuration des intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

# Création de l'instance du bot
bot = commands.Bot(command_prefix="!", intents=intents)

def run_bot():
    """
    Description:
        Initialise et exécute le bot. Charge les commandes, démarre
        éventuellement les tâches planifiées, puis lance la boucle Discord.
    Uses: Les variables / structures déclarées plus haut (bot, important_channels, etc.)
    Args: Aucun
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    # Enregistre les commandes définies dans discord_bot_commands.py
    setup_bot_commands(
        bot=bot,
        messages_by_channel=messages_by_channel,
        important_channels=important_channels,
        excluded_channels=excluded_channels
    )

    # Optionnel : on peut démarrer une tâche planifiée ici, ex: daily_task.start()

    # Récupérer le token
    token = get_discord_token()
    # Démarre la boucle d'événements
    bot.run(token)

@bot.event
async def on_ready():
    """
    Description:
        Événement déclenché une fois que le bot est prêt et connecté.
    Uses: L'instance 'bot' (commands.Bot)
    Args: Aucun (paramètre imposé par Discord)
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message):
    """
    Description:
        Intercepte chaque message sur le serveur. Classe le message
        dans 'important' ou 'general' sauf si le canal est exclu.
        Appelle bot.process_commands() pour laisser passer les commandes.
    Uses:
        - important_channels
        - excluded_channels
        - messages_by_channel
    Args: (message : discord.Message - Le message reçu)
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    # Ignorer les messages du bot lui-même pour éviter les boucles
    if message.author == bot.user:
        return

    channel_name = message.channel.name

    # Si le canal est exclu, on ignore la collecte de messages
    if channel_name in excluded_channels:
        await bot.process_commands(message)
        return

    # Canaux "importants"
    if channel_name in important_channels:
        if channel_name not in messages_by_channel["important"]:
            messages_by_channel["important"][channel_name] = []
        messages_by_channel["important"][channel_name].append((message.author.name, message.content))
    else:
        # Autres canaux => stocké dans "general"
        if channel_name not in messages_by_channel["general"]:
            messages_by_channel["general"][channel_name] = []
        messages_by_channel["general"][channel_name].append((message.author.name, message.content))

    # Permettre aux commandes (ex: !send_daily_summary) d'être traitées
    await bot.process_commands(message)

@tasks.loop(hours=24)
async def daily_task():
    """
    Description:
        Exemple de tâche planifiée qui se déclenche toutes les 24h.
        À adapter si tu veux envoyer un résumé à heure fixe, etc.
    Uses:
        datetime.now() pour récupérer l'heure
        messages_by_channel pour récupérer les messages
    Args: Aucun  ||  Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    now = datetime.now()
    # ex: si on veut un envoi à 23h UTC
    if now.hour == 23:
        print("[CORE] daily_task - Il est 23h, on pourrait envoyer un mail ici.")
        # ...
        # ex: summary = format_messages_for_email(messages_by_channel)
        # send_email(summary, ...)
        # reset
        # messages_by_channel["important"].clear()
        # messages_by_channel["general"].clear()

@daily_task.before_loop
async def before_daily_task():
    """
    Description: Attend que le bot soit complètement prêt avant de démarrer la loop.
    Uses: bot.wait_until_ready()
    Args: Aucun  ||  Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    print("[CORE] daily_task démarrera une fois que le bot sera prêt...")
    await bot.wait_until_ready()


if __name__ == "__main__":
    run_bot()
