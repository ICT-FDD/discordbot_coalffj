
import os
import json
from datetime import datetime
from discord.ext import commands

def reset_messages(bot: commands.Bot):
    bot.messages_by_channel["important"].clear()
    bot.messages_by_channel["general"].clear()

def generate_report_filename():
    now = datetime.now()
    # ex. "rapport_2025.02.24_20h45.json"
    return now.strftime("rapport_%Y.%m.%d_%Hh%M.json")

def save_messages_to_file(messages_dict):
    """
    Sauvegarde le contenu de messages_dict dans un fichier JSON,
    avec une en-tête comportant date min, date max, nb de messages...
    """
    all_timestamps = []
    total_msgs = 0

    for category, channels_map in messages_dict.items():
        for channel_name, msgs in channels_map.items():
            for msg in msgs:
                total_msgs += 1
                all_timestamps.append(msg["timestamp"])

    if all_timestamps:
        oldest = min(all_timestamps)
        newest = max(all_timestamps)
    else:
        oldest = None
        newest = None
    # Vous pouvez stocker ces meta-infos dans un petit dict
    metadata = {
        "oldest_message": oldest.isoformat() if oldest else None,
        "newest_message": newest.isoformat() if newest else None,
        "total_messages": total_msgs,
        "generated_at": datetime.now().isoformat()
    }
    data_to_save = {
        "metadata": metadata,
        "messages": messages_dict,  # tout le contenu
    }
    filename = generate_report_filename()
    full_path = os.path.join("rapports", filename)
    # On sérialise en JSON (en convertissant datetime en string)
    def custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, default=custom_serializer, indent=2)

    print(f"[SAVE] Fichier {filename} sauvegardé (nb_msgs={total_msgs}).")
