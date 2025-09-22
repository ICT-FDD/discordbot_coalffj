# bot/mails_management.py
"""
Description:
    - Construit un corps d’e-mail lisible à partir des messages collectés
      (groupé par JOUR → Canaux importants → Autres canaux), avec filtrage du bruit.
    - Envoie l’e-mail en SMTP de manière asynchrone.

Entrées:
    - format_messages_for_email(messages_dict, ...)
      messages_dict attendu:
      {
        "important": { "nom_canal": [ {author, content, timestamp: datetime}, ... ], ... },
        "general":   { "nom_canal": [ ... ] }
      }

    - send_email(body, from_addr, password, to_addr, *, host=None, port=None, timeout=None, subject=None)

Dépendances internes:
    - bot.summarizer.naive_summarize (pour condenser les canaux généraux)
"""

from __future__ import annotations

import re
import asyncio
import smtplib
from collections import defaultdict
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import zoneinfo

from bot.summarizer import naive_summarize

# ---------- Config par défaut ----------

DEFAULT_TZ = "Europe/Brussels"

# Par défaut on reste cohérent avec l’ancien paramétrage OVH (modifie si besoin)
DEFAULT_SMTP_HOST = "ssl0.ovh.net"
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_TIMEOUT = 30.0

# ---------- Nettoyage / filtrage ----------

# Emojis Unicode communs (approximation suffisante ici)
_EMOJI_RE = re.compile(r"^(?:[\U0001F000-\U0001FAFF\U00002700-\U000027BF\U00002600-\U000026FF]+)$")
_URL_RE = re.compile(r"https?://\S+")
_WS_RE = re.compile(r"\s+")
# Messages ultra-courts type "ok", "merci", "👍" qu’on souhaite ignorer
_SHORT_OK_RE = re.compile(r"^(ok|okay|thx|merci|thanks|\+1)$", re.IGNORECASE)

def _clean_text(s: str) -> str:
    """Trim + supprime les liens nus + compacte les espaces."""
    if not s:
        return ""
    s = s.strip()
    s = _URL_RE.sub("", s)     # on supprime les liens nus
    s = _WS_RE.sub(" ", s)     # on compacte
    return s.strip()

def _is_noise(s: str) -> bool:
    """Filtre le bruit: vide, trop court, emoji seul, 'ok/merci' etc., ou vide après nettoyage."""
    if not s:
        return True
    if _EMOJI_RE.match(s):
        return True
    if _SHORT_OK_RE.match(s):
        return True
    if len(s) < 4:
        return True
    if not _clean_text(s):
        return True
    return False

def _to_local(ts: datetime, tz_name: str) -> datetime:
    """Convertit un datetime en timezone locale (défaut: Europe/Brussels)."""
    try:
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        tz = zoneinfo.ZoneInfo(DEFAULT_TZ)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(tz)

def _dedupe_consecutive(msgs: list[dict]) -> list[dict]:
    """Retire les doublons consécutifs exacts (même auteur ET même contenu)."""
    out = []
    last_key = None
    for m in msgs:
        key = (m.get("author"), m.get("content"))
        if key == last_key:
            continue
        out.append(m)
        last_key = key
    return out

def _summarize_channel_paragraph(msgs: list[dict], max_chars: int = 500) -> str:
    """
    Construit un paragraphe condensé pour un canal "général".
    On concatène "Auteur: message", puis on applique naive_summarize.
    """
    parts = []
    for m in msgs:
        a = m.get("author", "???")
        c = _clean_text(m.get("content", ""))
        if _is_noise(c):
            continue
        parts.append(f"{a}: {c}")
    if not parts:
        return "— (aucun élément pertinent)"
    blob = " • ".join(parts)
    return naive_summarize(blob, max_sentences=3, max_length=max_chars)

# ---------- Construction du corps d’e-mail ----------

