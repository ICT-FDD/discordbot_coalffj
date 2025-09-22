# bot/discord_bot_commands.py
"""
Description:
    Commandes du bot (!preview_mail, !add_important, …) + helpers
    pour stocker les listes dans des messages du canal #bot-storage.
Author: baudoux.sebastien@gmail.com  | Version: 3.2 | 2025-09-19
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import discord
from discord.ext import commands

# Imports internes
from bot.env_config import (
    get_email_address,
    get_email_password,
    get_recipient_email,
    get_test_recipient_email,
    get_bot_storage_channel_id,
)
from bot.mails_management import send_email, format_messages_for_email
from bot.summarizer import (
    get_messages_last_24h,
    get_messages_last_72h,
    get_last_n_messages,
    format_messages_by_day,
)
from bot.file_utils import save_messages_to_file

# ============================================================
# Helpers : stockage des listes dans des messages Discord
# (version auto-bootstrapping : pas besoin d'IDs dans .env)
# ============================================================
STORE_TEMPLATE = {
    "version": 1,
    "updated_at": None,
    "data": []
}

TAG_IMPORTANT = "[[STORE:important_channels]]"
TAG_EXCLUDED  = "[[STORE:excluded_channels]]"

def _render_store_payload(tag: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"{tag}\n```json\n{body}\n```"

def _parse_store_message(content: str) -> dict:
    try:
        if "```json" in content:
            json_part = content.split("```json", 1)[1].split("```", 1)[0]
            return json.loads(json_part)
        return json.loads(content)  # tolérant
    except Exception:
        return dict(STORE_TEMPLATE)

async def _find_store_message(channel: discord.TextChannel, tag: str, bot_user_id: int):
    """Cherche un message contenant 'tag' ET écrit par le bot."""
    async for msg in channel.history(limit=100):
        if msg.author.id == bot_user_id and tag in (msg.content or ""):
            return msg
    return None

async def _ensure_message(channel: discord.TextChannel, tag: str, bot_user_id: int):
    """Retourne (message, payload). Crée si absent ou non éditable."""
    msg = await _find_store_message(channel, tag, bot_user_id)
    if msg is None:
        payload = dict(STORE_TEMPLATE)
        rendered = _render_store_payload(tag, payload)
        msg = await channel.send(rendered)
        return msg, payload

    payload = _parse_store_message(msg.content or "")
    return msg, payload

async def ensure_storage_loaded(bot: commands.Bot):
    """
    Charge/initialise les deux messages de stockage dans #bot-storage.
    - Si aucun message 'propre' appartenant au bot: on les crée.
    - Remplit bot.important_channels / bot.excluded_channels et bot._store.
    """
    storage_channel_id = get_bot_storage_channel_id()
    if not storage_channel_id:
        raise RuntimeError("BOT_STORAGE_CHANNEL_ID manquant dans .env")

    channel = bot.get_channel(storage_channel_id) or await bot.fetch_channel(storage_channel_id)
    bot_user_id = bot.user.id

    imp_msg, imp_payload = await _ensure_message(channel, TAG_IMPORTANT, bot_user_id)
    exc_msg, exc_payload = await _ensure_message(channel, TAG_EXCLUDED,  bot_user_id)

    bot._store = {
        "channel": channel,
        "important": {"message": imp_msg, "payload": imp_payload, "tag": TAG_IMPORTANT},
        "excluded":  {"message": exc_msg, "payload": exc_payload, "tag": TAG_EXCLUDED},
    }
    bot.important_channels = list(imp_payload.get("data", []))
    bot.excluded_channels  = list(exc_payload.get("data", []))

async def save_list_to_store(bot: commands.Bot, key: str, new_list: list[str]):
    """
    Écrit la liste (triée, unique) dans le message #bot-storage du bot.
    key ∈ {'important', 'excluded'}.
    """
    entry = bot._store[key]
    payload = dict(entry.get("payload") or STORE_TEMPLATE)
    payload["data"] = sorted(set(new_list))
    payload["version"] = int(payload.get("version", 0)) + 1
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    rendered = _render_store_payload(entry["tag"], payload)
    await entry["message"].edit(content=rendered)

    # maj mémoire
    entry["payload"] = payload
    if key == "important":
        bot.important_channels = payload["data"]
    else:
        bot.excluded_channels = payload["data"]


# ============================================================
# 1) Cog : EmailCog
# ============================================================
class EmailCog(commands.Cog):
    """Commandes liées à l'envoi de mails et au résumé quotidien."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="preview_mail", help="Aperçu du rapport e-mail.")
    async def preview_mail_cmd(self, ctx):
        mail_summary = format_messages_for_email(self.bot.messages_by_channel)
        if not mail_summary.strip():
            await ctx.send("Le rapport est vide (aucun message).")
            return
        await ctx.send(mail_summary[:1900] + ("\n[...] (tronqué)" if len(mail_summary) > 1900 else ""))

    @commands.command(name="send_daily_summary", help="Envoie un résumé par e-mail (24h).")
    async def send_daily_summary_cmd(self, ctx):
        recent_msgs = get_messages_last_24h(self.bot.messages_by_channel)
        summary = format_messages_for_email(recent_msgs)

        from_addr = get_email_address()
        password = get_email_password()
        to_addr = get_recipient_email()

        try:
            await send_email(summary, from_addr, password, to_addr)
            await ctx.send("✅ Résumé envoyé (24h) !")
        except Exception as e:
            await ctx.send(f"❌ Échec de l’envoi : {e!s}")

    @commands.command(name="test_send_daily_summary", help="Envoie un résumé par e-mail (test immédiat).")
    async def test_send_daily_summary_cmd(self, ctx):
        summary = format_messages_for_email(self.bot.messages_by_channel)
        from_addr = get_email_address()
        password = get_email_password()
        to_addr = get_test_recipient_email()

        try:
            await send_email(summary, from_addr, password, to_addr)
            await ctx.send(f"✅ Résumé envoyé à {to_addr}.")
        except Exception as e:
            await ctx.send(f"❌ Échec de l’envoi : {e!s}")
        finally:
            save_messages_to_file(self.bot.messages_by_channel)

