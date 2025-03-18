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
Author: baudoux.sebastien@gmail.com  | Version: 3.0 | 18/02/2025
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from bot.env_config import get_email_address, get_email_password, get_recipient_email, get_test_recipient_email
from bot.mails_management import send_email, format_messages_for_email
from bot.channel_lists import save_channels
from bot.summarizer import get_messages_last_24h, get_messages_last_72h, get_last_n_messages
from bot.file_utils import save_messages_to_file, reset_messages

# Chemins vers les fichiers .txt
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE = "data/excluded_channels.txt"

class EmailCog(commands.Cog):
    """Commandes liées à l'envoi de mails et au résumé quotidien."""
    def __init__(self, bot: commands.Bot, messages_by_channel, important_channels, excluded_channels):
        self.bot = bot
        self.messages_by_channel = messages_by_channel
        self.important_channels = important_channels
        self.excluded_channels = excluded_channels

    @commands.command(name="preview_mail", help="Affiche dans Discord un aperçu du rapport qui serait envoyé par e-mail.")
    async def preview_mail_cmd(self, ctx):
        # Usage: !preview_mail
        mail_summary = format_messages_for_email(self.messages_by_channel)
        if not mail_summary.strip():
            await ctx.send("Le rapport est vide (aucun message).")
            return
        # De nouveau, attention à la limite 2000 chars
        if len(mail_summary) > 1900:
            preview = mail_summary[:1900] + "\n[...] (tronqué)"
        else:
            preview = mail_summary

        await ctx.send(f"**Aperçu du mail :**\n{preview}")

    @commands.command(name="send_daily_summary", help="Envoie un résumé par e-mail (24h).")
    async def send_daily_summary_cmd(self, ctx):
        # Récupère messages <24h
        # *********************    !!!!  IMPORT DE get_messages_last_24h ??   *******
        recent_msgs = get_messages_last_24h(self.messages_by_channel)
        summary = format_messages_for_email(recent_msgs)

        from_addr = get_email_address()
        password = get_email_password()
        to_addr = get_recipient_email()

        send_email(summary, from_addr, password, to_addr)
        await ctx.send("Résumé envoyé (24h) !")

    @commands.command(name="test_send_daily_summary", help="Envoie un résumé par e-mail à l'adresse de test.")
    async def test_send_daily_summary_cmd(self, ctx):
        summary = format_messages_for_email(self.messages_by_channel)
        from_addr = get_email_address()
        password = get_email_password()
        to_addr = get_test_recipient_email()
        send_email(summary, from_addr, password, to_addr)
        await ctx.send(f"Résumé envoyé à {to_addr}.")
        # 4) Sauvegarde "recent_msgs" (les messages <24h) OU tout "self.messages_by_channel"
        save_messages_to_file(messages_by_channel)
        # 5) (Optionnel) reset / vider le cache
        # reset_messages(self.bot)

class MessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, messages_by_channel, important_channels, excluded_channels):
        self.bot = bot
        self.messages_by_channel = messages_by_channel
        self.important_channels = important_channels
        self.excluded_channels = excluded_channels

    @commands.command(name="list_messages", help="Affiche tous les messages stockés dans messages_by_channel, regroupés par canal.")
    async def list_messages_cmd(self, ctx):
        # Usage: !list_messages
        if not self.messages_by_channel["important"] and not self.messages_by_channel["general"]:
            await ctx.send("Aucun message n'est stocké pour l'instant.")
            return
        lines = []
        lines.append("**Messages en mémoire**\n\n (date) - [utilisateur]:<message>\n\n")
        # Canaux importants
        if self.messages_by_channel["important"]:
            lines.append("__Canaux importants__:")
            for channel, msgs in self.messages_by_channel["important"].items():
                lines.append(f"**#{channel}**:")
                for msg in msgs:
                    author = msg.get("author", "???")
                    date = msg["timestamp"].strftime("%H:%M")
                    content = msg.get("content", "")
                    lines.append(f"- ({date}) - [{author}]: {content}")
                lines.append("")  # saut de ligne
        # Canaux généraux
        if self.messages_by_channel["general"]:
            lines.append("__Canaux généraux__:")
            for channel, msgs in self.messages_by_channel["general"].items():
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

    @commands.command(name="preview_by_day", help="Affiche les messages du jour ??")
    async def preview_by_day_cmd(self, ctx):
        from bot.mermaid_utils import format_messages_by_day  # ex
        text = format_messages_by_day(self.messages_by_channel)
        # Tronquer si trop long
        if len(text) > 1900:
            text = text[:1900] + "\n(...) [Tronqué]"
        await ctx.send(text)

    @commands.command(name="fetch_72h", help="Affiche les messages depuis 72h")
    async def fetch_72h_cmd(self, ctx):
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
            if channel_name in self.excluded_channels:
                continue
            # Déterminer la catégorie "important" ou "general"
            if channel_name in self.important_channels:
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
        # Maintenant, on peut formater. Tu peux appeler format_messages_for_email si tu veux le rendu "mail"
        summary = format_messages_for_email(results)  # Suppose que tu importes format_messages_for_email
        # Envoyer l'aperçu dans Discord (attention à la limite 2000 caractères)
        if len(summary) > 1900:
            await ctx.send(summary[:1900] + "\n(...) [TROP LONG, tronqué]")
        else:
            await ctx.send(summary if summary else "Aucun message trouvé dans les 72h.")

    @commands.command(name="fetch_recent", help="Récupère les 'n' derniers messages dans chaque canal textuel, classés en 'important' ou 'general' selon la config.")
    async def fetch_recent_cmd(self, ctx, n: int = 10):
        # Usage: !fetch_recent [n] (par défaut, n = 10)
        # Structure locale pour stocker les messages récupérés
        results = {
            "important": {},
            "general": {}
        }
        # Parcours tous les canaux textuels du serveur
        for channel in ctx.guild.text_channels:
            channel_name = channel.name
            # Ignorer les canaux exclus
            if channel_name in self.excluded_channels:
                continue
            # Déterminer la catégorie
            if channel_name in self.important_channels:
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

