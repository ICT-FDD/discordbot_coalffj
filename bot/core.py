# bot/core.py

"""
Description:
    Fichier principal (core) qui initialise le bot Discord,
    déclare les événements globaux et lance le bot.
    Les commandes (!xxx) sont gérées via une extension (discord_bot_commands).
"""

import asyncio
import logging
import traceback
import sys

import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

# ---------------------------------------------------------------------
# 1) Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def my_excepthook(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = my_excepthook

# ---------------------------------------------------------------------
# 2) Config & intents
# ---------------------------------------------------------------------
from bot.env_config import get_discord_token

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot: commands.Bot | None = None  # affecté dans main()

# ---------------------------------------------------------------------
# 3) Tâches
# ---------------------------------------------------------------------
@tasks.loop(hours=24)
async def daily_task():
    now = datetime.now(timezone.utc)
    print(f"[CORE] daily_task - {now} (UTC)")

@daily_task.before_loop
async def before_daily_task():
    print("[CORE] daily_task attend que le bot soit prêt…")
    await bot.wait_until_ready()
    print("[CORE] daily_task prêt.")

async def populate_initial_messages(bot: commands.Bot, limit: int = 20):
    """
    Récupère `limit` messages récents dans chaque salon texte et
    remplit bot.messages_by_channel[category][channel_name].
    """
    if not bot.guilds:
        print("[WARN] Aucune guild détectée (le bot est-il invité ?)")
        return

    guild = bot.guilds[0]
    excluded = getattr(bot, "excluded_channels", [])
    important = getattr(bot, "important_channels", [])

    for channel in guild.text_channels:
        channel_name = channel.name
        if channel_name in excluded:
            continue

        category = "important" if (channel_name in important) else "general"

        if channel_name not in bot.messages_by_channel[category]:
            bot.messages_by_channel[category][channel_name] = []

        collected = []
        try:
            async for msg in channel.history(limit=limit, oldest_first=False):
                if msg.author.bot:
                    continue
                collected.append({
                    "author":    msg.author.name,
                    "content":   msg.content,
                    "timestamp": msg.created_at
                })
        except discord.Forbidden:
            print(f"[WARN] Pas de permission pour lire #{channel_name}")
            continue

        collected.reverse()
        bot.messages_by_channel[category][channel_name].extend(collected)

    print("[INIT] populate_initial_messages terminé")

# ---------------------------------------------------------------------
# 4) Entrée principale
# ---------------------------------------------------------------------
async def main():
    global bot
    print("=== DEBUG: main() appelé ===")

    bot = commands.Bot(command_prefix="!", intents=intents)

    # Mémoire interne
    bot.messages_by_channel = {"important": {}, "general": {}}
    # Valeurs par défaut pour éviter AttributeError avant le chargement du store
    bot.important_channels = []
    bot.excluded_channels = []

    # Listener global d'erreurs de commandes
    @commands.Cog.listener()
    async def on_command_error(ctx, error):
        traceback.print_exc()
        await ctx.send(f"Une erreur est survenue : {error}")

    bot.add_listener(on_command_error)

    @bot.event
    async def on_ready():
        print(f"[CORE] Connecté en tant que {bot.user} (ID: {bot.user.id})")

        # 1) Charger les listes depuis #bot-storage avant tout
        try:
            # import tardif pour éviter les cycles
            from bot.discord_bot_commands import ensure_storage_loaded
            await ensure_storage_loaded(bot)
            print("[CORE] bot-storage chargé ->",
                  "important:", bot.important_channels,
                  "excluded:", bot.excluded_channels)
        except Exception as e:
            print("[WARN] ensure_storage_loaded a échoué :", e)

        # 2) Pré-fetch des messages
        await populate_initial_messages(bot, limit=20)
        print("[CORE] Messages initiaux récupérés.")

        # 3) Tâche planifiée
        daily_task.start()

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        channel_name = message.channel.name
        print(f"[DEBUG] on_message: '{message.content}' dans #{channel_name}")

        excluded = getattr(bot, "excluded_channels", [])
        important = getattr(bot, "important_channels", [])

        if channel_name in excluded:
            await bot.process_commands(message)
            return

        cat = "important" if (channel_name in important) else "general"
        if channel_name not in bot.messages_by_channel[cat]:
            bot.messages_by_channel[cat][channel_name] = []

        now = datetime.now(timezone.utc)
        bot.messages_by_channel[cat][channel_name].append({
            "author":    message.author.name,
            "content":   message.content,
            "timestamp": now
        })

        await bot.process_commands(message)

    # Charger l’extension (cogs & helpers)
    try:
        await bot.load_extension("bot.discord_bot_commands")
    except Exception as e:
        print(f"[ERROR] Impossible de charger l'extension: {e}")
        traceback.print_exc()

    # Lancement
    token = get_discord_token()
    try:
        await bot.start(token)
    except Exception as e:
        print(f"[ERROR] Bot crashed : {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
# Fin de bot/core.py