# ============================================================
# 2) Cog : MessagesCog
# ============================================================
class MessagesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="list_messages", help="Affiche les messages groupés par canal.")
    async def list_messages_cmd(self, ctx):
        messages_by_channel = self.bot.messages_by_channel

        if not messages_by_channel["important"] and not messages_by_channel["general"]:
            await ctx.send("Aucun message n'est stocké pour l'instant.")
            return

        lines = ["**Messages en mémoire**", "", "(date) - [utilisateur]: <message>", ""]

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

        full_msg = "\n".join(lines)
        await ctx.send(full_msg[:1900] + ("\n(...) [TROP LONG, tronqué]" if len(full_msg) > 1900 else ""))

    @commands.command(name="preview_by_day", help="Affiche les messages du jour, groupés par date.")
    async def preview_by_day_cmd(self, ctx):
        text = format_messages_by_day(self.bot.messages_by_channel)
        await ctx.send(text[:1900] + ("\n(...) [Tronqué]" if len(text) > 1900 else ""))

    @commands.command(name="fetch_72h", help="Affiche les messages depuis 72h dans tous les salons.")
    async def fetch_72h_cmd(self, ctx):
        recent  = get_messages_last_72h(self.bot.messages_by_channel)
        summary = format_messages_for_email(recent)
        if not summary.strip():
            await ctx.send("Aucun message ces dernières 72h.")
        else:
            await ctx.send(summary[:1900] + ("\n(...) [TROP LONG, tronqué]" if len(summary) > 1900 else ""))

    @commands.command(name="fetch_recent", help="Récupère les 'n' derniers messages par salon.")
    async def fetch_recent_cmd(self, ctx, n: int = 10):
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
                results[category][channel.name] = collected

        summary = format_messages_for_email(results)
        if not summary.strip():
            await ctx.send("Aucun message trouvé.")
            return
        await ctx.send(f"**Aperçu des {n} derniers messages :**\n" + summary[:1900] + ("\n[...] (tronqué)" if len(summary) > 1900 else ""))

