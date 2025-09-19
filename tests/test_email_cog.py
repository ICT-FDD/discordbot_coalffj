import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.discord_bot_commands import EmailCog


class TestEmailCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.bot.messages_by_channel = {"important": {}, "general": {}}

    async def test_test_send_daily_summary_cmd_timeout(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch("bot.discord_bot_commands.send_email", new=AsyncMock(side_effect=TimeoutError)), \
             patch("bot.discord_bot_commands.save_messages_to_file") as mock_save, \
             patch("bot.discord_bot_commands.logger") as mock_logger:
            await cog.test_send_daily_summary_cmd(ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : délai d'attente dépassé."
        )
        mock_save.assert_not_called()
        mock_logger.exception.assert_called_once()

    async def test_test_send_daily_summary_cmd_oserror(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch(
            "bot.discord_bot_commands.send_email",
            new=AsyncMock(side_effect=OSError("network unreachable")),
        ), patch("bot.discord_bot_commands.save_messages_to_file") as mock_save, patch(
            "bot.discord_bot_commands.logger"
        ) as mock_logger:
            await cog.test_send_daily_summary_cmd(ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : erreur réseau lors de la connexion SMTP."
        )
        mock_save.assert_not_called()
        mock_logger.exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()
