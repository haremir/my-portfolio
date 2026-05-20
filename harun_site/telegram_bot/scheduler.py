"""
harun_site/telegram_bot/scheduler.py
──────────────────────────────────────
Lightweight async background scheduler for the Telegram bot.

Responsibilities
────────────────
* Nightly summary at a configurable hour (default 21:00 local time)
* Periodic health-check ping (optional, off by default)
* Inactivity ping when no chat logs arrive for N hours (optional)

Design
──────
* Runs as a background asyncio Task inside the bot process.
* NEVER imports from Reflex — safe to run standalone.
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

# Lazy import to avoid import-time side effects when running inside Reflex
def _get_notifier():
    from harun_site.telegram_bot import notifier as _n
    return _n


def _get_data_manager():
    from harun_site.utils import data_manager as _dm
    return _dm


# ── Config from env ────────────────────────────────────────────────────────
_SUMMARY_HOUR    = int(os.environ.get("DAILY_SUMMARY_HOUR", "21"))   # 24h local
_HEALTH_INTERVAL = int(os.environ.get("HEALTH_CHECK_HOURS",  "0"))   # 0 = disabled
_INACTIVITY_HRS  = int(os.environ.get("INACTIVITY_PING_HOURS", "0")) # 0 = disabled

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
    """Build a human-readable daily summary string (no Groq — fast and free)."""
    dm = _get_data_manager()
    today_str = date.today().isoformat()
    logs = dm.load_chat_logs()

    # Filter logs from today
    today_logs = [
        l for l in logs
        if (l.get("timestamp") or "").startswith(today_str)
    ]

    total_visitors  = len(today_logs)
    total_messages  = sum(l.get("message_count", 0) for l in today_logs)
    all_logs_count  = len(logs)

    # Project mention tally across today's logs
    from harun_site.utils.data_manager import load_projects, load_chat_log_messages
    projects = load_projects()
    proj_counts: dict[str, int] = {p.get("name", ""): 0 for p in projects}

    for log in today_logs:
        messages = load_chat_log_messages(log["filename"])
        text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        ).lower()
        for p in projects:
            name = p.get("name", "").lower()
            if name and name in text:
                proj_counts[p.get("name", "")] += 1

    top_project = max(proj_counts, key=proj_counts.get) if proj_counts else ""
    top_count   = proj_counts.get(top_project, 0)

    # Watchlist
    watchlist   = _get_notifier().load_watchlist()
    watch_line  = ("👀 İzleniyor: " + ", ".join(watchlist)) if watchlist else "👀 Watchlist boş"

    lines = [
        f"📊 <b>Günlük Özet — {today_str}</b>",
        "",
        f"👥 Bugünkü oturum: <b>{total_visitors}</b>",
        f"💬 Bugünkü mesaj: <b>{total_messages}</b>",
        f"📚 Toplam kayıt: {all_logs_count}",
    ]
    if top_project and top_count > 0:
        lines.append(f"🔥 En çok konuşulan: <b>{top_project}</b> ({top_count} oturum)")
    lines.append(watch_line)

    return "\n".join(lines)


# ── Health report builder ──────────────────────────────────────────────────
async def build_health_report() -> str:
    """Fast health check — no external API calls."""
    dm = _get_data_manager()
    logs = dm.load_chat_logs()
    watchlist = _get_notifier().load_watchlist()
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    disk_mb = sum(
        f.stat().st_size for f in data_dir.rglob("*.json") if f.is_file()
    ) / (1024 * 1024)

    lines = [
        "🩺 <b>Sistem Durumu</b>",
        "",
        f"📁 Chat log sayısı: {len(logs)}",
        f"👀 Watchlist: {', '.join(watchlist) if watchlist else '—'}",
        f"💾 Data boyutu: {disk_mb:.2f} MB",
    ]
    if disk_mb > 50:
        lines.append("⚠️ Data dizini büyüyor — eski logları temizlemeyi düşün.")
    return "\n".join(lines)


# ── Scheduler loop ────────────────────────────────────────────────────────
async def scheduler_loop(send_fn) -> None:
    """
    Main scheduler coroutine. *send_fn* is an async callable that accepts (text: str)
    and sends a Telegram message to the admin.

    Runs indefinitely; designed to be started as asyncio.create_task().
    """
    print("[TELEGRAM] Scheduler started.", file=sys.stderr)
    state = _load_state()

    while True:
        try:
            now  = datetime.now()
            today = now.date().isoformat()

            # ── Nightly summary ──────────────────────────────────────────
            last_summary = state.get("last_summary_date", "")
            if now.hour >= _SUMMARY_HOUR and last_summary != today:
                summary = await build_daily_summary()
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