# ============================================================
# 3) Cog : CanauxCog (stockage via #bot-storage)
# ============================================================
class CanauxCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._loaded = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._loaded:
            return
        try:
            await ensure_storage_loaded(self.bot)
            self._loaded = True
        except Exception as e:
            print("[CanauxCog] ensure_storage_loaded a échoué :", e)

    @commands.command(name="affiche", help="Affiche les listes des canaux importants et exclus (ex: !affiche important).")
    async def affiche_cmd(self, ctx, target: str):
        target = target.lower()
        if target == "important":
            await ctx.send(f"Canaux importants : {self.bot.important_channels}")
        elif target == "excluded":
            await ctx.send(f"Canaux exclus : {self.bot.excluded_channels}")
        else:
            await ctx.send("Usage : `!affiche important` ou `!affiche excluded`")

    @commands.command(name="add_important", help="Ajoute un canal (nom) aux canaux importants.")
    async def add_important_cmd(self, ctx, channel_name: str):
        await ensure_storage_loaded(self.bot)
        imp = set(self.bot.important_channels)
        if channel_name in imp:
            await ctx.send(f"'{channel_name}' est déjà dans les importants.")
            return
        imp.add(channel_name)
        await save_list_to_store(self.bot, "important", list(imp))
        await ctx.send(f"✅ Ajouté à importants : **{channel_name}**\n→ {self.bot.important_channels}")

    @commands.command(name="remove_important", help="Retire un canal (nom) des canaux importants.")
    async def remove_important_cmd(self, ctx, channel_name: str):
        await ensure_storage_loaded(self.bot)
        imp = set(self.bot.important_channels)
        if channel_name not in imp:
            await ctx.send(f"'{channel_name}' n'est pas dans les importants.")
            return
        imp.remove(channel_name)
        await save_list_to_store(self.bot, "important", list(imp))
        await ctx.send(f"🗑️ Retiré des importants : **{channel_name}**\n→ {self.bot.important_channels}")

    @commands.command(name="add_excluded", help="Ajoute un canal (nom) aux canaux exclus.")
    async def add_excluded_cmd(self, ctx, channel_name: str):
        await ensure_storage_loaded(self.bot)
        exc = set(self.bot.excluded_channels)
        if channel_name in exc:
            await ctx.send(f"'{channel_name}' est déjà dans les exclus.")
            return
        exc.add(channel_name)
        await save_list_to_store(self.bot, "excluded", list(exc))
        await ctx.send(f"✅ Ajouté aux exclus : **{channel_name}**\n→ {self.bot.excluded_channels}")

    @commands.command(name="remove_excluded", help="Retire un canal (nom) des canaux exclus.")
    async def remove_excluded_cmd(self, ctx, channel_name: str):
        await ensure_storage_loaded(self.bot)
        exc = set(self.bot.excluded_channels)
        if channel_name not in exc:
            await ctx.send(f"'{channel_name}' n'est pas dans les exclus.")
            return
        exc.remove(channel_name)
        await save_list_to_store(self.bot, "excluded", list(exc))
        await ctx.send(f"🗑️ Retiré des exclus : **{channel_name}**\n→ {self.bot.excluded_channels}")

# ============================================================
# 4) Cog : Debug & Help
# ============================================================
class DebugCog(commands.Cog):
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
            await ctx.send(summary[:1900] + ("..." if len(summary) > 1900 else ""))
        else:
            await ctx.send("Aucun message dans les 10 derniers.")

    @commands.command(name="test_72h", help="Affiche les messages depuis 72h")
    async def test_72h_cmd(self, ctx):
        recent  = get_messages_last_72h(self.bot.messages_by_channel)
        summary = format_messages_for_email(recent)
        if summary.strip():
            await ctx.send(summary[:1900] + ("..." if len(summary) > 1900 else ""))
        else:
            await ctx.send("Aucun message ces dernières 72h.")

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

@commands.command(name="help2", help="Aide avec menu interactif.")
async def help2_cmd(ctx):
    bot  = ctx.bot
    cogs = bot.cogs
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

    view = HelpView(cogs_with_embeds)
    embed_init = discord.Embed(
        title="Aide interactive",
        description="Sélectionnez un cog ci-dessous pour voir ses commandes.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed_init, view=view)

# ============================================================
# 5) setup() — ajoute tous les cogs
# ============================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(EmailCog(bot))
    await bot.add_cog(MessagesCog(bot))
    await bot.add_cog(CanauxCog(bot))
    await bot.add_cog(DebugCog(bot))
    bot.add_command(help2_cmd)
    print("[SETUP] Cogs chargés avec succès.")
    return bot
# Fin de bot/discord_bot_commands.py
