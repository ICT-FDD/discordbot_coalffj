# bot/core.py

import os
import discord
from discord.ext import commands, tasks
from datetime import datetime
from dotenv import load_dotenv

# Import de tes modules
from bot.channel_lists import load_channels, save_channels
from bot.discord_bot_commands import setup_bot_commands
from bot.mails_management import send_email
# etc.

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Fichiers .txt
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE = "data/excluded_channels.txt"

# On charge la liste des canaux importants / exclus
important_channels = load_channels(IMPORTANT_CHANNELS_FILE)
excluded_channels = load_channels(EXCLUDED_CHANNELS_FILE)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Structure de données (exemple) pour stocker les messages
messages_by_channel = {
    "important": {},
    "general": {}
}

@bot.event
async def on_ready():
    print(f"[CORE] Bot connecté en tant que {bot.user}")
    # On pourrait démarrer ici une tâche planifiée, etc.

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    channel_name = message.channel.name

    # Ignorer les canaux exclus
    if channel_name in excluded_channels:
        # Laisser passer quand même les commandes si on veut
        await bot.process_commands(message)
        return

    # Vérifier si c'est un canal important
    if channel_name in important_channels:
        if channel_name not in messages_by_channel["important"]:
            messages_by_channel["important"][channel_name] = []
        messages_by_channel["important"][channel_name].append((message.author.name, message.content))
    else:
        if channel_name not in messages_by_channel["general"]:
            messages_by_channel["general"][channel_name] = []
        messages_by_channel["general"][channel_name].append((message.author.name, message.content))

    # N'oublie pas de process les commandes
    await bot.process_commands(message)

# Exemple de tâche quotidienne
@tasks.loop(hours=24)
async def daily_task():
    now = datetime.now()
    if now.hour == 23:
        print("[CORE] Il est 23h, on pourrait envoyer un mail par exemple.")

        # On peut appeler ici une fonction qui récupère messages_by_channel, formatte, etc.

        # Reset
        messages_by_channel["important"].clear()
        messages_by_channel["general"].clear()

@daily_task.before_loop
async def before_daily_task():
    print("[CORE] daily_task démarre dans quelques instants...")
    await bot.wait_until_ready()



def run_bot():
    # Import tardif pour éviter les import cycles
    setup_bot_commands(bot, messages_by_channel, important_channels, excluded_channels)

    # On pourrait lancer la task quotidienne
    daily_task.start()

    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    run_bot()
