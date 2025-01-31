import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
from discord.ext import commands, tasks
from datetime import datetime
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Vérification simple au démarrage (juste en console)
if not DISCORD_TOKEN:
    print("[WARN] DISCORD_TOKEN est vide ou non défini.")
if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    print("[WARN] Informations de connexion email incomplètes.")
if not RECIPIENT_EMAIL:
    print("[WARN] RECIPIENT_EMAIL est vide ou non défini.")

# Liste des canaux importants (nom exact des canaux Discord)
IMPORTANT_CHANNELS = ["canalprojet1", "canalrendezvous"]

# Configuration du bot Discord
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Indispensable pour lire le contenu
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionnaire pour stocker les messages
messages_by_channel = {"important": {}, "general": {}}

# --------------------------------------------------
# Fonctions utilitaires
# --------------------------------------------------

def summarize_message(message: str, max_length=200) -> str:
    """Si le message dépasse max_length caractères, on le tronque."""
    if len(message) > max_length:
        return message[:max_length] + " [...]"
    return message

def format_messages_for_email(messages_by_channel: dict) -> str:
    """Construit le texte du rapport à partir des messages collectés."""
    email_body = ""

    # Canaux importants
    if messages_by_channel["important"]:
        email_body += "### Canaux importants\n\n"
        for channel, messages in messages_by_channel["important"].items():
            email_body += f"## {channel}\n\n"
            for author, content in messages:
                email_body += f"**{author} a écrit :**\n{content}\n\n"

    # Autres canaux (résumés)
    if messages_by_channel["general"]:
        email_body += "### Autres canaux\n\n"
        for channel, messages in messages_by_channel["general"].items():
            email_body += f"## {channel}\n\n"
            for author, content in messages:
                summary = summarize_message(content)
                email_body += f"**{author} a écrit :**\n{summary}\n\n"

    return email_body

def send_email(summary: str):
    """Envoie l'email à l'adresse RECIPIENT_EMAIL."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("[ERROR] Impossible d'envoyer l'email : identifiants SMTP manquants.")
        return
    if not RECIPIENT_EMAIL:
        print("[ERROR] Impossible d'envoyer l'email : RECIPIENT_EMAIL manquant.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = "Résumé quotidien des messages Discord"

        # Corps du mail en texte brut
        msg.attach(MIMEText(summary, "plain"))

        print("[INFO] Envoi de l'email en cours...")

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        
        print("[INFO] E-mail envoyé avec succès !")

    except Exception as e:
        print(f"[ERROR] Erreur lors de l'envoi de l'e-mail : {e}")

# --------------------------------------------------
# Tâche quotidienne (loop) pour envoyer le résumé
# --------------------------------------------------
@tasks.loop(hours=24)
async def daily_summary():
    """Tâche programmée toutes les 24h. 
       Envoie le résumé quand l'heure est 23h (UTC ou locale selon l'hébergeur)."""
    now = datetime.now()
    if now.hour == 23:
        print("[INFO] daily_summary déclenché à 23h. Préparation de l'e-mail...")
        summary = format_messages_for_email(messages_by_channel)

        # Petit log pour voir combien de messages on a récolté
        total_important = sum(len(msgs) for msgs in messages_by_channel["important"].values())
        total_general = sum(len(msgs) for msgs in messages_by_channel["general"].values())
        print(f"[INFO] Nombre de messages importants: {total_important}, "
              f"généraux: {total_general}")

        # Envoi de l'e-mail
        send_email(summary)

        # Réinitialiser les messages après envoi
        messages_by_channel["important"].clear()
        messages_by_channel["general"].clear()
        print("[INFO] Les messages ont été réinitialisés après l'envoi.")

# --------------------------------------------------
# Événements et commandes du bot
# --------------------------------------------------
@bot.event
async def on_ready():
    print(f"[INFO] Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    # On démarre la loop quotidienne
    daily_summary.start()

@bot.event
async def on_message(message):
    # Ignorer les messages du bot lui-même pour éviter les boucles
    if message.author == bot.user:
        return

    channel_name = str(message.channel.name)  # .name = le nom du salon

    # Log pour contrôle (optionnel, attention au spam si canal très actif)
    print(f"[DEBUG] Nouveau message dans #{channel_name} par {message.author.name} : {message.content}")

    # Traiter les messages des canaux importants
    if channel_name in IMPORTANT_CHANNELS:
        if channel_name not in messages_by_channel["important"]:
            messages_by_channel["important"][channel_name] = []
        messages_by_channel["important"][channel_name].append((message.author.name, message.content))
    else:
        # Traiter les autres canaux (à résumer)
        if channel_name not in messages_by_channel["general"]:
            messages_by_channel["general"][channel_name] = []
        messages_by_channel["general"][channel_name].append((message.author.name, message.content))

    # Nécessaire pour que les autres commandes (ex: !test) fonctionnent
    await bot.process_commands(message)

# --------------------------------------------------
# Commande manuelle pour tester l'envoi du résumé
# --------------------------------------------------
@bot.command(name="send_daily_summary")
async def send_daily_summary(ctx):
    """Commande manuelle: !send_daily_summary 
       - Force l'envoi du résumé par mail et vide la liste."""
    summary = format_messages_for_email(messages_by_channel)

    total_important = sum(len(msgs) for msgs in messages_by_channel["important"].values())
    total_general = sum(len(msgs) for msgs_by_channel in messages_by_channel["general"].values())
    await ctx.send(f"**Envoi du résumé** : {total_important} messages importants, "
                   f"{total_general} messages généraux.")
    
    send_email(summary)

    # Reset
    messages_by_channel["important"].clear()
    messages_by_channel["general"].clear()
    await ctx.send("Résumé envoyé et messages réinitialisés.")

# --------------------------------------------------
# Lancer le bot
# --------------------------------------------------
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