def format_messages_for_email(
    messages_dict: dict,
    *,
    tz_name: str = DEFAULT_TZ,
    max_items_important_per_channel: int = 8,
    summarize_general: bool = True,
    max_items_general_per_channel: int = 8,
) -> str:
    """
    Construit un texte propre:
      - Groupé par JOUR local
      - Canaux __importants__ : liste horodatée (HH:MM — Auteur : msg), limite par canal
      - __Autres canaux__ : paragraphe résumé (ou liste compacte si summarize_general=False)
      - Filtrage: liens nus, emojis seuls, “ok/merci”, messages < 4 chars, doublons consécutifs
    """
    # Collecte pour l'entête (période couverte / compteur brut)
    all_ts: list[datetime] = []
    total_before = 0
    for cat in ("important", "general"):
        for _ch, lst in messages_dict.get(cat, {}).items():
            total_before += len(lst)
            for m in lst:
                ts = m.get("timestamp")
                if isinstance(ts, datetime):
                    all_ts.append(ts)

    date_span = ""
    if all_ts:
        tz = zoneinfo.ZoneInfo(tz_name)
        lo = _to_local(min(all_ts), tz_name)
        hi = _to_local(max(all_ts), tz_name)
        date_span = f"{lo.strftime('%d/%m/%Y %H:%M')} → {hi.strftime('%d/%m/%Y %H:%M')} ({tz.key})"

    # Groupage par jour local
    by_day: dict[str, dict[str, dict[str, list[dict]]]] = defaultdict(
        lambda: {"important": defaultdict(list), "general": defaultdict(list)}
    )

    for cat in ("important", "general"):
        for ch, lst in messages_dict.get(cat, {}).items():
            # nettoyage + dédoublonnage
            cleaned: list[dict] = []
            for m in lst:
                c = _clean_text(m.get("content", ""))
                if _is_noise(c):
                    continue
                mm = dict(m)
                mm["content"] = c
                cleaned.append(mm)
            cleaned = _dedupe_consecutive(cleaned)

            for m in cleaned:
                ts = m.get("timestamp")
                if not isinstance(ts, datetime):
                    continue
                local = _to_local(ts, tz_name)
                key = local.strftime("%Y-%m-%d")
                m2 = dict(m)
                m2["_local_ts"] = local
                by_day[key][cat][ch].append(m2)

    # Construction texte
    lines: list[str] = []
    header_title = "Rapport quotidien – Discord Coalition FFJ"
    lines.append(f"**{header_title}**\n")
    if date_span:
        lines.append(f"_Période couverte_ : {date_span}\n")
    lines.append(f"_Messages collectés (avant filtrage)_ : {total_before}\n\n")

    for day_key in sorted(by_day.keys()):
        day_dt = datetime.strptime(day_key, "%Y-%m-%d")
        # ex: ### Lundi 22 Septembre 2025
        lines.append(day_dt.strftime("### %A %d %B %Y").capitalize() + "\n")

        # ---- Canaux importants ----
        imp = by_day[day_key]["important"]
        if imp:
            lines.append("__Canaux importants__\n")
            for ch, msgs in imp.items():
                msgs_sorted = sorted(msgs, key=lambda m: m["_local_ts"])[-max_items_important_per_channel:]
                lines.append(f"**#{ch}**\n")
                for m in msgs_sorted:
                    t = m["_local_ts"].strftime("%H:%M")
                    a = m.get("author", "???")
                    c = m.get("content", "")
                    if len(c) > 240:
                        c = c[:240] + " […]"
                    lines.append(f"- {t} — **{a}** : {c}")
                lines.append("")

        # ---- Autres canaux ----
        gen = by_day[day_key]["general"]
        if gen:
            lines.append("__Autres canaux__\n")
            for ch, msgs in gen.items():
                msgs_sorted = sorted(msgs, key=lambda m: m["_local_ts"])[-max_items_general_per_channel:]
                lines.append(f"**#{ch}**")
                if summarize_general:
                    para = _summarize_channel_paragraph(msgs_sorted, max_chars=450)
                    lines.append(para + "\n")
                else:
                    for m in msgs_sorted:
                        t = m["_local_ts"].strftime("%H:%M")
                        a = m.get("author", "???")
                        c = m.get("content", "")
                        if len(c) > 200:
                            c = c[:200] + " […]"
                        lines.append(f"- {t} — {a}: {c}")
                    lines.append("")
        lines.append("")  # espace entre jours

    body = "\n".join(lines).strip()
    if not body:
        body = "**Rapport quotidien – Discord Coalition FFJ**\n(Aucun contenu pertinent pour cette période.)"
    return body

# ---------- Envoi d’e-mail (async, SMTP) ----------

def _send_email_sync(
    body: str,
    from_addr: str,
    password: str,
    to_addr: str,
    *,
    host: str,
    port: int,
    timeout: float | None,
    subject: str | None = None,
) -> None:
    """Envoie un e-mail texte (UTF-8) en SMTP de manière synchrone."""
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject or "Rapport quotidien – Discord Coalition FFJ"
    msg.attach(MIMEText(body, "plain", _charset="utf-8"))

    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = timeout

    with smtplib.SMTP(host, port, **kwargs) as server:
        server.starttls()
        server.login(from_addr, password)
        server.sendmail(from_addr, to_addr, msg.as_string())

async def send_email(
    body: str,
    from_addr: str,
    password: str,
    to_addr: str,
    *,
    host: str | None = None,
    port: int | None = None,
    timeout: float | None = None,
    subject: str | None = None,
) -> None:
    """
    Enveloppe asynchrone autour de _send_email_sync.
    - Valeurs par défaut SMTP: OVH (ssl0.ovh.net:587, 30s)
    - Sujet par défaut: "[Coalition FFJ] Rapport Discord — JJ/MM/AAAA" (Europe/Brussels)
    """
    resolved_host = host or DEFAULT_SMTP_HOST
    resolved_port = DEFAULT_SMTP_PORT if port is None else port
    resolved_timeout = DEFAULT_SMTP_TIMEOUT if timeout is None else timeout

    if subject is None:
        tz = zoneinfo.ZoneInfo(DEFAULT_TZ)
        today = datetime.now(tz).strftime("%d/%m/%Y")
        subject = f"[Coalition FFJ] Rapport Discord — {today}"

    await asyncio.to_thread(
        _send_email_sync,
        body,
        from_addr,
        password,
        to_addr,
        host=resolved_host,
        port=resolved_port,
        timeout=resolved_timeout,
        subject=subject,
    )
