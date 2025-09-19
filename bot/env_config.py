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


def get_test_recipient_email():
    """
    Description: Récupère la variable TEST_RECIPIENT_EMAIL.
    Uses: os.getenv  ||  Args: None
    Returns: (str : la valeur de TEST_RECIPIENT_EMAIL, ou None si non défini)
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    return os.getenv("TEST_RECIPIENT_EMAIL")


def get_email_smtp_host(default: str = "ssl0.ovh.net"):
    """Récupère l'hôte SMTP (EMAIL_SMTP_HOST)."""
    return os.getenv("EMAIL_SMTP_HOST", default)


def get_email_smtp_port(default: int = 587):
    """Récupère le port SMTP (EMAIL_SMTP_PORT)."""
    value = os.getenv("EMAIL_SMTP_PORT")
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_email_smtp_timeout(default: float = 30.0):
    """Récupère le timeout SMTP (EMAIL_SMTP_TIMEOUT)."""
    value = os.getenv("EMAIL_SMTP_TIMEOUT")
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default
