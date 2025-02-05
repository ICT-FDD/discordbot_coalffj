

# --- Commandes Discord ---


@bot.command(name="list_messages")
async def list_messages(ctx):
    """
    Commande: !list_messages
    Affiche (dans Discord) la liste de tous les messages collectés, 
    regroupés par canal.
    """
    if not messages_by_channel["important"] and not messages_by_channel["general"]:
        await ctx.send("*Aucun message n'a été enregistré pour l'instant.*")
        return

    result = "**Messages en mémoire**\n\n"

    # Canaux importants
    if messages_by_channel["important"]:
        result += "__Canaux importants__:\n"
        for channel, msgs in messages_by_channel["important"].items():
            result += f"**#{channel}**:\n"
            for author, content in msgs:
                result += f"- {author} : {content}\n"
            result += "\n"

    # Canaux généraux
    if messages_by_channel["general"]:
        result += "__Canaux généraux__:\n"
        for channel, msgs in messages_by_channel["general"].items():
            result += f"**#{channel}**:\n"
            for author, content in msgs:
                result += f"- {author} : {content}\n"
            result += "\n"

    # Discord limite la longueur d'un message à ~2000 caractères
    if len(result) > 2000:
        await ctx.send(result[:1900] + "\n[...] (trop long)")
    else:
        await ctx.send(result)



# ---   CHANNELS MANAGMENT   ---- 

@bot.command(name="add_important")
async def add_important(ctx, channel_name: str):
    """
    Commande: !add_important <nom_de_canal>
    Ajoute ce canal à la liste "important_channels".
    """
    if channel_name in important_channels:
        await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux importants.")
        return

    important_channels.append(channel_name)
    save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
    await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux importants.")

@bot.command(name="remove_important")
async def remove_important(ctx, channel_name: str):
    """
    Commande: !remove_important <nom_de_canal>
    Retire ce canal de la liste "important_channels".
    """
    if channel_name not in important_channels:
        await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux importants.")
        return

    important_channels.remove(channel_name)
    save_channels(IMPORTANT_CHANNELS_FILE, important_channels)
    await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux importants.")

@bot.command(name="add_excluded")
async def add_excluded(ctx, channel_name: str):
    """
    Commande: !add_excluded <nom_de_canal>
    Ajoute ce canal à la liste "excluded_channels".
    """
    if channel_name in excluded_channels:
        await ctx.send(f"Le canal '{channel_name}' est déjà dans la liste des canaux exclus.")
        return

    excluded_channels.append(channel_name)
    save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
    await ctx.send(f"Canal '{channel_name}' ajouté à la liste des canaux exclus.")

@bot.command(name="remove_excluded")
async def remove_excluded(ctx, channel_name: str):
    """
    Commande: !remove_excluded <nom_de_canal>
    Retire ce canal de la liste "excluded_channels".
    """
    if channel_name not in excluded_channels:
        await ctx.send(f"Le canal '{channel_name}' n'est pas dans la liste des canaux exclus.")
        return

    excluded_channels.remove(channel_name)
    save_channels(EXCLUDED_CHANNELS_FILE, excluded_channels)
    await ctx.send(f"Canal '{channel_name}' retiré de la liste des canaux exclus.")