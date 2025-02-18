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

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from bot.env_config import get_email_address, get_email_password, get_recipient_email, get_test_recipient_email
from bot.mails_management import send_email, format_messages_for_email
from bot.channel_lists import save_channels
from bot.summarizer import get_messages_last_72h, get_last_n_messages

# Chemins vers les fichiers .txt
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE = "data/excluded_channels.txt"

def setup_bot_commands(bot, messages_by_channel, important_channels, excluded_channels):
    """
    Description:
        Fonction à appeler depuis core.py pour enregistrer les commandes
        sur l'instance 'bot'.
    Uses:
        bot (discord.ext.commands.Bot),
        messages_by_channel : dict,
        important_channels : list of str,
        excluded_channels : list of str
    Args:
        - bot
        - messages_by_channel
        - important_channels
        - excluded_channels
    Returns: None
    ---
    Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
    """
    print("=== DEBUG: setup_bot_commands() est appelé ===")
    print(f"=== DEBUG: important_channels = {important_channels}, excluded_channels = {excluded_channels} ===")

    """
    Liste des commandes :
        - send_daily_summary
        - test_send_daily_summary
        - chan_list
        - ping
        - add_important
        - remove_important
        - add_excluded
        - remove_excluded
        - aide
    """

    @bot.command(name="send_daily_summary")
    async def send_daily_summary_cmd(ctx):
        # On récupère uniquement les messages de moins de 24h
        recent_msgs = get_messages_last_24h(messages_by_channel)

        # Puis on formate
        summary = format_messages_for_email(recent_msgs)

        # On envoie le mail
        from_addr = get_email_address()
        password = get_email_password()
        to_addr = get_recipient_email()
        send_email(summary, from_addr, password, to_addr)

        # Message de confirmation dans Discord
        await ctx.send("Résumé envoyé (24h) !")

    @bot.command(name="test_send_daily_summary")
    async def test_send_daily_summary_cmd(ctx):
        """
        Description:
            Commande !test_send_daily_summary : envoie immédiatement un résumé par e-mail.
        Args:
            ctx : Context - contexte d'exécution de la commande
        Returns: None
        ---
        Author: ...
        """
        summary = format_messages_for_email(messages_by_channel)
        from_addr = get_email_address()
        password  = get_email_password()
        to_addr   = get_test_recipient_email()

        send_email(summary, from_addr, password, to_addr)
        await ctx.send(f"Résumé envoyé à {to_addr}.")


    @bot.command(name="list_messages")
    async def list_messages_cmd(ctx):
        """
        Affiche tous les messages stockés dans messages_by_channel,
        regroupés par canal. Pour debug ou pour voir ce qui sera envoyé.
        Usage: !list_messages
        """
        if not messages_by_channel["important"] and not messages_by_channel["general"]:
            await ctx.send("Aucun message n'est stocké pour l'instant.")
            return

        lines = []
        lines.append("**Messages en mémoire**\n\n (date) - [utilisateur]:<message>\n\n")

        # Canaux importants
        if messages_by_channel["important"]:
            lines.append("__Canaux importants__:")
            for channel, msgs in messages_by_channel["important"].items():
                lines.append(f"**#{channel}**:")
                for msg in msgs:
                    author = msg.get("author", "???")
                    date = msg["timestamp"].strftime("%H:%M")
                    content = msg.get("content", "")
                    lines.append(f"- ({date}) - [{author}]: {content}")
                lines.append("")  # saut de ligne

        # Canaux généraux
        if messages_by_channel["general"]:
            lines.append("__Canaux généraux__:")
            for channel, msgs in messages_by_channel["general"].items():
                lines.append(f"**#{channel}**:")
                for msg in msgs:
                    author = msg.get("author", "???")
                    date = msg["timestamp"].strftime("%H:%M")
                    content = msg.get("content", "")
                    lines.append(f"- ({date}) - [{author}]: {content}")
                lines.append("")

        # On assemble tout
        full_msg = "\n".join(lines)

        # Discord limite un message à ~2000 caractères, on coupe si besoin :
        if len(full_msg) > 1900:
            await ctx.send(full_msg[:1900] + "\n(...) [TROP LONG, tronqué]")
        else:
            await ctx.send(full_msg)


    @bot.command(name="preview_mail")
    async def preview_mail_cmd(ctx):
        """
        Affiche dans Discord un aperçu du rapport qui serait envoyé par e-mail.
        Usage: !preview_mail
        """
        from bot.mails_management import format_messages_for_email
        mail_summary = format_messages_for_email(messages_by_channel)

        if not mail_summary.strip():
            await ctx.send("Le rapport est vide (aucun message).")
            return

        # De nouveau, attention à la limite 2000 chars
        if len(mail_summary) > 1900:
            preview = mail_summary[:1900] + "\n[...] (tronqué)"
        else:
            preview = mail_summary

        await ctx.send(f"**Aperçu du mail :**\n{preview}")


    @bot.command(name="test_recent_10")
    async def test_recent_10_cmd(ctx):
        last_10 = get_last_n_messages(messages_by_channel, n=10)
        # Faire un petit formatage, ou direct preview
        summary = format_messages_for_email(last_10)
        if summary.strip():
            await ctx.send(summary[:1900] + "..." if len(summary) > 1900 else summary)
        else:
            await ctx.send("Aucun message dans les 10 derniers.")


    @bot.command(name="test_72h")
    async def test_72h_cmd(ctx):
        recent = get_messages_last_72h(messages_by_channel)
        summary = format_messages_for_email(recent)
        if summary.strip():
            await ctx.send(summary[:1900] + "..." if len(summary) > 1900 else summary)
        else:
            await ctx.send("Aucun message ces dernières 72h.")
            


    @bot.command(name="ping", help="Vérifie si le bot répond.")
    async def ping_command(ctx):
        """
        Commande simple !ping => le bot répond "Pong!"
        """
        await ctx.send("Pong!")

    # -------------------------
    # Affiche les canaux de la liste passée en paramètre. 
    # -------------------------
    @bot.command(name="affiche")
    async def affiche_cmd(ctx, target: str):
        """
        Affiche la liste des canaux d'une liste donnée.
        Usage: !affiche important   ou   !affiche excluded
        """
        target = target.lower()
        if target == "important":
            await ctx.send(f"Canaux importants : {important_channels}")
        elif target == "excluded":
            await ctx.send(f"Canaux exclus : {excluded_channels}")
        else:
            await ctx.send("Usage : `!affiche important` ou `!affiche excluded`")

    # -------------------------
    # Ajouter un canal à la liste "importants"
    # -------------------------
    @bot.command(name="add_important")
    async def add_important_cmd(ctx, channel_name: str):
        """
        Ajoute un canal à la liste des canaux importants.
        Usage: !add_important <nom-de-canal>
        """
        if channel_name in important_channels:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux importants.")
            return

        important_channels.append(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {important_channels}")

    # -------------------------
    # Retirer un canal de la liste "importants"
    # -------------------------
    @bot.command(name="remove_important")
    async def remove_important_cmd(ctx, channel_name: str):
        """
        Retire un canal de la liste des canaux importants.
        Usage: !remove_important <nom-de-canal>
        """
        if channel_name not in important_channels:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux importants.")
            return

        important_channels.remove(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {important_channels}")

    # -------------------------
    # Ajouter un canal à la liste "exclus"
    # -------------------------
    @bot.command(name="add_excluded")
    async def add_excluded_cmd(ctx, channel_name: str):
        """
        Ajoute un canal à la liste des canaux exclus.
        Usage: !add_excluded <nom-de-canal>
        """
        if channel_name in excluded_channels:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux exclus.")
            return

        excluded_channels.append(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {excluded_channels}")

    # -------------------------
    # Retirer un canal de la liste "exclus"
    # -------------------------
    @bot.command(name="remove_excluded")
    async def remove_excluded_cmd(ctx, channel_name: str):
        """
        Retire un canal de la liste des canaux exclus.
        Usage: !remove_excluded <nom-de-canal>
        """
        if channel_name not in excluded_channels:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux exclus.")
            return

        excluded_channels.remove(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {excluded_channels}")



    @bot.command(name="preview_by_day")
    async def preview_by_day_cmd(ctx):
        from bot.mermaid_utils import format_messages_by_day  # ex
        text = format_messages_by_day(messages_by_channel)
        # Tronquer si trop long
        if len(text) > 1900:
            text = text[:1900] + "\n(...) [Tronqué]"
        await ctx.send(text)


    @bot.command(name="fetch_72h")
    async def fetch_72h_cmd(ctx):
        """
        Récupère les messages des 72 dernières heures 
        dans tous les salons, sans se baser sur on_message,
        puis affiche un résumé dans Discord (ou envoi mail).
        """

        # Nouveau dictionnaire local
        results = {"important": {}, "general": {}}
        
        cutoff = datetime.utcnow() - timedelta(hours=72)
        
        for channel in ctx.guild.text_channels:
            channel_name = channel.name
            
            # Ignorer les canaux exclus
            if channel_name in excluded_channels:
                continue

            # Déterminer la catégorie "important" ou "general"
            if channel_name in important_channels:
                category = "important"
            else:
                category = "general"
            
            collected_msgs = []
            
            # Parcourir l'historique du canal après "cutoff"
            async for msg in channel.history(limit=None, after=cutoff):
                # Tu peux filtrer les messages d'un bot si tu veux
                if msg.author.bot:
                    continue
                # On stocke les infos utiles
                collected_msgs.append({
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at  # msg.created_at est en UTC
                })
            
            if collected_msgs:
                results[category][channel_name] = collected_msgs
        
        # Maintenant, on peut formater
        # (Tu peux appeler format_messages_for_email si tu veux le rendu "mail")
        summary = format_messages_for_email(results)  # Suppose que tu importes format_messages_for_email

        # Envoyer l'aperçu dans Discord (attention à la limite 2000 caractères)
        if len(summary) > 1900:
            await ctx.send(summary[:1900] + "\n(...) [TROP LONG, tronqué]")
        else:
            await ctx.send(summary if summary else "Aucun message trouvé dans les 72h.")



    @bot.command(name="fetch_recent")
    async def fetch_recent_cmd(ctx, n: int = 10):
        """
        Récupère les 'n' derniers messages dans chaque canal textuel,
        classés en 'important' ou 'general' selon la config.
        
        Usage: !fetch_recent [n]
        (par défaut, n = 10)
        """
        # Structure locale pour stocker les messages récupérés
        results = {
            "important": {},
            "general": {}
        }

        # Parcours tous les canaux textuels du serveur
        for channel in ctx.guild.text_channels:
            channel_name = channel.name
            
            # Ignorer les canaux exclus
            if channel_name in excluded_channels:
                continue
            
            # Déterminer la catégorie
            if channel_name in important_channels:
                category = "important"
            else:
                category = "general"
            
            collected_msgs = []

            # Récupère jusqu'à 'n' messages récents (les plus récents en premier)
            try:
                async for msg in channel.history(limit=n):
                    # Optionnel : ignorer les messages du bot
                    if msg.author.bot:
                        continue
                    
                    collected_msgs.append({
                        "author": msg.author.name,
                        "content": msg.content,
                        "timestamp": msg.created_at
                    })
            except discord.Forbidden:
                # Si le bot n'a pas les permissions pour lire l'historique
                continue
            
            # Si on a trouvé des messages, on les stocke
            if collected_msgs:
                # Ici, collected_msgs est dans l'ordre "du plus récent au plus ancien"
                # Si tu veux inverser pour avoir du plus ancien au plus récent, fais:
                # collected_msgs.reverse()
                results[category][channel_name] = collected_msgs

        # Maintenant, on formate ces messages (ex. pour un aperçu)
        # Suppose que format_messages_for_email(...) est importé de mails_management
        summary = format_messages_for_email(results)

        if not summary.strip():
            await ctx.send("Aucun message trouvé.")
            return

        # Discord a une limite de 2000 caractères par message
        if len(summary) > 1900:
            preview = summary[:1900] + "\n[...] (tronqué)"
        else:
            preview = summary

        await ctx.send(f"**Aperçu des {n} derniers messages :**\n{preview}")




    # -------------------------
    # Liste des commandes du bot
    # -------------------------    
    @bot.command(name="aide")
    async def aide_cmd(ctx):
        """
        Description:
            Affiche la liste des commandes du bot, en se basant 
            sur la liste bot.commands.
        """
        embed = discord.Embed(
            title="**Liste des commandes disponibles :**\n",
            description="Voici un récapitulatif des commandes disponibles.",
            color=discord.Color.blue()  # Couleur de l'embed
        )

        for cmd in bot.commands:
            # cmd.name = nom de la commande (ex: "ping")
            # cmd.help = aide (si tu l'as renseignée en paramètre help=..., 
            #                  ou si tu écris docstring + assignation)
            if cmd.hidden:
                # Si tu veux ignorer les commandes "cachées"
                continue
            # Soit on utilise cmd.help, soit on récupère la docstring 
            # si tu l'as associée
            desc = cmd.help if cmd.help else "(Pas de description fournie)"
            embed.add_field(name=f"!{cmd.name}", value=desc, inline=False)

        await ctx.send(embed=embed)
