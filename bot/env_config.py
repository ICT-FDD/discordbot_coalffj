# bot/env_config.py

"""
Description:
    Fournit des fonctions pour lire les variables d'environnement, 
    en s'appuyant sur le package 'python-dotenv'.
Uses: os, dotenv  ||  Args: (Aucune fonction n'a d'argument direct, elles lisent os.getenv)
Returns: Différents getters qui renvoient des strings (ou None si non défini).
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import os
from dotenv import load_dotenv

# Charge le contenu du fichier .env si présent
load_dotenv()

def get_discord_token():
    """
    Description: Récupère la variable DISCORD_TOKEN depuis les variables d'environnement.
    Uses: os.getenv  ||   Args: None
    Returns: (str : la valeur de DISCORD_TOKEN, ou None si non défini)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    return os.getenv("DISCORD_TOKEN")

def get_email_address():
    """
    Description: Récupère la variable EMAIL_ADDRESS.
    Uses: os.getenv  ||  Args: None
    Returns: (str : la valeur de EMAIL_ADDRESS, ou None si non défini)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    return os.getenv("EMAIL_ADDRESS")

def get_email_password():
    """
    Description: Récupère la variable EMAIL_PASSWORD.
    Uses: os.getenv  ||  Args: None
    Returns: (str : la valeur de EMAIL_PASSWORD, ou None si non défini)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    return os.getenv("EMAIL_PASSWORD")

def get_recipient_email():
    """
    Description: Récupère la variable RECIPIENT_EMAIL.
    Uses: os.getenv  ||  Args: None
    Returns: (str : la valeur de RECIPIENT_EMAIL, ou None si non défini)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    return os.getenv("RECIPIENT_EMAIL")
