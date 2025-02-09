# tests/test_bot_commands.py

import discord
import unittest
from unittest.mock import MagicMock, AsyncMock
from discord.ext import commands
from bot.discord_bot_commands import setup_bot_commands

class TestBotCommands(unittest.TestCase):
    def test_send_daily_summary_command(self):
        #bot = commands.Bot(command_prefix="!")
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
        setup_bot_commands(bot, {})  # messages_by_channel = {}
        
        # On simule un Context
        ctx = MagicMock()
        ctx.command = MagicMock()
        ctx.send = AsyncMock()

        # Récupérer la commande
        command = bot.get_command("send_daily_summary")
        self.assertIsNotNone(command)

        # Appeler la commande
        # Comme c'est async, on utilise run_until_complete
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(command(ctx))

        # Vérifier qu'on a envoyé un message "Résumé envoyé."
        ctx.send.assert_called_with("Résumé envoyé.")
