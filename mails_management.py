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
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bot.summarizer import naive_summarize


def format_messages_for_email(messages_dict):
    """
    Construit une chaîne de texte pour l'e-mail, en séparant
    les canaux "importants" (texte brut) et "généraux" (texte résumé).
    
    Format attendu de messages_dict:
      {
        "important": {
          "channelName1": [
            {"author": "Alice", "content": "Message...", "timestamp": datetime(...)},
            {"author": "Bob",   "content": "Autre...",  "timestamp": ...},
            ...
          ],
          "channelName2": [...]
        },
        "general": {
          "channelName3": [...],
          ...
        }
      }
    
    Returns:
        str: Le corps de l'e-mail (Markdown / texte brut).
    """
    email_body = " ** Mail de résumé quotidien du Discord de la Coalittion Feminist For Justice.**\n\n"

    # --- Canaux importants (non résumés) ---
    if "important" in messages_dict and messages_dict["important"]:
        email_body += "### Canaux importants\n\n"
        for channel, msg_list in messages_dict["important"].items():
            email_body += f"## {channel}\n\n"
            for msg in msg_list:
                author = msg.get("author", "???")
                content = msg.get("content", "")
                # Optionnel: si tu veux afficher la date
                date_str = ""
                if "timestamp" in msg and isinstance(msg["timestamp"], datetime):
                    date_str = msg["timestamp"].strftime("%Y-%m-%d %H:%M")
                email_body += f"{date_str} - **{author}** : {content}\n\n"

                #email_body += f"**{author}** a écrit :\n{content}\n\n"

    # --- Canaux généraux (résumés) ---
    if "general" in messages_dict and messages_dict["general"]:
        email_body += "### Autres canaux\n\n"
        for channel, msg_list in messages_dict["general"].items():
            email_body += f"## {channel}\n\n"
            for msg in msg_list:
                author = msg.get("author", "???")
                content = msg.get("content", "")
                # On applique un résumé
                summary = naive_summarize(content)
                # Optionnel: date / heure
                date_str = ""
                if "timestamp" in msg and isinstance(msg["timestamp"], datetime):
                    date_str = msg["timestamp"].strftime("%Y-%m-%d %H:%M")
                email_body += f"{date_str} - **{author}** : {summary}\n\n"

                #email_body += f"**{author}** a écrit :\n{summary}\n\n"

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