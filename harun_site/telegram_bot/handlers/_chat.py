# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_chat.py
──────────────────────────────────────────
Chat-log browsing and export commands.

Commands: /read, /export, /sor
"""
from __future__ import annotations

import sys
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Istanbul")
except Exception:
    _TZ = None

from harun_site.telegram_bot.handlers._reply import (
    _deny_if_not_owner,
    _escape_html,
    _msg,
    _now,
    _reply,
    _reply_error,
    _reply_multipart,
    _reply_plain,
    format_markdown_to_tg_html,
)


# ── /read ──────────────────────────────────────────────────────────────────
async def cmd_read(update, context) -> None:
    """Read chat logs via API client.

    /read        → list last 5 sessions
    /read <N>    → full transcript of session #N
    """
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.telegram_bot.api_client import api_client

        logs = await api_client.get_chat_logs()
        if not logs:
            await _reply_plain(update, "\U0001f4ed Hen\u00fcz hi\u00e7 sohbet kayd\u0131 yok.")
            return

        args = context.args

        # /read <N> → show specific chat transcript
        if args:
            try:
                idx = int(args[0]) - 1
                if idx < 0 or idx >= len(logs):
                    await _reply_plain(
                        update,
                        f"\u26a0\ufe0f Ge\u00e7ersiz numara. 1\u2013{len(logs)} aras\u0131nda bir de\u011fer gir.",
                    )
                    return
            except ValueError:
                await _reply_plain(update, "Kullan\u0131m: /read veya /read 1")
                return

            log = logs[idx]
            messages = await api_client.get_chat_log_messages(log["filename"])
            ts = log.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                if _TZ:
                    dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
                ts_fmt = (
                    dt.strftime("%-d %B %Y, %H:%M")
                    if sys.platform != "win32"
                    else dt.strftime("%d %B %Y, %H:%M")
                )
            except Exception:
                ts_fmt = ts[:16]

            user_count = sum(1 for m in messages if m.get("role") == "user")
            lines = [
                f"\U0001f4d6 <b>Sohbet #{idx + 1}</b> \u2014 {ts_fmt}\n"
                f"\U0001f4ac {user_count} kullan\u0131c\u0131 mesaj\u0131\n"
            ]
            for m in messages:
                role    = m.get("role", "")
                content = _escape_html(m.get("content", ""))[:600]
                if role == "user":
                    lines.append(f"\U0001f464 {content}")
                elif role == "assistant":
                    lines.append(f"\U0001f916 {content}")
                lines.append("")

            await _reply_multipart(update, "\n".join(lines))
            return

        # /read → list last 5 chats
        display = logs[:5]
        lines = ["\U0001f4d6 <b>Son Sohbetler:</b>\n"]
        now = _now()

        for i, log in enumerate(display, 1):
            ts = log.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                if _TZ:
                    dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
                diff = (now.date() - dt.date()).days
                if dt.date() == now.date():
                    ts_fmt = dt.strftime("%H:%M")
                elif diff == 1:
                    ts_fmt = "D\u00fcn " + dt.strftime("%H:%M")
                else:
                    ts_fmt = dt.strftime("%d.%m %H:%M")
            except Exception:
                ts_fmt = ts[:16]

            user_count = log.get("user_message_count", log.get("message_count", 0) // 2)
            flag = " \U0001f525" if user_count >= 8 else ""
            try:
                msgs = await api_client.get_chat_log_messages(log["filename"])
                first_msg = next(
                    (m.get("content", "") for m in msgs if m.get("role") == "user"), ""
                )
                preview = _escape_html(first_msg[:60]) + ("\u2026" if len(first_msg) > 60 else "")
            except Exception:
                preview = ""

            num_emoji = ["1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3", "4\ufe0f\u20e3", "5\ufe0f\u20e3"][i - 1]
            lines.append(f'{num_emoji} [{ts_fmt}] "{preview}" ({user_count} mesaj){flag}')

        lines.append(f"\n<i>Detay i\u00e7in: /read 1 \u2026 /read {len(display)}</i>")
        await _reply_plain(update, "\n".join(lines))
    except Exception as exc:
        await _reply_error(update, exc, context="/read")


# ── /export ────────────────────────────────────────────────────────────────
async def cmd_export(update, context) -> None:
    """Export chat logs as a plain-text file.

    /export          → all logs
    /export today    → today only
    /export last5    → last 5 sessions
    """
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.telegram_bot.api_client import api_client

        mode = context.args[0].lower() if context.args else "all"
        logs = await api_client.get_chat_logs()
        if not logs:
            await _reply_plain(update, "\U0001f4ed Hen\u00fcz hi\u00e7 sohbet kayd\u0131 yok.")
            return

        if mode == "today":
            today_str = _now().date().isoformat()
            filtered = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
            if not filtered:
                await _reply_plain(update, "\U0001f4ed Bug\u00fcn hi\u00e7 sohbet yok.")
                return
            label = "bugun"
        elif mode == "last5":
            filtered = logs[:5]
            label = "son5"
        else:
            filtered = logs
            label = "tum_loglar"

        status = _msg(update)
        if status:
            await status.reply_text(
                f"\U0001f4e4 {len(filtered)} sohbet haz\u0131rlan\u0131yor\u2026"
            )

        separator = "\u2550" * 40
        thin_sep  = "\u2500" * 40
        content_parts = [
            "PORTF\u00d6Y SOHBET KAYITLARI",
            f"Olu\u015fturulma: {_now().strftime('%d.%m.%Y %H:%M')} (\u0130stanbul)",
            f"Toplam sohbet: {len(filtered)}",
            "",
        ]

        for i, log in enumerate(filtered, 1):
            ts = log.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                if _TZ:
                    dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
                ts_fmt = dt.strftime("%d %B %Y, %H:%M")
            except Exception:
                ts_fmt = ts[:16]

            messages   = await api_client.get_chat_log_messages(log["filename"])
            user_count = sum(1 for m in messages if m.get("role") == "user")

            content_parts += [
                separator,
                f"SOHBET #{i} \u2014 {ts_fmt}",
                f"Kullan\u0131c\u0131 mesaj say\u0131s\u0131: {user_count}",
                separator,
                "",
            ]
            for m in messages:
                role    = m.get("role", "")
                content = m.get("content", "").strip()
                if role == "user":
                    content_parts.append(f"[Ziyaret\u00e7i]\n{content}")
                elif role == "assistant":
                    content_parts.append(f"[Harun]\n{content}")
                content_parts.append("")
            content_parts += [thin_sep, ""]

        full_content = "\n".join(content_parts)
        filename = (
            f"portfolio_sohbetler_{label}_{_now().strftime('%Y%m%d_%H%M')}.txt"
        )

        from harun_site.telegram_bot.notifier import send_document_async
        await send_document_async(filename, full_content)
        await _reply_plain(
            update,
            f"\u2705 <b>{len(filtered)}</b> sohbet dosya olarak g\u00f6nderildi.",
        )
    except Exception as exc:
        print(f"[TELEGRAM] /export error: {exc}", file=sys.stderr)
        await _reply_error(update, exc, context="/export")


# ── /sor ───────────────────────────────────────────────────────────────────
async def cmd_sor(update, context) -> None:
    """Simulate a portfolio visitor chat interaction."""
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.handlers._analytics import _run_portfolio_query

    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await _reply_plain(update, "Kullan\u0131m: /sor CebirX nedir?")
        return

    from harun_site.telegram_bot.handlers._reply import _thinking
    await _thinking(update, context)
    msg = _msg(update)
    if msg:
        await msg.reply_text("\U0001f4ac Portfolyo yan\u0131t\u0131 haz\u0131rlan\u0131yor\u2026")
    try:
        from harun_site.utils.chat_enrich import finalize_project_references
        answer          = await _run_portfolio_query(question)
        answer          = finalize_project_references(answer, question)
        formatted_answer = format_markdown_to_tg_html(answer)
        await _reply(update, formatted_answer, parse_html=True)
    except Exception as exc:
        await _reply_error(update, exc, context="/sor")
