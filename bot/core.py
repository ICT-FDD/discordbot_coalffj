# bot/core.py

"""
Description:
    Fichier principal (core) qui initialise le bot Discord,
    déclare les événements globaux et lance le bot.
    Les commandes (!xxx) sont gérées via un système d'extension (discord_bot_commands).

Uses:
    - env_config (lecture des variables d'environnement)
    - channel_lists (charge la liste des canaux importants / exclus)
    - discord_bot_commands (extension chargée via load_extension)
    - mails_management, summarizer (si nécessaire pour la logique interne)
"""

import asyncio
import logging
import traceback
import sys

import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

# ---------------------------------------------------------------------
# 1) Configuration du logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,  # Mets INFO ou WARNING si tu veux moins de verbosité
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ---------------------------------------------------------------------
# 2) (Optionnel) Capturer toutes les exceptions Python non gérées
# ---------------------------------------------------------------------
def my_excepthook(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = my_excepthook

# ---------------------------------------------------------------------
# 3) Préparation des variables / config
# ---------------------------------------------------------------------
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
excluded_channels  = load_channels(EXCLUDED_CHANNELS_FILE)   # ex: ["tests-bot", ...]

# Configuration des intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

# ---------------------------------------------------------------------
# 4) On crée une variable `bot` SANS l'instancier tout de suite
#    et on définit un handler global d'erreurs de commandes
#    Handler global pour les erreurs dans les commandes
#    (une seule fois dans tout le code)
# ---------------------------------------------------------------------
bot = None  # On mettra la vraie instance dans main()

@commands.Cog.listener()  # <-- Pas obligatoire, tu peux faire @bot.event si tu préfères
async def on_command_error(ctx, error):
    """Gestion globale des erreurs dans les commandes."""
    traceback.print_exc()
    # (Optionnel) avertir l'utilisateur sur Discord :
    await ctx.send(f"Une erreur est survenue : {error}")

# ---------------------------------------------------------------------
# 5) Les tâches planifiées et fonctions utilitaires
# ---------------------------------------------------------------------
@tasks.loop(hours=24)
async def daily_task():
    """
    Exécuté toutes les 24h (ex. s'il est démarré à 00h, ce sera tous les jours à 00h).
    """
    now = datetime.now(timezone.utc)
    print(f"[CORE] daily_task - Il est {now} (UTC).")
    # Ex: Envoyer un résumé par email, etc.
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
    Récupère 'limit' messages récents dans chaque text_channel du 1er serveur,
    et les stocke dans bot.messages_by_channel[category][channel_name].
    """
    # On suppose que bot.messages_by_channel, bot.important_channels, etc. sont déjà définis.
    if not bot.guilds:
        print("[WARN] Aucune guild détectée. Le bot n'est peut-être pas invité ?")
        return

    guild = bot.guilds[0]
    for channel in guild.text_channels:
        channel_name = channel.name
        # Ignorer canaux exclus
        if channel_name in bot.excluded_channels:
            continue

        # Déterminer la catégorie
        category = "important" if (channel_name in bot.important_channels) else "general"

        # Initialiser la liste si inexistante
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
            print(f"[WARN] Pas les permissions pour lire #{channel_name}")
            continue

        # Remet dans l’ordre chronologique (plus ancien -> plus récent)
        collected.reverse()
        bot.messages_by_channel[category][channel_name].extend(collected)

    print("[INIT] populate_initial_messages terminé")

# ---------------------------------------------------------------------
# 6) Point d'entrée asynchrone : main()
# ---------------------------------------------------------------------
async def main():
    global bot
    print("=== DEBUG: main() appelé ===")

    # On crée enfin l'instance du bot
    bot = commands.Bot(command_prefix="!", intents=intents)

    # Structure de stockage des messages
    bot.messages_by_channel = {
        "important": {},
        "general": {}
    }


    # On attache nos variables
    bot.important_channels   = important_channels
    bot.excluded_channels    = excluded_channels
    #bot.messages_by_channel  = messages_by_channel

    # On enregistre manuellement le listener global d'erreur
    # (car on_command_error n'a pas été défini avec @bot.event)
    bot.add_listener(on_command_error)

    # Déclarer ici les events, si tu veux (ex: on_ready, on_message)
    @bot.event
    async def on_ready():
        print(f"[CORE] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
        print(f"Canaux importants : {bot.important_channels}")
        print(f"Canaux exclus : {bot.excluded_channels}")

        # Récupération initiale
        await populate_initial_messages(bot, limit=20)
        print("Messages initiaux récupérés.")

        # On lance la tâche planifiée
        daily_task.start()

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        channel_name = message.channel.name
        print(f"[DEBUG] on_message: '{message.content}' dans #{channel_name}")

        if channel_name in bot.excluded_channels:
            # On exclut ce canal des traitements, mais on laisse passer les commandes
            await bot.process_commands(message)
            return

        # On détermine la catégorie
        cat = "important" if (channel_name in bot.important_channels) else "general"

        # Initialiser la liste si elle n'existe pas encore
        if channel_name not in bot.messages_by_channel[cat]:
            bot.messages_by_channel[cat][channel_name] = []

        now = datetime.now(timezone.utc)
        bot.messages_by_channel[cat][channel_name].append({
            "author":    message.author.name,
            "content":   message.content,
            "timestamp": now
        })

        # Toujours laisser passer les commandes
        await bot.process_commands(message)

    # On charge l'extension (cogs)
    try:
        await bot.load_extension("bot.discord_bot_commands")
    except Exception as e:
        print(f"[ERROR] Impossible de charger l'extension: {e}")
        traceback.print_exc() # ← Affiche tout le stack trace Python

    # Lancement du bot
    token = get_discord_token()
    try:
        await bot.start(token)
    except Exception as e:
        print(f"[ERROR] Bot crashed : {e}")
        raise

# ---------------------------------------------------------------------
# 7) Lancement du script
# ---------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
