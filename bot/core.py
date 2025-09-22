# bot/core.py
"""
Description:
    Fichier principal (core) qui initialise le bot Discord,
    déclare les événements globaux et lance le bot.
    Les commandes (!xxx) sont gérées via une extension (discord_bot_commands).
"""

from __future__ import annotations

import asyncio
import logging
import traceback
import sys
import signal
import contextlib
from datetime import datetime, timezone, timedelta
import zoneinfo

import discord
from discord.ext import commands

# ---------------------------------------------------------------------
# 1) Logging (moins verbeux)
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,  # mets DEBUG si tu veux plus de détails
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Réduire le bruit de certains loggers
logging.getLogger("discord.gateway").setLevel(logging.WARNING)
logging.getLogger("discord.client").setLevel(logging.INFO)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

def my_excepthook(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = my_excepthook

# ---------------------------------------------------------------------
# 2) Config & imports projet
# ---------------------------------------------------------------------
from bot.env_config import get_discord_token
# ✅ Getters email viennent d'env_config
from bot.env_config import (
    get_email_address,
    get_email_password,
    get_recipient_email,
)
# ✅ Fonctions mail & formatage viennent de mails_management
from bot.mails_management import (
    send_email,
    format_messages_for_email,
)
from bot.file_utils import save_messages_to_file

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot: commands.Bot | None = None  # affecté dans main()

# Événement pour arrêt propre (SIGINT/SIGTERM/Ctrl+C)
shutdown_event = asyncio.Event()

def _handle_signal():
    """Déclenché par SIGINT/SIGTERM pour arrêter proprement."""
    loop = asyncio.get_running_loop()
    loop.call_soon_threadsafe(shutdown_event.set)

# ---------------------------------------------------------------------
# 3) Scheduler “propre” (07:00 Europe/Brussels via asyncio.create_task)
# ---------------------------------------------------------------------
async def run_daily_07h_europe_brussels(job_coro):
    """
    Lance `job_coro` chaque jour à 07:00 Europe/Brussels.
    `job_coro` est une coroutine SANS argument.
    """
    log = logging.getLogger(__name__)
    tz = zoneinfo.ZoneInfo("Europe/Brussels")
    await asyncio.sleep(0)  # yield

    while True:
        now = datetime.now(tz)
        target = now.replace(hour=7, minute=0, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)

        sleep_s = (target - now).total_seconds()
        log.info("[CORE] Prochaine exécution à %s (dans %d s)", target.isoformat(), int(sleep_s))

        try:
            await asyncio.sleep(sleep_s)
            await job_coro()
        except asyncio.CancelledError:
            log.info("[CORE] Tâche quotidienne annulée — arrêt propre.")
            raise
        except Exception:
            log.exception("[CORE] Erreur dans la tâche quotidienne — on continue.")

async def do_daily_summary_job():
    """
    Construit le résumé et envoie l'e-mail quotidien.
    Utilise bot.messages_by_channel, déjà alimenté ailleurs.
    """
    assert bot is not None
    log = logging.getLogger(__name__)

    # 1) Construire le résumé (tout le buffer courant)
    messages_dict = getattr(bot, "messages_by_channel", {})
    summary = format_messages_for_email(messages_dict)

    # 2) Paramètres e-mail
    from_addr = get_email_address()
    password  = get_email_password()
    to_addr   = get_recipient_email()

    # 3) Envoi
    try:
        await send_email(summary, from_addr, password, to_addr)
        log.info("[MAIL] Résumé envoyé à %s.", to_addr)
    except Exception:
        log.exception("[MAIL] Échec de l'envoi du résumé (SMTP).")

    # 4) Sauvegarde locale (log JSON)
    try:
        save_messages_to_file(messages_dict)
    except Exception:
        log.exception("[SAVE] Échec de la sauvegarde du JSON.")

# ---------------------------------------------------------------------
# 4) Utilitaires
# ---------------------------------------------------------------------
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
# 5) Point d'entrée principal
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

    # Installer les handlers de signaux (Ctrl+C / kill)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:
            # Windows / environnements où add_signal_handler n'est pas dispo
            pass

    # Listener global d'erreurs de commandes
    @commands.Cog.listener()
    async def on_command_error(ctx, error):
        traceback.print_exc()
        try:
            await ctx.send(f"Une erreur est survenue : {error}")
        except Exception:
            pass

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

        # 3) Tâche planifiée (create_task → Task annulable/awaitable)
        if not hasattr(bot, "daily_task"):
            bot.daily_task = asyncio.create_task(
                run_daily_07h_europe_brussels(do_daily_summary_job)
            )
            logging.getLogger(__name__).info("[CORE] daily_task prête.")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author == bot.user:
            return

        channel_name = message.channel.name
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

    # Lancement + arrêt propre
    token = get_discord_token()
    try:
        # Démarre le bot en tâche concurrente
        start_task = asyncio.create_task(bot.start(token))
        # Attends soit un signal d'arrêt, soit un crash du bot
        await asyncio.wait(
            {start_task, asyncio.create_task(shutdown_event.wait())},
            return_when=asyncio.FIRST_COMPLETED
        )
    except KeyboardInterrupt:
        # Ctrl+C classique
        pass
    finally:
        # Annuler proprement la tâche quotidienne si présente
        task = getattr(bot, "daily_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Fermer le bot Discord
        with contextlib.suppress(Exception):
            await bot.close()

# ---------------------------------------------------------------------
# 6) Exécution
# ---------------------------------------------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Arrêt demandé (Ctrl+C) — fermeture propre.")
    except Exception as e:
        print(f"[FATAL] Exception non gérée dans main(): {e}")
        traceback.print_exc()
# EOF
