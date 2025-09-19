# bot/discord_bot_commands.py

"""
Description:
    Déclare les commandes du bot (ex. !send_daily_summary, !add_excluded, etc.).
    Les fonctions sont branchées sur l’instance du bot via @commands.command().

    On y définit plusieurs Cogs (EmailCog, MessagesCog, etc.).
    Chaque Cog ne reçoit que "bot" en paramètre, et accède aux
    variables globales (messages_by_channel, etc.) via self.bot.

Author: baudoux.sebastien@gmail.com  | Version: 3.1 | 2025-03-xx
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Union

# Imports internes
from bot.env_config import (
    get_email_address,
    get_email_password,
    get_recipient_email,
    get_test_recipient_email
)
from bot.mails_management import send_email, format_messages_for_email
from bot.channel_lists import save_channels
from bot.summarizer import (
    get_messages_last_24h,
    get_messages_last_72h,
    get_last_n_messages,
    format_messages_by_day
)
from bot.file_utils import save_messages_to_file, reset_messages

# Chemins vers les fichiers .txt (pour save_channels, etc.)
IMPORTANT_CHANNELS_FILE = "data/important_channels.txt"
EXCLUDED_CHANNELS_FILE  = "data/excluded_channels.txt"

# ----------------------------------------------------------------------
# 1) Cog : EmailCog
# ----------------------------------------------------------------------
class EmailCog(commands.Cog):
    """Commandes liées à l'envoi de mails et au résumé quotidien."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="preview_mail", help="Affiche dans Discord un aperçu du rapport qui serait envoyé par e-mail.")
    async def preview_mail_cmd(self, ctx):
        # On récupère la structure via self.bot
        mail_summary = format_messages_for_email(self.bot.messages_by_channel)
        if not mail_summary.strip():
            await ctx.send("Le rapport est vide (aucun message).")
            return
        if len(mail_summary) > 1900:
            preview = mail_summary[:1900] + "\n[...] (tronqué)"
        else:
            preview = mail_summary
        await ctx.send(f"**Aperçu du mail :**\n{preview}")

    @commands.command(name="send_daily_summary", help="Envoie un résumé par e-mail (24h).")
    async def send_daily_summary_cmd(self, ctx):
        # Récupère les messages <24h depuis la structure du bot
        recent_msgs = get_messages_last_24h(self.bot.messages_by_channel)
        summary = format_messages_for_email(recent_msgs)

        from_addr = get_email_address()
        password  = get_email_password()
        to_addr   = get_recipient_email()

        send_email(summary, from_addr, password, to_addr)
        await ctx.send("Résumé envoyé (24h) !")

    @commands.command(name="test_send_daily_summary", help="Envoie un résumé par e-mail à l'adresse de test.")
    async def test_send_daily_summary_cmd(self, ctx):
        summary   = format_messages_for_email(self.bot.messages_by_channel)
        from_addr = get_email_address()
        password  = get_email_password()
        to_addr   = get_test_recipient_email()

        send_email(summary, from_addr, password, to_addr)
        await ctx.send(f"Résumé envoyé à {to_addr}.")

        # Sauvegarde du cache local (self.bot.messages_by_channel)
        save_messages_to_file(self.bot.messages_by_channel)
        # reset_messages(self.bot)  # décommente si nécessaire

