import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
from discord.ext import commands, tasks
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Liste des canaux importants (nom exact des canaux Discord)
IMPORTANT_CHANNELS = ["canalprojet1", "canalrendezvous"]

# Configuration du bot Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Indispensable pour avoir le contenu du message
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionnaire pour stocker les messages
messages_by_channel = {"important": {}, "general": {}}

# Fonction pour résumer les messages longs (pour les canaux non importants)
def summarize_message(message):
    max_length = 200  # Longueur maximale avant de résumer
    if len(message) > max_length:
        return message[:max_length] + " [...]"  # Résumé avec une coupure
    return message

# Fonction pour formater les messages pour l'e-mail
def format_messages_for_email(messages_by_channel):
    email_body = ""

    # Ajouter les messages des canaux importants
    if messages_by_channel["important"]:
        email_body += "### Canaux importants\n\n"
        for channel, messages_list in messages_by_channel["important"].items():
            email_body += f"## {channel}\n\n"
            for author, content in messages_list:
                email_body += f"**{author} a écrit :**\n{content}\n\n"

    # Ajouter les messages des autres canaux (résumés)
    if messages_by_channel["general"]:
        email_body += "### Autres canaux\n\n"
        for channel, messages_list in messages_by_channel["general"].items():
            email_body += f"## {channel}\n\n"
            for author, content in messages_list:
                summary = summarize_message(content)
                email_body += f"**{author} a écrit :**\n{summary}\n\n"

    return email_body

# Fonction pour envoyer l'e-mail
def send_email(summary):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = "Résumé quotidien des messages Discord"

        msg.attach(MIMEText(summary, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
            print("E-mail envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")

# Tâche quotidienne pour envoyer le résumé (à 23h UTC)
@tasks.loop(hours=24)
async def daily_summary():
    now = datetime.now()
    if now.hour == 23:
        summary = format_messages_for_email(messages_by_channel)
        send_email(summary)
        messages_by_channel["important"].clear()  # Réinitialiser les messages après envoi
        messages_by_channel["general"].clear()

# Commande manuelle pour forcer l'envoi du résumé
@bot.command(name="send_daily_summary")
async def send_daily_summary(ctx):
    """Commande manuelle: !send_daily_summary 
       - Force l'envoi du résumé par mail et vide la liste."""
    summary = format_messages_for_email(messages_by_channel)

    total_important = sum(len(msgs) for msgs in messages_by_channel["important"].values())
    total_general = sum(len(msgs) for msgs in messages_by_channel["general"].values())

    await ctx.send(f"**Envoi du résumé** : {total_important} messages importants, {total_general} messages généraux.")

    send_email(summary)

    # On réinitialise les stocks de messages
    messages_by_channel["important"].clear()
    messages_by_channel["general"].clear()
    await ctx.send("Résumé envoyé et messages réinitialisés.")

# Événement déclenché au démarrage du bot
@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")
    daily_summary.start()

# Surveiller tous les nouveaux messages
@bot.event
async def on_message(message):
    # Éviter de traiter les messages du bot lui-même
    if message.author == bot.user:
        return

    channel_name = str(message.channel)

    # Canaux importants
    if channel_name in IMPORTANT_CHANNELS:
        if channel_name not in messages_by_channel["important"]:
            messages_by_channel["important"][channel_name] = []
        messages_by_channel["important"][channel_name].append((message.author.name, message.content))
    else:
        # Canaux généraux (à résumer)
        if channel_name not in messages_by_channel["general"]:
            messages_by_channel["general"][channel_name] = []
        messages_by_channel["general"][channel_name].append((message.author.name, message.content))

    # Nécessaire pour que d'autres commandes (ex: !send_daily_summary) puissent être interceptées
    await bot.process_commands(message)

# Lancer le bot
bot.run(DISCORD_TOKEN)
