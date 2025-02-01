


@bot.command(name="preview_mail")
async def preview_mail(ctx):
    """
    Commande: !preview_mail
    Affiche dans Discord le rapport qui SERA envoyé par e-mail.
    """
    summary = format_messages_for_email(messages_by_channel)
    # Pour éviter de spam un message trop long, on peut couper après X caractères
    if len(summary) > 1900:
        preview_text = summary[:1900] + "\n[...tronqué...]"
    else:
        preview_text = summary

    if not preview_text.strip():
        preview_text = "*Aucun message enregistré.*"

    await ctx.send(f"**Aperçu du mail :**\n{preview_text}")

@bot.command(name="send_daily_summary")
async def send_daily_summary(ctx):
    """
    Commande manuelle: !send_daily_summary 
    Force l'envoi du résumé par mail et vide les messages enregistrés.
    """
    summary = format_messages_for_email(messages_by_channel)
    send_email(summary)

    # Log du nombre de messages
    total_important = sum(len(msgs) for msgs in messages_by_channel["important"].values())
    total_general = sum(len(msgs) for msgs in messages_by_channel["general"].values())

    # On envoie une confirmation dans le salon
    await ctx.send(f"Envoi du résumé terminé.\n"
                   f"{total_important} messages importants, "
                   f"{total_general} messages généraux.")

    # Reset
    messages_by_channel["important"].clear()
    messages_by_channel["general"].clear()