# ----------------------------------------------------------------------
# 2) Cog : MessagesCog
# ----------------------------------------------------------------------
class MessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="list_messages", help="Affiche tous les messages stockés, regroupés par canal.")
    async def list_messages_cmd(self, ctx):
        messages_by_channel = self.bot.messages_by_channel

        if not messages_by_channel["important"] and not messages_by_channel["general"]:
            await ctx.send("Aucun message n'est stocké pour l'instant.")
            return

        lines = ["**Messages en mémoire**", "", "(date) - [utilisateur]: <message>", ""]

        # Canaux importants
        if messages_by_channel["important"]:
            lines.append("__Canaux importants__ :")
            for channel, msgs in messages_by_channel["important"].items():
                lines.append(f"**#{channel}** :")
                for msg in msgs:
                    author = msg.get("author", "???")
                    date   = msg["timestamp"].strftime("%H:%M")
                    content = msg.get("content", "")
                    lines.append(f"- ({date}) - [{author}]: {content}")
                lines.append("")

        # Canaux généraux
        if messages_by_channel["general"]:
            lines.append("__Canaux généraux__ :")
            for channel, msgs in messages_by_channel["general"].items():
                lines.append(f"**#{channel}** :")
                for msg in msgs:
                    author = msg.get("author", "???")
                    date   = msg["timestamp"].strftime("%H:%M")
                    content = msg.get("content", "")
                    lines.append(f"- ({date}) - [{author}]: {content}")
                lines.append("")

        # Assemblage et envoi
        full_msg = "\n".join(lines)
        if len(full_msg) > 1900:
            await ctx.send(full_msg[:1900] + "\n(...) [TROP LONG, tronqué]")
        else:
            await ctx.send(full_msg)

    @commands.command(name="preview_by_day", help="Affiche les messages du jour, groupés par date.")
    async def preview_by_day_cmd(self, ctx):
        # On appelle format_messages_by_day sur la structure
        text = format_messages_by_day(self.bot.messages_by_channel)

        if len(text) > 1900:
            text = text[:1900] + "\n(...) [Tronqué]"
        await ctx.send(text)

    @commands.command(name="fetch_72h", help="Affiche les messages depuis 72h dans tous les salons (historique).")
    async def fetch_72h_cmd(self, ctx):
        """
        Récupère les messages des 72 dernières heures dans tous les salons,
        puis affiche un résumé dans Discord (ou par mail).
        """
        cutoff   = datetime.utcnow() - timedelta(hours=72)
        results  = {"important": {}, "general": {}}
        excluded = self.bot.excluded_channels
        imp_ch   = self.bot.important_channels

        for channel in ctx.guild.text_channels:
            if channel.name in excluded:
                continue
            category = "important" if channel.name in imp_ch else "general"
            collected = []
            async for msg in channel.history(limit=None, after=cutoff):
                if msg.author.bot:
                    continue
                collected.append({
                    "author": msg.author.name,
                    "content": msg.content,
                    "timestamp": msg.created_at
                })
            if collected:
                results[category][channel.name] = collected

        summary = format_messages_for_email(results)
        if len(summary) > 1900:
            await ctx.send(summary[:1900] + "\n(...) [TROP LONG, tronqué]")
        else:
            await ctx.send(summary if summary else "Aucun message trouvé dans les 72h.")

    @commands.command(name="fetch_recent", help="Récupère les 'n' derniers messages dans chaque canal textuel.")
    async def fetch_recent_cmd(self, ctx, n: int = 10):
        """
        Usage: !fetch_recent [n]
        Parcourt chaque salon textuel, récupère n messages récents, et affiche un aperçu.
        """
        results  = {"important": {}, "general": {}}
        excluded = self.bot.excluded_channels
        imp_ch   = self.bot.important_channels

        for channel in ctx.guild.text_channels:
            if channel.name in excluded:
                continue
            category = "important" if channel.name in imp_ch else "general"
            collected = []
            try:
                async for msg in channel.history(limit=n):
                    if msg.author.bot:
                        continue
                    collected.append({
                        "author": msg.author.name,
                        "content": msg.content,
                        "timestamp": msg.created_at
                    })
            except discord.Forbidden:
                continue

            if collected:
                # On pourrait faire collected.reverse() si on veut du plus ancien au plus récent
                results[category][channel.name] = collected

        summary = format_messages_for_email(results)
        if not summary.strip():
            await ctx.send("Aucun message trouvé.")
            return

        if len(summary) > 1900:
            preview = summary[:1900] + "\n[...] (tronqué)"
        else:
            preview = summary

        await ctx.send(f"**Aperçu des {n} derniers messages :**\n{preview}")

