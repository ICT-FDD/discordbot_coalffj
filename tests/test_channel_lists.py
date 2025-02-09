# tests/test_channel_lists.py

import unittest
import os
import tempfile
from bot.channel_lists import load_channels, save_channels

class TestChannelLists(unittest.TestCase):
    def test_load_save_channels(self):
        # 1) Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            test_path = tmpfile.name

        # 2) Sauvegarder quelques canaux
        channels_to_save = ["canal1", "canal2", "canal3"]
        save_channels(test_path, channels_to_save)

        # 3) Charger ce qu'on vient de sauvegarder
        loaded = load_channels(test_path)

        self.assertEqual(len(loaded), 3)
        self.assertIn("canal2", loaded)

        # Nettoyage
        os.remove(test_path)

    def test_load_nonexistent_file(self):
        # Charger un fichier qui n'existe pas ne doit pas planter, 
        # on s'attend à une liste vide
        non_existent_path = "fake_path_123456.txt"
        result = load_channels(non_existent_path)
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
