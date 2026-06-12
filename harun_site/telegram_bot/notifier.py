# -*- coding: utf-8 -*-
"""
────────────────────────────────────
All outbound Telegram message logic.

Responsibilities
────────────────
1. Low-level send (fire-and-forget, never raises into caller).
2. Anti-spam guard — cooldown + deduplication persisted to JSON.
3. Mute state — suppress non-critical alerts for 1h / 1d / indefinitely.
4. New visitor notification (skips admin self-tests).
5. Hiring / session intent detection (keyword-first, lower thresholds).
6. Watch-list evaluation — notify when a watched project is mentioned.
7. Error alert batching — group repeated errors before sending.

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
import threading
import time
from pathlib import Path
from typing import Any

import httpx

# ── Paths ──────────────────────────────────────────────────────────────────
_HERE       = Path(__file__).resolve().parent.parent  # harun_site/
_BASE       = _HERE.parent                             # project root

# Use the same DATA_DIR logic as data_manager.py
_PKG_DATA = _HERE / "data"
_ROOT_DATA = _BASE / "data"
if _PKG_DATA.exists() and any(_PKG_DATA.iterdir()):
    _DATA_DIR = _PKG_DATA
else:
    _DATA_DIR = _ROOT_DATA

_GUARD_FILE = _DATA_DIR / "tg_notify_state.json"
_WATCH_FILE = _DATA_DIR / "tg_watchlist.json"

# ── Cooldown config (seconds) ──────────────────────────────────────────────
_HIRING_COOLDOWN    = int(os.environ.get("HIRING_INTENT_COOLDOWN_MINUTES",  "60"))  * 60
_ERROR_COOLDOWN     = int(os.environ.get("ERROR_ALERT_COOLDOWN_MINUTES",    "10"))  * 60
_DAILY_COOLDOWN     = int(os.environ.get("DAILY_SUMMARY_COOLDOWN_HOURS",    "23"))  * 3600
_WATCH_COOLDOWN     = int(os.environ.get("WATCH_ALERT_COOLDOWN_MINUTES",    "30"))  * 60
_VISITOR_COOLDOWN   = int(os.environ.get("VISITOR_NOTIFY_COOLDOWN_SECONDS", "5"))

# ── Test-session anti-spam: >5 new sessions in 60s → treat as self-test ───
_TEST_SPAM_WINDOW   = int(os.environ.get("TEST_SPAM_WINDOW_SECONDS",  "60"))
_TEST_SPAM_THRESHOLD = int(os.environ.get("TEST_SPAM_THRESHOLD_COUNT", "5"))   # 3→5: daha toleranslı

# Hiring intent keyword signals (Turkish + English)
_HIRING_KEYWORDS = [
    "çalışmak", "çalışalım", "işbirliği", "iş birliği",
    "collaborate", "collaboration", "hire", "hiring",
    "freelance", "proje teklifi", "danışmanlık", "consulting",
    "fiyat", "ücret", "pricing", "maliyet", "cost",
    "iletişim", "contact", "ulaşabilir miyim", "reach",
    "linkedin", "mail", "email", "github",
    "birlikte", "together", "partner",
    "teklif", "offer", "anlaşma", "deal", "sözleşme", "contract",
]

# Contact-request keywords (triggers weaker signal)
_CONTACT_KEYWORDS = [
    "linkedin", "github", "mail", "email", "iletişim",
    "contact", "nasıl ulaşabilirim", "reach you",
]

# Frustration / confusion signals — KEPT PASSIVE, not used for notifications
# because "CebirX ne demek" is curiosity, not confusion, and there's no
# actionable response we can take either way.
_CONFUSION_KEYWORDS = [
    "anlamadım", "anlamıyorum", "ne demek", "açıklar mısın",
    "confused", "unclear", "bilmiyorum", "neden",
]


# ── Sync wrappers for async API client ────────────────────────────────────
# notifier runs in sync context (Reflex event handler threads), so we need
# to call async api_client methods via a dedicated event loop.

def _run_async(coro):
    """Run an async coroutine synchronously. Safe to call from any thread.

    Strategy:
      1. Try asyncio.run() — cleanest, works when no loop is running.
      2. If a loop is already running (e.g. inside bot handler thread),
         dispatch to a fresh thread to avoid blocking.
    """
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # A running event loop exists in this thread (e.g. Reflex / bot).
        import concurrent.futures
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result(timeout=15)
        except Exception as exc:
            print(f"[NOTIFY] _run_async thread fallback failed: {exc}", file=sys.stderr)
            return None
    except Exception as exc:
        print(f"[NOTIFY] _run_async failed: {exc}", file=sys.stderr)
        return None


def _get_projects_sync() -> list[dict]:
    """Fetch project list from Reflex API synchronously."""
    try:
        from harun_site.telegram_bot.api_client import api_client
        result = _run_async(api_client.get_projects())
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"[NOTIFY] _get_projects_sync failed: {e}", file=sys.stderr)
        return []


def _get_chat_logs_sync() -> list[dict]:
    """Fetch chat logs from Reflex API synchronously."""
    try:
        from harun_site.telegram_bot.api_client import api_client
        result = _run_async(api_client.get_chat_logs())
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"[NOTIFY] _get_chat_logs_sync failed: {e}", file=sys.stderr)
        return []


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


def _save_guard(guard: dict) -> None:
    try:
        _write(_GUARD_FILE, guard)
    except Exception:
        pass


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


# ── Mute state ─────────────────────────────────────────────────────────────
# Stored inside _GUARD_FILE under keys:
#   "muted_until"  : float  — Unix timestamp; 0 = not muted; -1 = muted indefinitely
#   "mute_type"    : str    — "1h", "1d", "forever"

def get_mute_state() -> dict:
    """Return {"muted": bool, "until": float, "type": str}."""
    guard = _load_guard()
    muted_until = guard.get("muted_until", 0)
    mute_type   = guard.get("mute_type", "")
    now = time.time()

    if muted_until == -1:
        return {"muted": True, "until": -1, "type": "forever"}
    if muted_until > 0 and now < muted_until:
        return {"muted": True, "until": muted_until, "type": mute_type}
    # Auto-expired — clean up
    if muted_until > 0 and now >= muted_until:
        guard.pop("muted_until", None)
        guard.pop("mute_type", None)
        _save_guard(guard)
    return {"muted": False, "until": 0, "type": ""}


def is_muted() -> bool:
    return get_mute_state()["muted"]


def set_mute(duration: str) -> float:
    """
    Mute notifications.
    duration: "1h" | "1d" | "forever"
    Returns the muted_until timestamp (-1 for forever).
    """
    guard = _load_guard()
    now = time.time()
    if duration == "1h":
        until = now + 3600
    elif duration == "1d":
        until = now + 86400
    else:  # forever
        until = -1
    guard["muted_until"] = until
    guard["mute_type"]   = duration
    _save_guard(guard)
    return until


def clear_mute() -> None:
    """Remove mute state."""
    guard = _load_guard()
    guard.pop("muted_until", None)
    guard.pop("mute_type", None)
    _save_guard(guard)


# ── New-visitor notification toggle ───────────────────────────────────────
def is_new_visitor_notify_enabled() -> bool:
    guard = _load_guard()
    return guard.get("new_visitor_enabled", True)


def set_new_visitor_notify(enabled: bool) -> None:
    guard = _load_guard()
    guard["new_visitor_enabled"] = enabled
    _save_guard(guard)


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
        _save_guard(guard)
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

    # Attach command keyboard to notifications so admin can act directly
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


async def _send_document_raw(token: str, chat_id: int, filename: str, content: str) -> bool:
    """Send a text file as a Telegram document. Never raises."""
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        file_bytes = content.encode("utf-8")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                data={"chat_id": str(chat_id)},
                files={"document": (filename, file_bytes, "text/plain")},
            )
        if resp.status_code != 200:
            print(f"[NOTIFY] sendDocument HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return False
        return True
    except Exception as exc:
        print(f"[NOTIFY] sendDocument failed: {exc}", file=sys.stderr)
        return False


def _get_creds() -> tuple[str, int] | None:
    token       = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "")
    if not token or not chat_id_str:
        print(
            f"[NOTIFY] ⚠️ TELEGRAM_BOT_TOKEN={'var' if token else 'YOK'} "
            f"TELEGRAM_ADMIN_ID={'var' if chat_id_str else 'YOK'} — bildirim GÖNDERİLEMEZ!",
            file=sys.stderr,
        )
        return None
    try:
        return token, int(chat_id_str)
    except ValueError:
        print(f"[NOTIFY] ⚠️ TELEGRAM_ADMIN_ID geçersiz: '{chat_id_str}'", file=sys.stderr)
        return None


def send_notification(text: str, *, ignore_mute: bool = False) -> None:
    """
    Fire-and-forget notification from sync context (e.g. Reflex event handler).

    Runs in a daemon thread with its own event loop so it never blocks
    Reflex's event loop and never leaks into it.
    ignore_mute=True bypasses mute for critical alerts (errors, daily summary).
    """
    if not ignore_mute and is_muted():
        print("[NOTIFY] Mute aktif — bildirim atlanıyor", file=sys.stderr)
        return

    creds = _get_creds()
    if not creds:
        return
    print(f"[NOTIFY] Gönderiliyor: {text[:100].replace(chr(10),' ')}...", file=sys.stderr)
    token, chat_id = creds

    async def _go() -> None:
        await _send_raw(token, chat_id, text)

    def _worker() -> None:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_go())
        except Exception as exc:
            print(f"[NOTIFY] Thread dispatch error: {exc}", file=sys.stderr)
        finally:
            loop.close()

    threading.Thread(target=_worker, daemon=True).start()


async def send_notification_async(text: str, *, ignore_mute: bool = False) -> None:
    """Async variant for use inside bot handlers / scheduler."""
    if not ignore_mute and is_muted():
        return
    creds = _get_creds()
    if not creds:
        return
    token, chat_id = creds
    await _send_raw(token, chat_id, text)


async def send_document_async(filename: str, content: str) -> None:
    """Send a text file as a Telegram document (async, for bot handlers)."""
    creds = _get_creds()
    if not creds:
        return
    token, chat_id = creds
    await _send_document_raw(token, chat_id, filename, content)


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

    Three-stage detection (lower thresholds than before):
      Score ≥ 3 → fire even on 1st message (very strong signal)
      Score ≥ 2 → fire after 2+ user messages
      Score ≥ 1 or contact ≥ 2 → fire after 3+ user messages (original logic)
    """
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return None

    text = _text_of(messages)
    score = _keyword_score(text, _HIRING_KEYWORDS)
    contact_score = _keyword_score(text, _CONTACT_KEYWORDS)
    msg_count = len(user_msgs)
    long_session = msg_count >= 8

    triggered = (
        (score >= 3)                                           # 1+ msg, very strong
        or (msg_count >= 2 and score >= 2)                    # 2+ msgs, strong
        or (msg_count >= 3 and (score >= 1 or contact_score >= 2))  # 3+ msgs, weak
        or (long_session and score >= 1)                      # long session, any
    )
    if not triggered:
        return None

    # Fetch project list via API (sync wrapper around async api_client)
    projects = _get_projects_sync()
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
        "score":        score,
        "contact":      contact_score,
        "msg_count":    msg_count,
        "long_session": long_session,
        "top_project":  top_project,
    }


