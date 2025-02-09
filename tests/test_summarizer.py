# tests/test_summarizer.py

import unittest
from bot.summarizer import summarize_message

class TestSummarizer(unittest.TestCase):
    def test_short_text(self):
        text = "Bonjour. Comment ça va ?"
        summary = summarize_message(text, max_sentences=2, max_length=50)
        self.assertIn("Bonjour. Comment ça va", summary)

    def test_long_text(self):
        text = "Phrase1. Phrase2. Phrase3. Phrase4 vraiment longue..."
        summary = summarize_message(text, max_sentences=2, max_length=50)
        # On s'attend à ne voir que 2 phrases, potentiellement tronquées
        self.assertTrue("Phrase1" in summary)
        self.assertTrue("Phrase2" in summary)
        self.assertFalse("Phrase3" in summary)
        self.assertIn("(résumé...)", summary)

    def test_max_length(self):
        text = "Ceci est un message extrêmement long " + ("bla " * 50)
        summary = summarize_message(text, max_sentences=3, max_length=60)
        self.assertTrue(len(summary) <= 70)  # un peu de marge pour "[...]" et "(résumé...)"

if __name__ == "__main__":
    unittest.main()
