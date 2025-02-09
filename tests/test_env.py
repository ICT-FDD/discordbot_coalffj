"""
Description:
    Test unitaire pour vérifier la bonne lecture des variables d'environnement
    définies dans .env via env_config.py.
Uses: unittest, os, env_config  ||  Args: (aucun - se lance via unittest)
Returns: (résultat du test)
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import os
import unittest
from bot.env_config import (
    get_discord_token,
    get_email_address,
    get_email_password,
    get_recipient_email
)

class TestEnvConfig(unittest.TestCase):
    def setUp(self):
        """
        Description:
            Éventuellement override /forcé/ des variables d'environnement 
            pour s'assurer d'un comportement prévisible.
        Uses: os.environ  ||  Args: None  ||  Returns: None
        """
        os.environ["DISCORD_TOKEN"] = "fake_token_for_test"
        os.environ["EMAIL_ADDRESS"] = "test_address@example.com"
        os.environ["EMAIL_PASSWORD"] = "test_password_123"
        os.environ["RECIPIENT_EMAIL"] = "test_destination@example.com"

    def test_discord_token(self):
        """
        Vérifie que get_discord_token() retourne la bonne valeur forcée dans setUp().
        """
        token = get_discord_token()
        self.assertEqual(token, "fake_token_for_test")

    def test_email_address(self):
        """
        Vérifie que get_email_address() retourne la bonne valeur.
        """
        email = get_email_address()
        self.assertEqual(email, "test_address@example.com")

    def test_email_password(self):
        pwd = get_email_password()
        self.assertEqual(pwd, "test_password_123")

    def test_recipient_email(self):
        rcp = get_recipient_email()
        self.assertEqual(rcp, "test_destination@example.com")


if __name__ == "__main__":
    unittest.main()
