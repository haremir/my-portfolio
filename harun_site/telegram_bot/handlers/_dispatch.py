# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_dispatch.py
──────────────────────────────────────────────
Inline button callback dispatcher and free-text message handler.
"""
from __future__ import annotations

import sys

from harun_site.telegram_bot.handlers._auth import _is_owner
from harun_site.telegram_bot.handlers._reply import _msg, _reply_plain


# ── Inline button callbacks ────────────────────────────────────────────────
async def handle_callback(update, context) -> None:
    """Route inline keyboard button presses to the appropriate command."""
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if not _is_owner(update):
        return
    data = query.data or ""

    # Mute duration selection
    if data.startswith("mute:"):
        duration = data.split(":", 1)[1]
        from harun_site.telegram_bot.notifier import set_mute

        try:
            from zoneinfo import ZoneInfo
            _TZ = ZoneInfo("Europe/Istanbul")
        except Exception:
            _TZ = None

        until = set_mute(duration)
        label = {"1h": "1 saat", "1d": "1 g\u00fcn"}.get(duration, "a\u00e7ana kadar")
        if until == -1:
            time_info = "s\u00fcresiz"
        else:
            from datetime import datetime as _dt
            until_dt = (
                _dt.fromtimestamp(until, tz=_TZ) if _TZ else _dt.fromtimestamp(until)
            )
            time_info = f"otomatik a\u00e7\u0131lma: {until_dt.strftime('%H:%M')}"
        await _reply_plain(
            update,
            f"\U0001f507 Bildirimler <b>{label}</b> s\u00fcreyle susturuldu.\n"
            f"\u23f0 {time_info}\n\n"
            "Bildirimleri a\u00e7mak i\u00e7in: /unmute",
        )
        return

    # Command shortcuts from the keyboard
    cmd = data.replace("cmd:", "", 1)
    print(f"[TELEGRAM] Button: {cmd}", file=sys.stderr)

    if cmd == "sor_hint":
        await _reply_plain(
            update,
            "\U0001f4ac Portfolyo ziyaret\u00e7i sohbeti:\n"
            "<code>/sor CebirX nedir?</code>\n\n"
            "Log analizi i\u00e7in do\u011frudan mesaj yaz.",
        )
        return

    # Lazy import to avoid circular deps at module level
    from harun_site.telegram_bot.handlers._analytics import (
        cmd_hot, cmd_panic, cmd_stats, cmd_summary, cmd_visitor,
    )
    from harun_site.telegram_bot.handlers._chat import cmd_export, cmd_read, cmd_sor
    from harun_site.telegram_bot.handlers._admin import (
        cmd_clear, cmd_help, cmd_mute, cmd_ping, cmd_start, cmd_unmute, cmd_watchlist,
    )

    dispatch = {
        "summary":   cmd_summary,
        "stats":     cmd_stats,
        "hot":       cmd_hot,
        "panic":     cmd_panic,
        "help":      cmd_help,
        "clear":     cmd_clear,
        "watchlist": cmd_watchlist,
        "ping":      cmd_ping,
        "start":     cmd_start,
        "visitor":   cmd_visitor,
        "read":      cmd_read,
        "export":    cmd_export,
        "mute":      cmd_mute,
        "unmute":    cmd_unmute,
    }
    handler = dispatch.get(cmd)
    if handler:
        await handler(update, context)
    else:
        await _reply_plain(update, f"\u26a0\ufe0f Bilinmeyen komut: {cmd}")


# ── Free-text → AI log analyst ────────────────────────────────────────────
async def handle_message(update, context) -> None:
    """Route free-text messages to the AI log-analysis engine."""
    from harun_site.telegram_bot.handlers._reply import _deny_if_not_owner, _thinking
    from harun_site.telegram_bot.handlers._analytics import (
        _run_analytics_query,
        format_markdown_to_tg_html,
    )
    from harun_site.telegram_bot.handlers._reply import _reply

    if not await _deny_if_not_owner(update):
        return
    text = (update.message.text or "").strip()
    if not text:
        return
    print(f"[TELEGRAM] Free-text query: {text[:80]}", file=sys.stderr)
    await _thinking(update, context)
    status = None
    if _msg(update):
        status = await _msg(update).reply_text("\U0001f914 Log analizi yap\u0131l\u0131yor\u2026")
    try:
        chat_id = update.effective_chat.id
        answer  = await _run_analytics_query(chat_id, text)
        try:
            await status.delete()
        except Exception:
            pass
        await _reply(update, format_markdown_to_tg_html(answer), parse_html=True)
    except Exception as exc:
        from harun_site.telegram_bot.handlers._reply import _reply_error
        await _reply_error(update, exc, context="message")
