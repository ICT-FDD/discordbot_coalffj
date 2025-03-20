# bot/summarizer.py

"""
Description: Fournit des fonctions pour résumer du texte (tronquer, extraire les premières phrases, etc.).
Uses: Module 're' pour séparer les phrases
Args: (selon la fonction)  ||  Returns: (texte résumé)
---
Author: baudoux.sebastien@gmail.com  | Version: 1.0 | 09/02/2025
"""

import re
from datetime import datetime, timedelta
import locale

def format_messages_by_day(messages_dict):
    """
    Formate les messages en les regroupant par jour (timestamp),
    puis par catégorie ("important"/"general"), puis par canal.
    Retourne une chaîne de caractères type :
        Jeudi 5 janvier 2025
          Canaux importants
            reunions-mensuelles
              17:25 - username : message...
            ...
          Canaux généraux
            ...
    """
    # (Optionnel) Si tu veux des noms de jours/mois en français :
    locale.setlocale(locale.LC_TIME, "fr_FR.utf8")
    # 1) Construire une structure day_dict[YYYY-MM-DD][category][channel] = [msg, ...]
    day_dict = {}
    # On parcourt "important" puis "general"
    for category in ["important", "general"]:
        if category not in messages_dict:
            continue
        for channel, msg_list in messages_dict[category].items():
            for msg in msg_list:
                ts = msg.get("timestamp")
                # Si pas de timestamp, on skip
                if not ts:
                    continue
                # Extraire la partie "jour" (au format YYYY-MM-DD)
                day_str = ts.strftime("%Y-%m-%d")
                # Initialiser la structure si besoin
                if day_str not in day_dict:
                    day_dict[day_str] = {"important": {}, "general": {}}
                if channel not in day_dict[day_str][category]:
                    day_dict[day_str][category][channel] = []
                day_dict[day_str][category][channel].append(msg)
    # 2) Construire le texte final
    lines = []
    # Trier les jours pour avoir un ordre chronologique (du plus ancien au plus récent)
    sorted_days = sorted(day_dict.keys())
    for day_str in sorted_days:
        # Transformer day_str "2025-01-05" en "Jeudi 05 janvier 2025", par ex
        # => On retransforme en datetime
        day_dt = datetime.strptime(day_str, "%Y-%m-%d")
        # Ex : day_formatted = day_dt.strftime("%A %d %B %Y")
        # => "Thursday 05 January 2025" (en anglais) Si localisé fr_FR, possible => "jeudi 05 janvier 2025"
        day_formatted = day_dt.strftime("%A %d %B %Y")
        lines.append(f"{day_formatted}\n")  # Titre du jour
        # -- Canaux importants --
        important_channels = day_dict[day_str]["important"]
        if important_channels:
            lines.append("  Canaux importants\n")
            # On parcourt chaque canal
            for channel, msgs in important_channels.items():
                lines.append(f"    {channel}\n")
                # On trie les messages dans l'ordre chrono
                msgs_sorted = sorted(msgs, key=lambda m: m["timestamp"])
                for m in msgs_sorted:
                    time_str = m["timestamp"].strftime("%H:%M")
                    author = m["author"]
                    content = m["content"]
                    lines.append(f"      {time_str} - {author} : {content}\n")
            lines.append("")
        # -- Canaux généraux --
        general_channels = day_dict[day_str]["general"]
        if general_channels:
            lines.append("  Canaux généraux\n")
            for channel, msgs in general_channels.items():
                lines.append(f"    {channel}\n")
                msgs_sorted = sorted(msgs, key=lambda m: m["timestamp"])
                for m in msgs_sorted:
                    time_str = m["timestamp"].strftime("%H:%M")
                    author = m["author"]
                    content = m["content"]
                    lines.append(f"      {time_str} - {author} : {content}\n")
            lines.append("")
    # 3) Combiner tout
    final_text = "".join(lines)
    if not final_text.strip():
        final_text = "Aucun message à afficher."
    return final_text

def get_messages_last_24h(messages_dict):
    """
    Retourne un nouveau dictionnaire ne contenant
    que les messages postés ces 24 dernières heures.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)

    filtered = {
        "important": {},
        "general": {}
    }

    for category in ["important", "general"]:
        for channel, msg_list in messages_dict[category].items():
            # Conserver seulement ceux dont le timestamp >= cutoff
            recent_msgs = []
            for msg in msg_list:
                if msg["timestamp"] >= cutoff:
                    recent_msgs.append(msg)
            if recent_msgs:
                filtered[category][channel] = recent_msgs

    return filtered

def get_messages_last_72h(messages_dict):
    """
    Retourne un nouveau dictionnaire ne contenant 
    que les messages postés ces 24 dernières heures.
    """
    cutoff = datetime.utcnow() - timedelta(hours=72)

    filtered = {
        "important": {},
        "general": {}
    }

    for category in ["important", "general"]:
        for channel, msg_list in messages_dict[category].items():
            # Conserver seulement ceux dont le timestamp >= cutoff
            recent_msgs = []
            for msg in msg_list:
                if msg["timestamp"] >= cutoff:
                    recent_msgs.append(msg)
            if recent_msgs:
                filtered[category][channel] = recent_msgs

    return filtered

def get_last_n_messages(messages_dict, n=10):
    """
    Retourne un nouveau dictionnaire ne contenant 
    que les 'n' derniers messages de chaque canal.
    Hypothèse : la liste de messages est déjà ordonnée 
                du plus ancien au plus récent.
    """
    filtered = {
        "important": {},
        "general": {}
    }

    for category in ["important", "general"]:
        for channel, msg_list in messages_dict[category].items():
            if msg_list:
                # On prend les 'n' derniers
                last_msgs = msg_list[-n:]
                filtered[category][channel] = last_msgs

    return filtered

def naive_summarize(text, max_sentences=3, max_length=250):
    """
    Découpe (naïvement) le texte en phrases et en extrait jusqu'à max_sentences.
    Tronque le résultat si ça dépasse max_length.
    """
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return text  # Pas de phrase, on renvoie tel quel
    # Ici on ne prend que les premières phrases (façon "extrait") :
    extracted = ". ".join(sentences[:max_sentences])
    # On ajoute un point si on a coupé le texte
    if len(sentences) > max_sentences:
        extracted += "."
    # Tronquage si le texte est trop long
    if len(extracted) > max_length:
        extracted = extracted[:max_length] + " [...]"
    # Indication qu’on a fait un résumé
    if len(sentences) > max_sentences:
        extracted += " (résumé...)"
    return extracted
