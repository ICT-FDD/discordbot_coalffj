# bot/mails_management.py

"""
Description:
    Gère la logique d'envoi d'e-mails (SMTP) et la création d'un texte 
    prêt à être envoyé (format_messages_for_email).
Uses: smtplib, email.mime
Args: (Les fonctions prennent les infos email en paramètre)
Returns: Rien, ou le message formaté
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def format_messages_for_email(messages_dict):
    """
    Exemple minimal : construit un corps de mail à partir des messages
    stockés. Tu peux y intégrer du Markdown, etc.
    """
    email_body = ""
    if "important" in messages_dict and messages_dict["important"]:
        email_body += "### Canaux importants\n"
        # etc.
    return email_body

def send_email(body, from_addr, password, to_addr):
    """
    Description: Envoie l'e-mail via SMTP Gmail, en mode starttls().
    Uses: smtplib
    Args:
        body : str - Contenu texte du mail
        from_addr : str - Adresse mail de l'expéditeur
        password : str - Mot de passe SMTP
        to_addr : str - Adresse mail destinataire
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = "Test mail"

    msg.attach(MIMEText(body, "plain"))

    #print("DEBUG: Inside send_email, about to call starttls()")

    # Connexion SMTP (avec 'with' → appelle __enter__ et __exit__)
    with smtplib.SMTP("ssl0.ovh.net", 587) as server:
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())
    # La sortie du 'with' appelle server.quit() ou server.__exit__, 
    # donc on n'a pas besoin de le faire manuellement.