# ----------------------------------------------------------------------
# 3) Cog : CanauxCog
# ----------------------------------------------------------------------
class CanauxCog(commands.Cog):
    """Commandes pour gérer la liste des canaux importants/exclus."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _normalize_channel_name(channel: Union[str, discord.abc.GuildChannel]) -> str:
        """Retourne un nom de canal à partir d'une chaîne ou d'un objet de canal."""
        if isinstance(channel, str):
            name = channel.strip()
        elif hasattr(channel, "name"):
            name = str(channel.name).strip()
        else:
            name = str(channel).strip()

        if name.startswith("#"):
            name = name[1:]
        return name

    @commands.command(name="affiche", help="Affiche les listes des canaux importants et exclus.")
    async def affiche_cmd(self, ctx, target: str):
        """
        Usage: !affiche important
               !affiche excluded
        """
        target = target.lower()
        if target == "important":
            await ctx.send(f"Canaux importants : {self.bot.important_channels}")
        elif target == "excluded":
            await ctx.send(f"Canaux exclus : {self.bot.excluded_channels}")
        else:
            await ctx.send("Usage : `!affiche important` ou `!affiche excluded`")

    @commands.command(name="add_important", help="Ajoute un canal dans la liste des canaux importants.")
    async def add_important_cmd(self, ctx, channel: Union[str, discord.abc.GuildChannel]):
        channel_name = self._normalize_channel_name(channel)
        if not channel_name:
            await ctx.send("Nom de canal invalide.")
            return
        # Usage: !add_important <nom-de-canal>
        imp_ch = self.bot.important_channels
        if channel_name in imp_ch:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux importants.")
            return

        imp_ch.append(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, imp_ch)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {imp_ch}")

    @commands.command(name="remove_important", help="Retire un canal de la liste des canaux importants.")
    async def remove_important_cmd(self, ctx, channel: Union[str, discord.abc.GuildChannel]):
        channel_name = self._normalize_channel_name(channel)
        if not channel_name:
            await ctx.send("Nom de canal invalide.")
            return
        imp_ch = self.bot.important_channels
        if channel_name not in imp_ch:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux importants.")
            return

        imp_ch.remove(channel_name)
        save_channels(IMPORTANT_CHANNELS_FILE, imp_ch)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux importants.")
        await ctx.send(f"Canaux importants maintenant : {imp_ch}")

    @commands.command(name="add_excluded", help="Ajoute un canal à la liste des canaux exclus.")
    async def add_excluded_cmd(self, ctx, channel: Union[str, discord.abc.GuildChannel]):
        channel_name = self._normalize_channel_name(channel)
        if not channel_name:
            await ctx.send("Nom de canal invalide.")
            return
        exc_ch = self.bot.excluded_channels
        if channel_name in exc_ch:
            await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux exclus.")
            return

        exc_ch.append(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, exc_ch)
        await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {exc_ch}")

    @commands.command(name="remove_excluded", help="Retire un canal de la liste des canaux exclus.")
    async def remove_excluded_cmd(self, ctx, channel: Union[str, discord.abc.GuildChannel]):
        channel_name = self._normalize_channel_name(channel)
        if not channel_name:
            await ctx.send("Nom de canal invalide.")
            return
        exc_ch = self.bot.excluded_channels
        if channel_name not in exc_ch:
            await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux exclus.")
            return

        exc_ch.remove(channel_name)
        save_channels(EXCLUDED_CHANNELS_FILE, exc_ch)
        await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux exclus.")
        await ctx.send(f"Canaux exclus maintenant : {exc_ch}")

# ----------------------------------------------------------------------
# 4) Cog : DebugCog
# ----------------------------------------------------------------------
class DebugCog(commands.Cog):
    """Commandes de test et debug."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", help="Vérifie si le bot répond.", hidden=False)
    async def ping_command(self, ctx):
        await ctx.send("Pong!")

    @commands.command(name="test_recent_10", help="Affiche les 10 derniers messages")
    async def test_recent_10_cmd(self, ctx):
        last_10 = get_last_n_messages(self.bot.messages_by_channel, n=10)
        summary = format_messages_for_email(last_10)
        if summary.strip():
            if len(summary) > 1900:
                await ctx.send(summary[:1900] + "...")
            else:
                await ctx.send(summary)
        else:
            await ctx.send("Aucun message dans les 10 derniers.")

    @commands.command(name="test_72h", help="Affiche les messages depuis 72h")
    async def test_72h_cmd(self, ctx):
        recent  = get_messages_last_72h(self.bot.messages_by_channel)
        summary = format_messages_for_email(recent)
        if summary.strip():
            if len(summary) > 1900:
                await ctx.send(summary[:1900] + "...")
            else:
                await ctx.send(summary)
        else:
            await ctx.send("Aucun message ces dernières 72h.")

# ----------------------------------------------------------------------
# 5) Commande d’aide avancée : help2 (avec menu interactif)
# ----------------------------------------------------------------------
class CogSelect(discord.ui.Select):
    def __init__(self, cogs_with_embeds: dict[str, discord.Embed]):
        self.cogs_with_embeds = cogs_with_embeds
        options = [
            discord.SelectOption(label=cog_name, description=f"Commandes du cog {cog_name}")
            for cog_name in cogs_with_embeds.keys()
        ]
        super().__init__(placeholder="Choisissez un groupe de commandes...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cog_name = self.values[0]
        embed = self.cogs_with_embeds[cog_name]
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, cogs_with_embeds: dict[str, discord.Embed]):
        super().__init__(timeout=60)
        self.add_item(CogSelect(cogs_with_embeds))

@commands.command(name="help2", help="Affiche l'aide avec un menu interactif pour chaque Cog.")
async def help2_cmd(ctx):
    bot  = ctx.bot
    cogs = bot.cogs  # dict : { "EmailCog": instanceEmailCog, ... }
    cogs_with_embeds = {}

    # Construire un embed par cog
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

    view = HelpView(cogs_with_embeds)
    embed_init = discord.Embed(
        title="Aide interactive",
        description="Sélectionnez un cog ci-dessous pour voir ses commandes.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed_init, view=view)


# ----------------------------------------------------------------------
# 6) Fonction setup() pour charger tous les Cogs
# ----------------------------------------------------------------------
async def setup(bot: commands.Bot):
    """
    Appelée automatiquement par bot.load_extension("bot.discord_bot_commands").
    On y ajoute tous les Cogs au bot.
    """
    await bot.add_cog(EmailCog(bot))
    await bot.add_cog(MessagesCog(bot))
    await bot.add_cog(CanauxCog(bot))
    await bot.add_cog(DebugCog(bot))

    # On ajoute aussi la commande help2
    bot.add_command(help2_cmd)
    print("[SETUP] Cogs chargés avec succès.")
    return bot
# ---------------------------------------------------------------------