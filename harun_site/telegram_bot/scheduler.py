# -*- coding: utf-8 -*-
"""
──────────────────────────────────────
Lightweight async background scheduler for the Telegram bot.

Responsibilities
────────────────
* Nightly summary at a configurable hour (default 21:00 Istanbul time)
* Periodic health-check ping (optional, off by default)

Design
──────
* Runs as a background asyncio Task inside the bot process.
* NEVER imports from Reflex — safe to run standalone.
* All datetime operations use Europe/Istanbul timezone.
* On failure: logs the error, sleeps, and retries next cycle.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Istanbul")
except Exception:
    _TZ = None


def _now() -> datetime:
    return datetime.now(_TZ) if _TZ else datetime.now()


def _today_str() -> str:
    return _now().date().isoformat()


# Lazy import to avoid import-time side effects when running inside Reflex
def _get_notifier():
    from harun_site.telegram_bot import notifier as _n
    return _n


def _get_api_client():
    from harun_site.telegram_bot.api_client import api_client as _ac
    return _ac


# ── Config from env ────────────────────────────────────────────────────────
_SUMMARY_HOUR    = int(os.environ.get("DAILY_SUMMARY_HOUR",  "21"))   # 24h Istanbul
_HEALTH_INTERVAL = int(os.environ.get("HEALTH_CHECK_HOURS",   "0"))   # 0 = disabled

_STATE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "tg_scheduler_state.json"


def _load_state() -> dict:
    if not _STATE_FILE.exists():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    import shutil, tempfile
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(_STATE_FILE.parent), prefix="tg_sched_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        shutil.move(tmp, str(_STATE_FILE))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass


# ── Daily summary builder ──────────────────────────────────────────────────
async def build_daily_summary() -> str:
    """
    Build a rich human-readable daily summary string.
    No Groq — fast, free, keyword-based analysis.
    """
    ac        = _get_api_client()
    notifier  = _get_notifier()
    today     = _today_str()
    logs      = await ac.get_chat_logs()

    # Filter logs from today
    today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today)]

    total_sessions  = len(today_logs)
    total_user_msgs = sum(
        l.get("user_message_count", l.get("message_count", 0) // 2)
        for l in today_logs
    )
    all_sessions = len(logs)

    # ── Project mention tally ────────────────────────────────────────────
    projects = await ac.get_projects()
    proj_counts: dict[str, int] = {p.get("name", ""): 0 for p in projects}

    # ── Hiring signal count + top user questions ─────────────────────────
    hiring_count     = 0
    top_questions: list[str] = []

    from harun_site.telegram_bot.notifier import _HIRING_KEYWORDS, _keyword_score

    for log in today_logs:
        messages = await ac.get_chat_log_messages(log["filename"])
        user_text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        ).lower()

        # Project mentions
        for p in projects:
            name = p.get("name", "").lower()
            if name and name in user_text:
                proj_counts[p.get("name", "")] += 1

        # Hiring signal?
        if _keyword_score(user_text, _HIRING_KEYWORDS) >= 1:
            hiring_count += 1

        # Collect first user message as a notable question sample
        first_user = next(
            (m.get("content", "") for m in messages if m.get("role") == "user"),
            "",
        )
        if first_user and len(top_questions) < 3:
            top_questions.append(first_user[:100])

    # Top project
    top_project = max(proj_counts, key=proj_counts.get) if proj_counts else ""
    top_count   = proj_counts.get(top_project, 0)

    # ── Weekly comparison ─────────────────────────────────────────────────
    # Count sessions from the previous 7 days (excluding today)
    from datetime import timedelta as _td
    week_ago = (_now().date() - _td(days=7)).isoformat()
    prev_week_logs = [
        l for l in logs
        if week_ago <= (l.get("timestamp") or "")[:10] < today
    ]
    prev_avg = len(prev_week_logs) / 7 if prev_week_logs else 0
    if prev_avg > 0:
        pct_change = ((total_sessions - prev_avg) / prev_avg) * 100
        trend_sign = "+" if pct_change >= 0 else ""
        trend_line = f"📈 7 günlük ortalamayla: {trend_sign}{pct_change:.0f}%"
    else:
        trend_line = ""

    # ── Watchlist ──────────────────────────────────────────────────────────
    watchlist  = notifier.load_watchlist()
    watch_line = ("👀 İzleniyor: " + ", ".join(watchlist)) if watchlist else "👀 Watchlist boş"

    # ── Mute status ────────────────────────────────────────────────────────
    mute_state = notifier.get_mute_state()
    mute_lines: list[str] = []
    if mute_state["muted"]:
        if mute_state["until"] == -1:
            mute_lines = ["", "🔇 <b>Sistem şu an MUTE konumunda</b> (açana kadar)", "   Açmak için: /unmute"]
        else:
            until_dt = datetime.fromtimestamp(mute_state["until"], tz=_TZ) if _TZ else datetime.fromtimestamp(mute_state["until"])
            mute_lines = ["", f"🔇 <b>Sistem MUTE</b> ({until_dt.strftime('%H:%M')}'e kadar)", "   Açmak için: /unmute"]

    # ── Assemble ───────────────────────────────────────────────────────────
    lines: list[str] = [
        f"📊 <b>Günlük Özet — {today}</b>",
        *mute_lines,
        "",
        f"👥 Bugünkü oturum: <b>{total_sessions}</b>",
        f"💬 Bugünkü kullanıcı mesajı: <b>{total_user_msgs}</b>",
        f"📚 Toplam kayıtlı oturum: {all_sessions}",
    ]

    if top_project and top_count > 0:
        lines.append(f"🔥 En çok konuşulan: <b>{top_project}</b> ({top_count} oturum)")
    if hiring_count > 0:
        lines.append(f"🚨 Hiring sinyali: <b>{hiring_count} oturum</b>")
    if trend_line:
        lines.append(trend_line)

    if top_questions:
        lines.append("")
        lines.append("💬 <b>Öne çıkan sorular:</b>")
        for q in top_questions:
            lines.append(f"  • {q.replace('<','&lt;').replace('>','&gt;')}")

    lines.append("")
    lines.append(watch_line)

    return "\n".join(lines)


# ── Health report builder ──────────────────────────────────────────────────
async def build_health_report() -> str:
    """Health check -- log count via API, local disk stats if accessible."""
    ac        = _get_api_client()
    notifier  = _get_notifier()
    logs      = await ac.get_chat_logs()
    watchlist = notifier.load_watchlist()

    # Disk size: best-effort (may not be available on Railway)
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    try:
        disk_mb = sum(
            f.stat().st_size for f in data_dir.rglob("*.json") if f.is_file()
        ) / (1024 * 1024)
        disk_line = f"\U0001f4be Data boyutu: {disk_mb:.2f} MB"
        warn_line = (
            "\u26a0\ufe0f Data dizini buyuyor -- eski loglari temizlemeyi dusun."
            if disk_mb > 50 else ""
        )
    except Exception:
        disk_line = "\U0001f4be Data boyutu: olculemedI (uzak ortam)"
        warn_line = ""

    mute_state = notifier.get_mute_state()
    mute_info  = ""
    if mute_state["muted"]:
        if mute_state["until"] == -1:
            mute_info = "\n\U0001f507 Bildirimler: MUTE (suresiz)"
        else:
            until_dt = datetime.fromtimestamp(mute_state["until"], tz=_TZ) if _TZ else datetime.fromtimestamp(mute_state["until"])
            mute_info = f"\n\U0001f507 Bildirimler: MUTE ({until_dt.strftime('%H:%M')}'e kadar)"
    else:
        mute_info = "\n\U0001f514 Bildirimler: Aktif"

    lines = [
        "\U0001fa7a <b>Sistem Durumu</b>",
        "",
        f"\U0001f4c1 Chat log sayisi: {len(logs)}",
        f"\U0001f440 Watchlist: {', '.join(watchlist) if watchlist else chr(8212)}",
        disk_line,
        f"\U0001f550 Sunucu saati: {_now().strftime('%H:%M')} (Istanbul)",
        mute_info,
    ]
    if warn_line:
        lines.append(warn_line)
    return "\n".join(lines)


# ── Scheduler loop ─────────────────────────────────────────────────────────
async def scheduler_loop(send_fn) -> None:
    """
    Main scheduler coroutine. *send_fn* is an async callable that accepts (text: str)
    and sends a Telegram message to the admin.

    Runs indefinitely; designed to be started as asyncio.create_task().
    All time comparisons use Europe/Istanbul timezone.
    """
    print("[TELEGRAM] Scheduler started.", file=sys.stderr)
    state = _load_state()

    while True:
        try:
            now   = _now()
            today = now.date().isoformat()

            # ── Nightly summary ──────────────────────────────────────────
            last_summary = state.get("last_summary_date", "")
            if now.hour >= _SUMMARY_HOUR and last_summary != today:
                summary = await build_daily_summary()
                # Daily summary is never muted — use send_fn directly
                await send_fn(summary)
                state["last_summary_date"] = today
                _save_state(state)
                print(f"[TELEGRAM] Nightly summary sent.", file=sys.stderr)

            # ── Periodic health check ────────────────────────────────────
            if _HEALTH_INTERVAL > 0:
                last_health = state.get("last_health_ts", 0)
                if time.time() - last_health > _HEALTH_INTERVAL * 3600:
                    report = await build_health_report()
                    await send_fn(report)
                    state["last_health_ts"] = time.time()
                    _save_state(state)
                    print(f"[TELEGRAM] Health check sent.", file=sys.stderr)

        except Exception as exc:
            print(f"[TELEGRAM] Scheduler error: {exc}", file=sys.stderr)

        # Sleep until next minute boundary
        await asyncio.sleep(60)
