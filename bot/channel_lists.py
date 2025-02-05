# bot/channel_lists.py

import os

def load_channels(filepath):
    """Charge la liste de canaux depuis un fichier texte (un canal par ligne)."""
    channels = []
    if not os.path.isfile(filepath):
        return channels
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                channels.append(line)
    return channels

def save_channels(filepath, channels_list):
    """Sauvegarde une liste de canaux dans le fichier texte, un par ligne."""
    with open(filepath, "w", encoding="utf-8") as f:
        for ch in channels_list:
            f.write(ch + "\n")
