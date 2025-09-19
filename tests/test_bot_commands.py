# tests/test_bot_commands.py

import asyncio
import discord
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from discord.ext import commands
from bot.discord_bot_commands import EmailCog

class TestBotCommands(unittest.TestCase):
    def test_send_daily_summary_command(self):
        intents = discord.Intents.default()
        bot = commands.Bot(command_prefix="!", intents=intents)
        bot.messages_by_channel = {"important": {}, "general": {}}

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(bot.add_cog(EmailCog(bot)))

        ctx = MagicMock()
        ctx.command = MagicMock()
        ctx.send = AsyncMock()

        command = bot.get_command("send_daily_summary")
        self.assertIsNotNone(command)

        with patch("bot.discord_bot_commands.send_email", new=AsyncMock()) as mock_send, \
             patch("bot.discord_bot_commands.get_email_address", return_value="addr@example.com"), \
             patch("bot.discord_bot_commands.get_email_password", return_value="pwd"), \
             patch("bot.discord_bot_commands.get_recipient_email", return_value="dest@example.com"):
            loop.run_until_complete(command(ctx))

        ctx.send.assert_called_with("Résumé envoyé (24h) !")
        mock_send.assert_awaited_once()

        loop.run_until_complete(bot.close())
        loop.close()
