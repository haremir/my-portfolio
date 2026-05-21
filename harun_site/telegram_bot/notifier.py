"""
harun_site/telegram_bot/notifier.py
────────────────────────────────────
All outbound Telegram message logic.

Responsibilities
────────────────
1. Low-level send (fire-and-forget, never raises into caller).
2. Anti-spam guard — cooldown + deduplication persisted to JSON.
3. Hiring / session intent detection (keyword-first, Groq fallback).
4. Watch-list evaluation — notify when a watched project is mentioned.
5. Error alert batching — group repeated errors before sending.

Follows the "extend, don't replace" rule:
  • reads logs via data_manager helpers
  • sends notifications via Telegram Bot API (httpx, already in venv)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

# ── Paths ──────────────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parent.parent.parent
_GUARD_FILE   = _BASE / "data" / "tg_notify_state.json"
_WATCH_FILE   = _BASE / "data" / "tg_watchlist.json"

# ── Cooldown config (seconds) ──────────────────────────────────────────────
_HIRING_COOLDOWN   = int(os.environ.get("HIRING_INTENT_COOLDOWN_MINUTES",  "60"))  * 60
_ERROR_COOLDOWN    = int(os.environ.get("ERROR_ALERT_COOLDOWN_MINUTES",    "10"))  * 60
_DAILY_COOLDOWN    = int(os.environ.get("DAILY_SUMMARY_COOLDOWN_HOURS",    "23"))  * 3600
_WATCH_COOLDOWN    = int(os.environ.get("WATCH_ALERT_COOLDOWN_MINUTES",    "30"))  * 60

# Hiring intent keyword signals (Turkish + English)
_HIRING_KEYWORDS = [
    "çalışmak", "çalışalım", "işbirliği", "iş birliği",
    "collaborate", "collaboration", "hire", "hiring",
    "freelance", "proje teklifi", "danışmanlık", "consulting",
    "fiyat", "ücret", "pricing", "maliyet", "cost",
    "iletişim", "contact", "ulaşabilir miyim", "reach",
    "linkedin", "mail", "email", "github",
    "birlikte", "together", "partner",
]

# Contact-request keywords (triggers weaker signal)
_CONTACT_KEYWORDS = [
    "linkedin", "github", "mail", "email", "iletişim",
    "contact", "nasıl ulaşabilirim", "reach you",
]

# Frustration / confusion signals
_CONFUSION_KEYWORDS = [
    "anlamadım", "anlamıyorum", "ne demek", "açıklar mısın",
    "confused", "unclear", "bilmiyorum", "neden",
]


# ── Atomic write helper ────────────────────────────────────────────────────
def _write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.stem + "_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_guard() -> dict:
    if not _GUARD_FILE.exists():
        return {}
    try:
        return json.loads(_GUARD_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── Watch-list persistence ─────────────────────────────────────────────────
def load_watchlist() -> list[str]:
    """Return list of watched project slugs/names (lowercase)."""
    if not _WATCH_FILE.exists():
        return []
    try:
        return json.loads(_WATCH_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_watchlist(items: list[str]) -> None:
    _write(_WATCH_FILE, [i.lower() for i in items])


def watch_add(project: str) -> bool:
    """Add *project* to watchlist. Returns True if newly added."""
    wl = load_watchlist()
    p = project.lower().strip()
    if p in wl:
        return False
    wl.append(p)
    save_watchlist(wl)
    return True


def watch_remove(project: str) -> bool:
    """Remove *project* from watchlist. Returns True if removed."""
    wl = load_watchlist()
    p = project.lower().strip()
    if p not in wl:
        return False
    save_watchlist([x for x in wl if x != p])
    return True


# ── Anti-spam guard ────────────────────────────────────────────────────────
def _should_send(kind: str, key: str, cooldown_secs: int) -> bool:
    """
    Return True if this notification is allowed (not in cooldown).
    Persist the timestamp on approval.
    """
    guard = _load_guard()
    slot = f"{kind}:{key}"
    last = guard.get(slot, 0)
    now = time.time()
    if now - last < cooldown_secs:
        return False
    guard[slot] = now
    try:
        _write(_GUARD_FILE, guard)
    except Exception:
        pass
    return True


# ── Low-level HTTP sender ──────────────────────────────────────────────────
async def _send_raw(token: str, chat_id: int, text: str) -> bool:
    """
    POST a message to Telegram. Returns True on success.
    Never raises — all errors are logged and swallowed.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    
    # Attach command keyboard to notifications so admin can act on them directly
    try:
        from harun_site.telegram_bot.keyboards import command_keyboard
        payload["reply_markup"] = command_keyboard().to_dict()
    except Exception as e:
        print(f"[NOTIFY] Failed to attach keyboard: {e}", file=sys.stderr)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
        if resp.status_code != 200:
            print(f"[NOTIFY] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return False
        return True
    except Exception as exc:
        print(f"[NOTIFY] Send failed: {exc}", file=sys.stderr)
        return False


def send_notification(text: str) -> None:
    """
    Fire-and-forget notification from sync context (e.g. Reflex event handler).
    Resolves token/chat_id from env at call time so the bot can be
    reconfigured without restart.
    """
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "")
    if not token or not chat_id_str:
        return
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return

    async def _go() -> None:
        await _send_raw(token, chat_id, text)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_go())
        else:
            loop.run_until_complete(_go())
    except Exception as exc:
        print(f"[NOTIFY] Dispatch error: {exc}", file=sys.stderr)


async def send_notification_async(text: str) -> None:
    """Async variant for use inside bot handlers / scheduler."""
    token       = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "")
    if not token or not chat_id_str:
        return
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return
    await _send_raw(token, chat_id, text)


