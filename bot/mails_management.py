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

import asyncio
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from bot.env_config import (
    get_email_smtp_host,
    get_email_smtp_port,
    get_email_smtp_timeout,
)
from bot.summarizer import naive_summarize

DEFAULT_SMTP_HOST = "ssl0.ovh.net"
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_TIMEOUT = 30.0


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
    Returns: str: Le corps de l'e-mail (Markdown / texte brut).
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
    return email_body


def _send_email_sync(
    body: str,
    from_addr: str,
    password: str,
    to_addr: str,
    *,
    host: str,
    port: int,
    timeout: Optional[float],
):
    """Envoie un e-mail de manière synchrone via SMTP."""
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = "Test mail"
    msg.attach(MIMEText(body, "plain"))

    smtp_kwargs = {}
    if timeout is not None:
        smtp_kwargs["timeout"] = timeout
    with smtplib.SMTP(host, port, **smtp_kwargs) as server:
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())


async def send_email(
    body: str,
    from_addr: str,
    password: str,
    to_addr: str,
    *,
    host: Optional[str] = None,
    port: Optional[int] = None,
    timeout: Optional[float] = None,
):
    """Enveloppe asynchrone qui envoie un e-mail via SMTP dans un thread."""
    resolved_host = host or get_email_smtp_host(DEFAULT_SMTP_HOST)
    resolved_port = port if port is not None else get_email_smtp_port(DEFAULT_SMTP_PORT)
    resolved_timeout = (
        timeout if timeout is not None else get_email_smtp_timeout(DEFAULT_SMTP_TIMEOUT)
    )
    await asyncio.to_thread(
        _send_email_sync,
        body,
        from_addr,
        password,
        to_addr,
        host=resolved_host,
        port=resolved_port,
        timeout=resolved_timeout,
    )