def detect_watch_mentions(messages: list[dict]) -> list[str]:
    """Return names of watched projects mentioned in *messages*."""
    watchlist = load_watchlist()
    if not watchlist:
        return []
    text = _text_of(messages)
    return [p for p in watchlist if p in text]


# ── Notification formatters ────────────────────────────────────────────────
def fmt_new_visitor_alert(first_message: str, time_str: str) -> str:
    short = first_message[:200].replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"🆕 <b>Yeni Ziyaretçi Sohbeti</b>\n"
        f"💬 {short}\n"
        f"⏰ {time_str}"
    )


def fmt_hiring_alert(signal: dict) -> str:
    project_line = f"\n🎯 <b>Proje:</b> {signal['top_project']}" if signal.get("top_project") else ""
    long_flag = " (uzun oturum 🔥)" if signal.get("long_session") else ""

    # Suggest adding to watchlist if not already there
    watchlist_hint = ""
    if signal.get("top_project"):
        wl = load_watchlist()
        slug = signal["top_project"].lower().strip()
        if slug not in wl:
            watchlist_hint = f"\n\n💡 <b>{signal['top_project']}</b> watchlist'te değil → <code>/watch {slug}</code>"

    return (
        f"🚨 <b>İşe Alım / İşbirliği Sinyali</b>{long_flag}\n"
        f"📬 {signal['msg_count']} mesajlık oturum"
        f"{project_line}\n"
        f"💡 Hiring score: {signal['score']} · Contact score: {signal['contact']}"
        f"{watchlist_hint}"
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


def fmt_long_session_alert(msg_count: int, top_project: str, level: int = 1) -> str:
    proj    = f" — <b>{top_project}</b>" if top_project else ""
    emoji   = "🔥🔥" if level >= 2 else "💬"
    label   = "Çok Uzun Oturum" if level >= 2 else "Uzun Oturum"
    return (
        f"{emoji} <b>{label}</b>{proj}\n"
        f"Ziyaretçi {msg_count} mesaj gönderdi."
    )


# ── High-level notification triggers ──────────────────────────────────────

def notify_new_visitor(first_message: str, log_filename: str) -> None:
    """
    Called when a brand-new chat session starts (first message of a new log).
    """
    if not is_new_visitor_notify_enabled():
        print("[NOTIFY] Yeni ziyaretçi bildirimi KAPALI (toggle)", file=sys.stderr)
        return
    if is_muted():
        print("[NOTIFY] Mute aktif — yeni ziyaretçi bildirimi atlanıyor", file=sys.stderr)
        return

    # Anti-spam: check for self-test burst (via API, sync wrapper)
    try:
        logs = _get_chat_logs_sync()
        now = time.time()
        recent = [l for l in logs if now - l.get("mtime", 0) < _TEST_SPAM_WINDOW]
        print(f"[NOTIFY] Self-test check: {len(recent)}/{_TEST_SPAM_THRESHOLD} recent logs in {_TEST_SPAM_WINDOW}s", file=sys.stderr)
        if len(recent) >= _TEST_SPAM_THRESHOLD:
            print(
                f"[NOTIFY] ⚠️ Yeni ziyaretçi ATLANDI — self-test burst detected "
                f"({len(recent)} logs in {_TEST_SPAM_WINDOW}s)",
                file=sys.stderr,
            )
            return
    except Exception as e:
        print(f"[NOTIFY] Self-test check hatası: {e}", file=sys.stderr)

    # Per-session dedup: only fire once per log file
    if not _should_send("new_visitor", log_filename, cooldown_secs=86400 * 7):
        print(f"[NOTIFY] Yeni ziyaretçi bildirimi ATLANDI — cooldown (log={log_filename})", file=sys.stderr)
        return

    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Istanbul")
    except Exception:
        tz = None
    now_dt = datetime.now(tz) if tz else datetime.now()
    time_str = now_dt.strftime("%H:%M")

    print(f"[NOTIFY] ✅ Yeni ziyaretçi bildirimi GÖNDERİLİYOR (log={log_filename}, msg='{first_message[:80]}...')", file=sys.stderr)
    send_notification(fmt_new_visitor_alert(first_message, time_str))


def notify_hiring_if_warranted(messages: list[dict], log_filename: str = "") -> None:
    """Called from ChatState after each AI response is saved."""
    if is_muted():
        return
    signal = detect_hiring_intent(messages)
    if not signal:
        # Debug: neden tetiklenmediğini göster
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if user_msgs:
            text = _text_of(messages)
            score = _keyword_score(text, _HIRING_KEYWORDS)
            contact_score = _keyword_score(text, _CONTACT_KEYWORDS)
            if score > 0 or contact_score > 0:
                print(
                    f"[HIRING] ⚠️ Eşik altı: score={score} contact={contact_score} "
                    f"msg_count={len(user_msgs)} (tetiklenmedi)",
                    file=sys.stderr,
                )
        return
    # Dedup key: per-session (log filename) to avoid repeat on every message
    key = log_filename or hashlib.md5(
        _text_of(messages).encode()[:200]
    ).hexdigest()[:12]
    if _should_send("hiring", key, _HIRING_COOLDOWN):
        print(
            f"[HIRING] ✅ İşe alım sinyali GÖNDERİLİYOR! "
            f"score={signal['score']} contact={signal['contact']} "
            f"msgs={signal['msg_count']} project={signal.get('top_project','—')}",
            file=sys.stderr,
        )
        send_notification(fmt_hiring_alert(signal))
    else:
        print(
            f"[HIRING] Tetiklendi ama cooldown'da "
            f"(score={signal['score']}, key={key})",
            file=sys.stderr,
        )


def notify_watch_if_warranted(messages: list[dict]) -> None:
    """Called from ChatState after each AI response. Fires per watched project."""
    if is_muted():
        return
    mentioned = detect_watch_mentions(messages)
    if not mentioned:
        return
    msg_count = sum(1 for m in messages if m.get("role") == "user")
    for project in mentioned:
        if _should_send("watch", project, _WATCH_COOLDOWN):
            print(f"[WATCH] Firing watch alert for: {project}", file=sys.stderr)
            send_notification(fmt_watch_alert(project, msg_count))


def notify_error(error: str, context: str = "") -> None:
    """Called from exception handlers. Groups errors by type. Never muted."""
    key = hashlib.md5(error.encode()[:100]).hexdigest()[:12]
    if _should_send("error", key, _ERROR_COOLDOWN):
        print(f"[NOTIFY] Firing error alert", file=sys.stderr)
        # ignore_mute=True — errors are always critical
        send_notification(fmt_error_alert(error, context), ignore_mute=True)


def notify_long_session(messages: list[dict], log_filename: str = "") -> None:
    """
    Cascading threshold:
      10 user messages → level-1 alert (💬 Uzun Oturum)
      20 user messages → level-2 alert (🔥🔥 Çok Uzun Oturum)
    Each level fires only once per session.
    """
    if is_muted():
        return

    user_msgs = [m for m in messages if m.get("role") == "user"]
    count = len(user_msgs)

    # Determine which level should fire
    if count >= 20:
        level = 2
    elif count >= 10:
        level = 1
    else:
        return

    projects = _get_projects_sync()
    text = _text_of(messages)
    top_project = ""
    top_count = 0
    for p in projects:
        name = p.get("name", "").lower()
        if name and name in text:
            c = text.count(name)
            if c > top_count:
                top_count = c
                top_project = p.get("name", "")

    session_key = log_filename or hashlib.md5(text.encode()[:300]).hexdigest()[:12]
    dedup_key = f"{session_key}:lvl{level}"
    if _should_send("long_session", dedup_key, cooldown_secs=86400):
        print(f"[NOTIFY] Firing long-session alert level={level} ({count} msgs)", file=sys.stderr)
        send_notification(fmt_long_session_alert(count, top_project, level))
