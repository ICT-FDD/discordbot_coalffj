# bot/discord_bot_commands.py

"""
Description:
    Déclare les commandes du bot (ex. !send_daily_summary, !add_excluded, etc.).
    Les fonctions sont branchées sur l'instance 'bot' via decorators @bot.command.
Uses:
    - channel_lists pour mettre à jour les listes
    - mails_management pour envoyer des mails
    - summarizer pour éventuellement résumer dans une commande
Args: (Reçoit le bot et les structures de données en paramètres via setup_bot_commands)
Returns: (Ne retourne rien, les commandes sont enregistrées dans l'objet bot)
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

from discord.ext import commands
from bot.env_config import get_email_address, get_email_password, get_recipient_email
from bot.channel_lists import save_channels
from bot.mails_management import send_email, format_messages_for_email

def setup_bot_commands(bot, messages_by_channel):
    """
    Description:
        Fonction à appeler depuis core.py pour enregistrer les commandes
        sur l'instance 'bot'.
    Uses: bot (discord.ext.commands.Bot)
    Args: (bot : objet Bot)
          (messages_by_channel : dict - structure de stockage des messages)
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """

    @bot.command(name="send_daily_summary")
    async def send_daily_summary(ctx):
        """
        Description:
            Commande !send_daily_summary : envoie immédiatement un résumé par e-mail.
        Args: (ctx : Context - contexte d'exécution de la commande)
        Returns: None
        ---
        Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
        """
        
        summary = format_messages_for_email(messages_by_channel)
        from_addr = get_email_address()
        password  = get_email_password()
        to_addr   = get_recipient_email()

        send_email(summary, from_addr, password, to_addr)
        await ctx.send("Résumé envoyé.")

    # Ajoute d'autres commandes ici...
    # @bot.command(name="add_excluded"), etc.