# ── Intent detection ───────────────────────────────────────────────────────
def _text_of(messages: list[dict]) -> str:
    return " ".join(
        m.get("content", "") for m in messages if m.get("role") == "user"
    ).lower()


def _keyword_score(text: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw in text)


def detect_hiring_intent(messages: list[dict]) -> dict[str, Any] | None:
    """
    Returns a signal dict if hiring/collaboration intent is detected, else None.

    Two-stage detection:
      Stage 1 — cheap keyword scan (always runs)
      Stage 2 — confident signal if score >= 2 OR long session with 1 hit
    """
    # Ignore trivially short sessions (greetings, single-exchange)
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if len(user_msgs) < 3:
        return None

    text = _text_of(messages)
    score = _keyword_score(text, _HIRING_KEYWORDS)
    contact_score = _keyword_score(text, _CONTACT_KEYWORDS)

    # Long session (8+ user messages) with any hiring signal = notable
    long_session = len(user_msgs) >= 8

    if score >= 2 or (long_session and score >= 1) or contact_score >= 2:
        # Figure out which project was mentioned most
        from harun_site.utils.data_manager import load_projects
        projects = load_projects()
        top_project = ""
        top_count = 0
        for p in projects:
            name = p.get("name", "").lower()
            slug = p.get("slug", "").lower()
            count = text.count(name) + text.count(slug)
            if count > top_count:
                top_count = count
                top_project = p.get("name", "")

        return {
            "score":       score,
            "contact":     contact_score,
            "msg_count":   len(user_msgs),
            "long_session": long_session,
            "top_project": top_project,
        }
    return None


def detect_watch_mentions(messages: list[dict]) -> list[str]:
    """Return names of watched projects mentioned in *messages*."""
    watchlist = load_watchlist()
    if not watchlist:
        return []
    text = _text_of(messages)
    return [p for p in watchlist if p in text]


# ── Notification formatters ────────────────────────────────────────────────
def fmt_hiring_alert(signal: dict) -> str:
    project_line = f"\n🎯 <b>Proje:</b> {signal['top_project']}" if signal.get("top_project") else ""
    long_flag = " (uzun oturum 🔥)" if signal.get("long_session") else ""
    return (
        f"🚨 <b>İşe Alım / İşbirliği Sinyali</b>{long_flag}\n"
        f"📬 {signal['msg_count']} mesajlık oturum"
        f"{project_line}\n"
        f"💡 Hiring score: {signal['score']} · Contact score: {signal['contact']}"
    )


def fmt_watch_alert(project: str, msg_count: int) -> str:
    return (
        f"👀 <b>Watch Alert:</b> <code>{project}</code> konuşuluyor!\n"
        f"📩 Oturumda {msg_count} mesaj var."
    )


def fmt_error_alert(error: str, context: str = "") -> str:
    short = error[:300].replace("<", "&lt;").replace(">", "&gt;")
    ctx   = f"\n📍 {context}" if context else ""
    return (
        f"⚠️ <b>Uygulama Hatası</b>{ctx}\n"
        f"<code>{short}</code>"
    )


def fmt_long_session_alert(msg_count: int, top_project: str) -> str:
    proj = f" — <b>{top_project}</b>" if top_project else ""
    return (
        f"💬 <b>Uzun Oturum</b>{proj}\n"
        f"Ziyaretçi {msg_count} mesaj gönderdi."
    )


# ── High-level notification triggers ──────────────────────────────────────
def notify_hiring_if_warranted(messages: list[dict]) -> None:
    """Called from ChatState after each AI response is saved."""
    signal = detect_hiring_intent(messages)
    if not signal:
        return
    key = hashlib.md5(
        _text_of(messages).encode()[:200]
    ).hexdigest()[:12]
    if _should_send("hiring", key, _HIRING_COOLDOWN):
        print(f"[NOTIFY] Firing hiring alert (score={signal['score']})", file=sys.stderr)
        send_notification(fmt_hiring_alert(signal))


def notify_watch_if_warranted(messages: list[dict]) -> None:
    """Called from ChatState after each AI response. Fires per watched project."""
    mentioned = detect_watch_mentions(messages)
    if not mentioned:
        return
    msg_count = sum(1 for m in messages if m.get("role") == "user")
    for project in mentioned:
        if _should_send("watch", project, _WATCH_COOLDOWN):
            print(f"[WATCH] Firing watch alert for: {project}", file=sys.stderr)
            send_notification(fmt_watch_alert(project, msg_count))


def notify_error(error: str, context: str = "") -> None:
    """Called from exception handlers. Groups errors by type."""
    key = hashlib.md5(error.encode()[:100]).hexdigest()[:12]
    if _should_send("error", key, _ERROR_COOLDOWN):
        print(f"[NOTIFY] Firing error alert", file=sys.stderr)
        send_notification(fmt_error_alert(error, context))


def notify_long_session(messages: list[dict]) -> None:
    """Fires once per session when message count crosses threshold (12 msgs)."""
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if len(user_msgs) != 12:   # exact threshold crossing
        return
    from harun_site.utils.data_manager import load_projects
    projects = load_projects()
    text = _text_of(messages)
    top_project = ""
    top_count = 0
    for p in projects:
        name = p.get("name", "").lower()
        count = text.count(name)
        if count > top_count:
            top_count = count
            top_project = p.get("name", "")

    # Deduplicate using text hash
    key = hashlib.md5(text.encode()[:300]).hexdigest()[:12]
    if _should_send("long_session", key, _WATCH_COOLDOWN):
        print(f"[NOTIFY] Firing long-session alert ({len(user_msgs)} msgs)", file=sys.stderr)
        send_notification(fmt_long_session_alert(len(user_msgs), top_project))
