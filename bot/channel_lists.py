# bot/channel_lists.py

"""
Description:
    Gère la lecture et l'écriture de fichiers texte contenant la liste
    des canaux importants ou exclus.
Uses: (Fonctions standard de lecture/écriture sur disque)
Args: (Les fonctions prennent en paramètre un chemin de fichier et/ou une liste)
Returns: (Listes de chaînes de caractères, ou rien selon la fonction)
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import os

def load_channels(filepath):
    """
    Description: Charge la liste de canaux depuis un fichier texte (un canal par ligne).
    Uses: open(...), os.path.isfile
    Args: (filepath : str - Chemin d'accès au fichier) 
    Returns: (list : Liste des canaux (strings))
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
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
    """
    Description:
        Écrit la liste de canaux dans le fichier texte (un par ligne),
        en écrasant le contenu existant.
    Uses: open(...) en mode "w"
    Args:
        filepath : str - Chemin du fichier
        channels_list : list - Liste de canaux (strings)
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    with open(filepath, "w", encoding="utf-8") as f:
        for ch in channels_list:
            f.write(ch + "\n")
