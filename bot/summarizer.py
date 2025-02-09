# bot/summarizer.py

"""
Description: Fournit des fonctions pour résumer du texte (tronquer, extraire les premières phrases, etc.).
Uses: Module 're' pour séparer les phrases
Args: (selon la fonction)  ||  Returns: (texte résumé)
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import re

def summarize_message(text, max_sentences=2, max_length=200):
    """
    Description:
        Découpe le texte en phrases naïvement sur . ! ?, 
        prend les 'max_sentences' premières, et tronque si nécessaire.
    Uses: re.split
    Args:
        text : str - Le message à résumer
        max_sentences : int - Nombre de phrases max
        max_length : int - Longueur maximale avant tronquage
    Returns: (str : Le texte transformé/résumé)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return text

    extracted = ". ".join(sentences[:max_sentences])
    if len(sentences) > max_sentences:
        extracted += "."

    if len(extracted) > max_length:
        extracted = extracted[:max_length] + " [...]"

    if len(sentences) > max_sentences:
        extracted += " (résumé...)"

    return extracted
