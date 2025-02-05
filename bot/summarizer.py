# bot/summarizer.py
import re

def summarize_message(text, max_sentences=2, max_length=200):
    """
    Exemple de résumé naive : sépare en phrases sur . ! ?, prend X premières phrases,
    puis tronque si plus de max_length.
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