class CanauxCog(commands.Cog):
    # Commandes pour gèrer les canaux
    def __init__(self, bot: commands.Bot, messages_by_channel, important_channels, excluded_channels):
        self.bot = bot
        self.messages_by_channel = messages_by_channel
        self.important_channels = important_channels
        self.excluded_channels = excluded_channels
    @commands.command(name="affiche", help="Affiche les listes des canaux importants et exclus")
    async def affiche_cmd(self, ctx, target: str):
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

    @commands.command(name="add_important", help="Ajout un canal dans la liste des canaux importants")
    async def add_important_cmd(self, ctx, channel_name: str):
        # Usage: !add_important <nom-de-canal>
        if channel_name in important_channels:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux importants.")
            return

        important_channels.append(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {important_channels}")

    @commands.command(name="remove_important", help="Retire un canal de la liste des canaux importants.")
    async def remove_important_cmd(self, ctx, channel_name: str):
        # Usage: !remove_important <nom-de-canal>
        if channel_name not in important_channels:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux importants.")
            return

        important_channels.remove(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {important_channels}")

    @commands.command(name="add_excluded", help="Ajoute un canal à la liste des canaux exclus.")
    async def add_excluded_cmd(self, ctx, channel_name: str):
        # Usage: !add_excluded <nom-de-canal>
        if channel_name in excluded_channels:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux exclus.")
            return

        excluded_channels.append(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {excluded_channels}")        

    @commands.command(name="remove_excluded", help="Retire un canal de la liste des canaux exclus.")
    async def remove_excluded_cmd(self, ctx, channel_name: str):
        # Usage: !remove_excluded <nom-de-canal>
        if channel_name not in excluded_channels:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux exclus.")
            return

        excluded_channels.remove(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {excluded_channels}")

class DebugCog(commands.Cog):
    """Commandes de test et debug."""
    def __init__(self, bot: commands.Bot, messages_by_channel, important_channels, excluded_channels):
        self.bot = bot
        self.messages_by_channel = messages_by_channel
        self.important_channels = important_channels
        self.excluded_channels = excluded_channels

    @commands.command(name="ping", help="Vérifie si le bot répond.", hidden=False)
    async def ping_command(self, ctx):
        await ctx.send("Pong!")

    @commands.command(name="test_recent_10", help="Affiche les 10 derniers messages")
    async def test_recent_10_cmd(self, ctx):
        last_10 = get_last_n_messages(self.messages_by_channel, n=10)
        # Faire un petit formatage, ou direct preview
        summary = format_messages_for_email(last_10)
        if summary.strip():
            await ctx.send(summary[:1900] + "..." if len(summary) > 1900 else summary)
        else:
            await ctx.send("Aucun message dans les 10 derniers.")

    @commands.command(name="test_72h", help="Affiche les messages depuis 72h")
    async def test_72h_cmd(self, ctx):
        recent = get_messages_last_72h(self.messages_by_channel)
        summary = format_messages_for_email(recent)
        if summary.strip():
            await ctx.send(summary[:1900] + "..." if len(summary) > 1900 else summary)
        else:
            await ctx.send("Aucun message ces dernières 72h.")

# Premier menu => choisit le Cog
# Deuxième menu => affiche les "commandes" disponibles dans ce Cog
# (ou un menu dynamique créé en callback)
"""
class CogSelect(discord.ui.Select):
    def __init__(self, all_cogs):
        self.all_cogs = all_cogs
        options = [discord.SelectOption(label=cog_name) for cog_name in all_cogs.keys()]
        super().__init__(placeholder="Choisissez un Cog...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        # On récupère la liste des commandes
        commands_list = self.all_cogs[cog_name].get_commands()

        # On construit un 2e menu, "CommandSelect"
        view = CommandSelectionView(commands_list)
        embed = discord.Embed(title=f"Cog {cog_name}", description="Choisissez la commande à exécuter :")
        await interaction.response.edit_message(embed=embed, view=view)


class CommandSelect(discord.ui.Select):
    def __init__(self, commands_list):
        self.commands_list = commands_list
        options = []
        for cmd in commands_list:
            options.append(discord.SelectOption(label=cmd.name, description=cmd.help or ""))
        super().__init__(placeholder="Choisissez une commande...", options=options)

    async def callback(self, interaction: discord.Interaction):
        chosen_cmd_name = self.values[0]
        # Exécuter la commande, ex. via bot.get_command(chosen_cmd_name)
        command_obj = interaction.client.get_command(chosen_cmd_name)  # client = bot
        if command_obj:
            # on "simule" l'appel => on a besoin d'un contexte ou d'un pseudo-contexte
            # c'est le plus compliqué, car y'a pas de ctx direct en slash
            # => plus simple : coder la logique en dur ou faire un mini callback
            await interaction.response.send_message(f"Commande {chosen_cmd_name} déclenchée (WIP).")
        else:
            await interaction.response.send_message("Impossible de trouver la commande.")


class CommandSelectionView(discord.ui.View):
    def __init__(self, commands_list):
        super().__init__()
        self.add_item(CommandSelect(commands_list))

class HelpView(discord.ui.View):
    def __init__(self, all_cogs):
        super().__init__()
        self.add_item(CogSelect(all_cogs))

@commands.command(name="help2")
async def help2_cmd(ctx):
    bot = ctx.bot
    all_cogs = bot.cogs
    view = HelpView(all_cogs)
    embed = discord.Embed(title="Choisissez un Cog pour voir ses commandes.")
    await ctx.send(embed=embed, view=view)

"""

class CogSelect(discord.ui.Select):
    def __init__(self, cogs_with_embeds: dict[str, discord.Embed]):
        #Construit un menu déroulant avec une option par Cog.
        self.cogs_with_embeds = cogs_with_embeds
        
        options = []
        for cog_name in cogs_with_embeds.keys():
            options.append(discord.SelectOption(
                label=cog_name,
                description=f"Commandes du cog {cog_name}"
            ))
        
        super().__init__(
            placeholder="Choisissez un groupe de commandes...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        #Quand l'utilisateur sélectionne un cog dans la liste.
        cog_name = self.values[0]  # ex: "EmailCog", "DebugCog", etc.
        embed = self.cogs_with_embeds[cog_name]
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    #Une View qui contient seulement notre menu déroulant de cogs.
    def __init__(self, cogs_with_embeds: dict[str, discord.Embed]):
        super().__init__(timeout=60)  # 60s d'inactivité avant que les interractions se désactivent
        self.add_item(CogSelect(cogs_with_embeds))

@commands.command(name="help2", help="Affiche l'aide avec un menu de sélection pour chaque Cog.")
async def help2_cmd(ctx):
    # Cette commande génère un embed vide initial, plus un menu de sélection permettant de naviguer d'un Cog à l'autre.
    bot = ctx.bot
    cogs = bot.cogs  # dict {NomDuCog: instanceDeCog, ...}

    # 1) Construire un dictionnaire de 'NomDuCog' -> 'Embed'
    cogs_with_embeds = {}

    for cog_name, cog_instance in cogs.items():
        commands_list = cog_instance.get_commands()
        
        embed = discord.Embed(
            title=f"Aide - {cog_name}",
            description=f"Commandes du cog {cog_name}",
            color=discord.Color.blue()
        )
        for cmd in commands_list:
            if cmd.hidden:
                continue
            desc = cmd.help if cmd.help else "Pas de description"
            embed.add_field(name=f"!{cmd.name}", value=desc, inline=False)
        
        cogs_with_embeds[cog_name] = embed

    # 2) Créer la View
    view = HelpView(cogs_with_embeds)

    # 3) Envoyer un "embed initial" + la View
    #    L'embed initial pourrait être un message d'accueil générique
    embed_init = discord.Embed(
        title="Aide interactive",
        description="Sélectionnez un groupe (Cog) ci-dessous pour voir les commandes.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed_init, view=view)

# -----------------------------------------------------------------
# Pagination "custom" pour l'aide : on va faire une commande `help2` (par ex.)
# qui affiche chaque Cog sur une page différente.
# -----------------------------------------------------------------
"""
@commands.command(name="help2", help="Affiche l'aide avec pagination par Cog.")
async def help2_cmd(ctx):
    #Commande d'aide paginée (une page par Cog)
    bot = ctx.bot
    cogs = bot.cogs  # Dictionnaire { 'NomDuCog': instanceDuCog, ... }
    pages = []
    for cog_name, cog_instance in cogs.items():
        # Récupération des commandes du cog
        commands_list = cog_instance.get_commands()
        # Construire un embed
        embed = discord.Embed(
            title=f"Aide - {cog_name}",
            description=f"Commandes du cog {cog_name}",
            color=discord.Color.blue()
        )
        for cmd in commands_list:
            if cmd.hidden:
                continue
            desc = cmd.help if cmd.help else "Pas de description"
            embed.add_field(name=f"!{cmd.name}", value=desc, inline=False)
        pages.append(embed)
    # Petit helper de pagination avec réactions (exemple simplifié)
    index = 0
    message = await ctx.send(embed=pages[index])
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return (
            user == ctx.author
            and str(reaction.emoji) in ["⬅️", "➡️"]
            and reaction.message.id == message.id
        )
    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
        except:
            break
        else:
            if str(reaction.emoji) == "⬅️":
                index = (index - 1) % len(pages)
            else:
                index = (index + 1) % len(pages)

            await message.edit(embed=pages[index])
            await message.remove_reaction(reaction.emoji, user)
"""
# -----------------------------------------------------------------
# La fonction setup() qui sera appelée depuis core.py pour charger ce fichier
# NOTE : selon la version de discord.py/py-cord, c'est parfois `async def setup(bot):`
#        et on utilise `await bot.add_cog(...)`.
# -----------------------------------------------------------------
async def setup(bot):
    # Récupérez les variables stockées sur bot
    msgs = bot.messages_by_channel
    imp = bot.important_channels
    excl = bot.excluded_channels
    
    # async def setup(bot: commands.Bot, messages_by_channel, important_channels, excluded_channels):
    """Cette fonction est appelée par votre core.py pour initialiser les Cogs."""
    # On crée une instance de chaque Cog et on l'ajoute
    await bot.add_cog(EmailCog(bot, msgs, imp, excl))
    await bot.add_cog(MessagesCog(bot, msgs, imp, excl))    
    await bot.add_cog(CanauxCog(bot, msgs, imp, excl))
    await bot.add_cog(DebugCog(bot, msgs, imp, excl))    
    # await bot.add_cog(EmailCog(bot, messages_by_channel, important_channels, excluded_channels))
    # await bot.add_cog(MessagesCog(bot, messages_by_channel, important_channels, excluded_channels))
    # await bot.add_cog(CanauxCog(bot, messages_by_channel, important_channels, excluded_channels))
    # await bot.add_cog(DebugCog(bot, messages_by_channel, important_channels, excluded_channels))
    # On peut aussi ajouter la commande help2 directement au bot
    bot.add_command(help2_cmd)

