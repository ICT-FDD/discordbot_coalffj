# bot/core.py

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime

# Imports internes
from bot.env_config import get_discord_token
from bot.channel_lists import load_channels
from bot.summarizer import get_messages_last_24h  # si besoin
from bot.mails_management import send_email, format_messages_for_email  # ex, si besoin

# Fichiers config
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE  = "data/excluded_channels.txt"

# Chargement des listes de canaux
important_channels = load_channels(IMPORTANT_CHANNELS_FILE)
excluded_channels  = load_channels(EXCLUDED_CHANNELS_FILE)

# Structure de stockage des messages
messages_by_channel = {
    "important": {},
    "general": {}
}

# Intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

@tasks.loop(hours=24)
async def daily_task():
    """
    Exécuté toutes les 24h (ex. s'il est démarré à 00h, ce sera tous les jours à 00h).
    """
    now = datetime.utcnow()
    print(f"[CORE] daily_task - Il est {now} (UTC).")

    # Ex: Envoyer un résumé par email
    # summary = format_messages_for_email(bot.messages_by_channel)
    # send_email(summary, ...)
    # reset / vider messages_by_channel si besoin

@daily_task.before_loop
async def before_daily_task():
    print("[CORE] daily_task démarrera une fois que le bot sera prêt...")
    # on attend que bot soit prêt
    await bot.wait_until_ready()
    print("[CORE] daily_task est prêt à démarrer.")

async def populate_initial_messages(bot: commands.Bot, limit: int = 20):
    """
    Parcourt chaque text_channel, récupère 'limit' messages récents,
    et les stocke dans bot.messages_by_channel.
    """
    # On suppose que bot.messages_by_channel, bot.important_channels, etc. sont déjà définis.
    if not bot.guilds:
        print("[WARN] Aucune guild détectée. Le bot est peut-être pas invité ?")
        return

    guild = bot.guilds[0]  # si vous n’avez qu’un seul serveur
    for channel in guild.text_channels:
        channel_name = channel.name
        # Ignorer canaux exclus
        if channel_name in bot.excluded_channels:
            continue

        # Déterminer la catégorie
        if channel_name in bot.important_channels:
            category = "important"
        else:
            category = "general"

        # Initialiser la liste si inexistante
        if channel_name not in bot.messages_by_channel[category]:
            bot.messages_by_channel[category][channel_name] = []

        collected = []
        try:
            async for msg in channel.history(limit=limit, oldest_first=False):
                if msg.author.bot:
                    continue
                collected.append({
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at
                })
        except discord.Forbidden:
            print(f"[WARN] Pas les permissions pour lire #{channel_name}")
            continue

        # On remet collected dans l’ordre chronologique (plus ancien -> plus récent)
        collected.reverse()
        bot.messages_by_channel[category][channel_name].extend(collected)

    print("[INIT] populate_initial_messages terminé")


async def main():
    """
    Point d'entrée asynchrone. 
    - Crée le bot, 
    - stocke les variables (important_channels, etc.),
    - déclare les events (on_ready, on_message),
    - charge l'extension,
    - lance le bot.
    """
    print("=== DEBUG: main() appelé ===")

    global bot  # si on veut réutiliser bot dans daily_task.before_loop
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Attachement des variables
    bot.important_channels   = important_channels
    bot.excluded_channels    = excluded_channels
    bot.messages_by_channel  = messages_by_channel

    # ----- Events ----- #
    @bot.event
    async def on_ready():
        print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
        print(f"Canaux importants : {bot.important_channels}")
        print(f"Canaux exclus : {bot.excluded_channels}")
        
        # Récupération initiale
        await populate_initial_messages(bot, limit=20)
        print("Messages initiaux récupérés.")

        # On lance la tâche planifiée (si on le souhaite)
        daily_task.start()

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        channel_name = message.channel.name
        print(f"[DEBUG] on_message: '{message.content}' dans #{channel_name}")

        if channel_name in bot.excluded_channels:
            await bot.process_commands(message)
            return

        now = datetime.utcnow()
        # On détermine la catégorie
        if channel_name in bot.important_channels:
            cat = "important"
        else:
            cat = "general"

        if channel_name not in bot.messages_by_channel[cat]:
            bot.messages_by_channel[cat][channel_name] = []

        bot.messages_by_channel[cat][channel_name].append({
            "author": message.author.name,
            "content": message.content,
            "timestamp": now
        })

        # Laisser passer les commandes
        await bot.process_commands(message)

    # ----- Charger l'extension (cogs) ----- #
    try:
        await bot.load_extension("bot.discord_bot_commands")
    except Exception as e:
        print(f"[ERROR] Impossible de charger l'extension: {e}")

    # ----- Lancement du bot ----- #
    token = get_discord_token()

    try:
        await bot.start(token)
    except Exception as e:
        print(f"[ERROR] Bot crashed : {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
