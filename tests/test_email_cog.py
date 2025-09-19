import smtplib
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.discord_bot_commands import EmailCog


class TestEmailCog(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.bot.messages_by_channel = {"important": {}, "general": {}}

    async def test_test_send_daily_summary_cmd_missing_config(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch("bot.discord_bot_commands.send_email", new=AsyncMock()) as mock_send, \
             patch("bot.discord_bot_commands.logger") as mock_logger:
            await cog.test_send_daily_summary_cmd.callback(cog, ctx)

        ctx.send.assert_awaited_once_with(
            "Configuration e-mail incomplète : EMAIL_ADDRESS, EMAIL_PASSWORD, TEST_RECIPIENT_EMAIL manquant(s)."
        )
        mock_send.assert_not_called()
        mock_logger.error.assert_called_once()

    async def test_test_send_daily_summary_cmd_timeout(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch("bot.discord_bot_commands.send_email", new=AsyncMock(side_effect=TimeoutError)), \
             patch("bot.discord_bot_commands.save_messages_to_file") as mock_save, \
             patch("bot.discord_bot_commands.logger") as mock_logger:
            # Simule une configuration valide
            with patch("bot.discord_bot_commands.get_email_address", return_value="addr@example.com"), \
                 patch("bot.discord_bot_commands.get_email_password", return_value="pwd"), \
                 patch("bot.discord_bot_commands.get_test_recipient_email", return_value="test@example.com"):
                await cog.test_send_daily_summary_cmd.callback(cog, ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : délai d'attente dépassé."
        )
        mock_save.assert_not_called()
        mock_logger.exception.assert_called_once()

    async def test_test_send_daily_summary_cmd_smtpexception(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch(
            "bot.discord_bot_commands.send_email",
            new=AsyncMock(side_effect=smtplib.SMTPException("smtp error")),
        ), patch("bot.discord_bot_commands.save_messages_to_file") as mock_save, patch(
            "bot.discord_bot_commands.logger"
        ) as mock_logger, patch(
            "bot.discord_bot_commands.get_email_address", return_value="addr@example.com"
        ), patch(
            "bot.discord_bot_commands.get_email_password", return_value="pwd"
        ), patch(
            "bot.discord_bot_commands.get_test_recipient_email",
            return_value="test@example.com",
        ):
            await cog.test_send_daily_summary_cmd.callback(cog, ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : erreur SMTP (authentification ou envoi)."
        )
        mock_save.assert_not_called()
        mock_logger.exception.assert_called_once()

    async def test_test_send_daily_summary_cmd_unexpected(self):
        cog = EmailCog(self.bot)
        ctx = MagicMock()
        ctx.send = AsyncMock()

        with patch(
            "bot.discord_bot_commands.send_email",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ), patch("bot.discord_bot_commands.save_messages_to_file") as mock_save, patch(
            "bot.discord_bot_commands.logger"
        ) as mock_logger, patch(
            "bot.discord_bot_commands.get_email_address", return_value="addr@example.com"
        ), patch(
            "bot.discord_bot_commands.get_email_password", return_value="pwd"
        ), patch(
            "bot.discord_bot_commands.get_test_recipient_email",
            return_value="test@example.com",
        ):
            await cog.test_send_daily_summary_cmd.callback(cog, ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : erreur inattendue (voir les logs)."
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
        ) as mock_logger, patch(
            "bot.discord_bot_commands.get_email_address", return_value="addr@example.com"
        ), patch(
            "bot.discord_bot_commands.get_email_password", return_value="pwd"
        ), patch(
            "bot.discord_bot_commands.get_test_recipient_email",
            return_value="test@example.com",
        ):
            await cog.test_send_daily_summary_cmd.callback(cog, ctx)

        ctx.send.assert_awaited_once_with(
            "Échec de l'envoi du mail de test : erreur réseau lors de la connexion SMTP."
        )
        mock_save.assert_not_called()
        mock_logger.exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()
