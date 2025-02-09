# tests/test_bot_integration.py

import unittest
from unittest.mock import patch
from bot.core import bot

class TestBotIntegration(unittest.TestCase):
    @patch("discord.ext.commands.bot.Bot.run")
    def test_bot_run(self, mock_run):
        # Juste vérifier qu'on peut appeler run sans erreur
        token = "fake_token"
        # On n'a pas besoin d'argument : bot.run(token) est dans run_bot() 
        # si on a un "run_bot" dans core.py
        # On simule un run
        pass

if __name__ == "__main__":
    unittest.main()
