# bot/core.py

"""
Description:
    Fichier principal (core) qui initialise le bot Discord,
    déclare les événements globaux et lance le bot.
    Les commandes (!xxx) sont désormais gérées via un système d'extension (discord_bot_commands).
Uses:
    - env_config (lecture des variables d'environnement)
    - channel_lists (charge la liste des canaux importants / exclus)
    - discord_bot_commands (extension chargée via load_extension)
    - mails_management, summarizer (si nécessaire pour la logique interne)
"""

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime

# Imports internes
from bot.env_config import (
    get_discord_token,
    get_email_address,
    get_email_password,
    get_recipient_email,
    get_test_recipient_email
)
from bot.channel_lists import load_channels

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

@tasks.loop(hours=24)
async def daily_task():
    """
    Exemple de tâche planifiée qui se déclenche toutes les 24h.
    À adapter pour envoyer un résumé à heure fixe, etc.
    """
    now = datetime.now()
    if now.hour == 23:
        print("[CORE] daily_task - Il est 23h, on pourrait envoyer un mail ici.")
        # ex: summary = format_messages_for_email(bot.messages_by_channel)
        # send_email(summary, ...)

@daily_task.before_loop
async def before_daily_task():
    # Attend que le bot soit complètement prêt avant de démarrer la loop.
    print("[CORE] daily_task démarrera une fois que le bot sera prêt...")
    await bot.wait_until_ready()

async def main():
    """
    Point d'entrée asynchrone. On y crée le bot, on charge l'extension 'discord_bot_commands',
    puis on lance le bot via bot.start(token).
    """
    print("=== DEBUG: main() appelé ===")

        # 1) Créer l'instance du bot
    bot = commands.Bot(command_prefix="!", intents=intents)
        # 2) Stocker vos variables sur bot
    bot.important_channels = important_channels
    bot.excluded_channels = excluded_channels
    bot.messages_by_channel = messages_by_channel
        # 3) Déclarer (ou déplacer) vos events ici, OU les laisser tels quels en décorateur
        #    (on peut les laisser globalement si on fait @bot.event en bas du fichier, c’est aussi ok)
        #    Mais si on les laisse en global, il faut s'assurer que `bot` est bien défini.
    @bot.event
    async def on_ready():
        print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
        print(f"Canaux importants : {bot.important_channels}")
        print(f"Canaux exclus : {bot.excluded_channels}")
        # On peut démarrer la tâche planifiée ici si on veut
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

        if channel_name in bot.important_channels:
            if channel_name not in bot.messages_by_channel["important"]:
                bot.messages_by_channel["important"][channel_name] = []
            bot.messages_by_channel["important"][channel_name].append({
                "author": message.author.name,
                "content": message.content,
                "timestamp": now
            })
        else:
            if channel_name not in bot.messages_by_channel["general"]:
                bot.messages_by_channel["general"][channel_name] = []
            bot.messages_by_channel["general"][channel_name].append({
                "author": message.author.name,
                "content": message.content,
                "timestamp": now
            })

        await bot.process_commands(message)

        # 4) Charger l'extension
        #    => Cela va appeler async def setup(bot) dans discord_bot_commands.py
    await bot.load_extension("bot.discord_bot_commands")

        # 5) Lancer le bot
    token = get_discord_token()
    await bot.start(token)

if __name__ == "__main__":
        # 6) On exécute la coroutine main() pour lancer le bot
    asyncio.run(main())