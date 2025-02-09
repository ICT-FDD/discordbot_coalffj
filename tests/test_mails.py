# tests/test_mails.py

"""
Descript. : Tests unitaires pour mails_management.py, en simulant l'envoi SMTP via un mock.
Uses: unittest, unittest.mock
Args: (Aucun - se lance avec unittest discover)
Returns: Résultat du test
---
Author: Ton Nom
Version: 1.0 - 02/02/2025
"""

import unittest
from unittest.mock import ANY
from unittest.mock import patch, MagicMock
from bot.mails_management import send_email

class TestMailsManagement(unittest.TestCase):

    @patch("bot.mails_management.smtplib.SMTP")
    def test_send_email(self, mock_smtp):
        """
        Vérifie que send_email() appelle bien SMTP, starttls(), login, sendmail.
        """
        # Setup
        from_addr = "test@example.com"
        password = "fakepass"
        to_addr = "dest@example.com"
        body = "Hello World"

        # Action
        send_email(body, from_addr, password, to_addr)
        
        # Vérif que SMTP(...) a été appelé avec "smtp.ovh.com", 587
        mock_smtp.assert_called_once_with("ssl0.ovh.net", 587)

        # Récupérer l'instance "server" (celui qui subit server.starttls(), etc.)
        mock_server_instance = mock_smtp.return_value.__enter__.return_value
        
        # Vérifier que starttls() a bien été appelé
        mock_server_instance.starttls.assert_called_once()
        
        # Vérifier que login() a bien été appelé avec les bons arguments
        mock_server_instance.login.assert_called_once_with(from_addr, password)
        
        # Vérifier que sendmail() a bien été appelé au moins 1 fois
        mock_server_instance.sendmail.assert_called_once()

        # (Optionnel) on peut vérifier le 1er argument 
        mock_server_instance.sendmail.assert_called_once_with(from_addr, to_addr, ANY)

        # Comme on utilise 'with smtplib.SMTP(...) as server:',
        # la fermeture se fait par __exit__. On peut éventuellement tester:
        mock_smtp.return_value.__exit__.assert_called_once()

if __name__ == "__main__":
    unittest.main()