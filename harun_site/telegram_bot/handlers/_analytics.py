# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_analytics.py
────────────────────────────────────────────────
AI-powered log analysis and statistics commands.

Commands: /stats, /summary, /hot, /panic, /visitor
Bridge functions: _build_log_payload, _run_analytics_query, _run_portfolio_query
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from collections import Counter

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
    _reply_plain,
    _thinking,
    format_markdown_to_tg_html,
)


# ── API / AI bridge ────────────────────────────────────────────────────────
async def _build_log_payload(max_logs: int = 12) -> list[dict]:
    """Fetch recent chat logs from Reflex Cloud API for AI analysis."""
    from harun_site.telegram_bot.api_client import api_client

    logs = await api_client.get_chat_logs()
    payload = []
    for log in logs[:max_logs]:
        messages = await api_client.get_chat_log_messages(log["filename"])
        payload.append({
            "filename":          log["filename"],
            "timestamp":         log.get("timestamp", ""),
            "message_count":     log.get("message_count", 0),
            "user_samples":      [
                m.get("content", "")[:160]
                for m in messages if m.get("role") == "user"
            ][:3],
            "assistant_samples": [
                m.get("content", "")[:100]
                for m in messages if m.get("role") == "assistant"
            ][:1],
        })
    return payload


async def _run_analytics_query(chat_id: int, question: str) -> str:
    """Ask Groq AI about chat logs fetched via API."""
    from harun_site.utils.groq_client import answer_admin_chat_about_logs
    from harun_site.telegram_bot.memory import append_turn, get_history

    payload = await _build_log_payload()
    history = get_history(chat_id)
    history_with_question = [*history, {"role": "user", "content": question}]
    answer = await answer_admin_chat_about_logs(history_with_question, payload)
    append_turn(chat_id, question, answer)
    return answer


async def _run_portfolio_query(question: str) -> str:
    """Single-turn portfolio chat simulation (no log API)."""
    from harun_site.utils.groq_client import complete_chat
    return await complete_chat([{"role": "user", "content": question}])


# ── /stats ─────────────────────────────────────────────────────────────────
async def cmd_stats(update, context) -> None:
    """Quick stats via Reflex Cloud API."""
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.telegram_bot.api_client import api_client
        from harun_site.telegram_bot.notifier import load_watchlist

        stats = await api_client.get_stats()
        watchlist = load_watchlist()
        if stats:
            wl_str = ", ".join(watchlist) if watchlist else "\u2014"
            await _reply_plain(
                update,
                f"\U0001f4c8 <b>\u0130statistikler</b>\n\n"
                f"\U0001f4c1 Toplam kay\u0131t: <b>{stats.get('total_sessions', 0)}</b>\n"
                f"\U0001f4ac Toplam kullan\u0131c\u0131 mesaj\u0131: <b>{stats.get('total_user_messages', 0)}</b>\n"
                f"\U0001f465 Bug\u00fcnk\u00fc oturum: <b>{stats.get('today_sessions', 0)}</b>\n"
                f"\U0001f4e9 Bug\u00fcnk\u00fc kullan\u0131c\u0131 mesaj\u0131: <b>{stats.get('today_user_messages', 0)}</b>\n"
                f"\U0001f440 Watchlist: {wl_str}",
            )
        else:
            await _reply_plain(
                update,
                "\u26a0\ufe0f \u0130statistikler al\u0131namad\u0131 \u2014 API yan\u0131t\u0131 bo\u015f.",
            )
    except Exception as exc:
        await _reply_error(update, exc, context="/stats")


# ── /summary ───────────────────────────────────────────────────────────────
async def cmd_summary(update, context) -> None:
    """Trigger the daily summary builder on demand."""
    if not await _deny_if_not_owner(update):
        return
    print("[TELEGRAM] /summary requested", file=sys.stderr)
    if _msg(update):
        await _msg(update).reply_text("\u23f3 \u00d6zet haz\u0131rlan\u0131yor\u2026")
    try:
        from harun_site.telegram_bot.scheduler import build_daily_summary
        summary = await build_daily_summary()
        await _reply_plain(update, summary)
    except Exception as exc:
        print(f"[TELEGRAM] /summary error: {exc}", file=sys.stderr)
        await _reply_error(update, exc, context="/summary")


# ── /hot ───────────────────────────────────────────────────────────────────
async def cmd_hot(update, context) -> None:
    """AI analysis: interesting sessions (recruiter, hiring, deep tech…)."""
    if not await _deny_if_not_owner(update):
        return
    await _thinking(update, context)
    if _msg(update):
        await _msg(update).reply_text("\U0001f50d Analiz ediliyor\u2026")
    try:
        chat_id = update.effective_chat.id
        question = (
            "Son oturumlarda \u00f6ne \u00e7\u0131kan ilgin\u00e7 konu\u015fmalar hangileri? "
            "Recruiter, hiring, derin teknik soru veya conversion sinyali olanlar\u0131 k\u0131saca listele."
        )
        answer = await _run_analytics_query(chat_id, question)
        await _reply(update, format_markdown_to_tg_html(answer), parse_html=True)
    except Exception as exc:
        await _reply_error(update, exc, context="/hot")


# ── /panic ─────────────────────────────────────────────────────────────────
async def cmd_panic(update, context) -> None:
    """System health report + Groq API status check."""
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.telegram_bot.scheduler import build_health_report
        report = await build_health_report()

        groq_ok = False
        try:
            import httpx
            token = os.environ.get("GROQ_API_KEY", "")
            if token:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(
                        "https://api.groq.com/openai/v1/models",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                groq_ok = r.status_code == 200
        except Exception:
            groq_ok = False

        groq_line = (
            "\u2705 Groq eri\u015filebilir"
            if groq_ok
            else "\u274c Groq eri\u015filemiyor / kota dolu olabilir"
        )
        await _reply_plain(update, report + f"\n{groq_line}")
    except Exception as exc:
        print(f"[TELEGRAM] /panic error: {exc}", file=sys.stderr)
        await _reply_error(update, exc, context="/panic")


# ── /visitor ───────────────────────────────────────────────────────────────
async def cmd_visitor(update, context) -> None:
    """Live visitor status via API client."""
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.telegram_bot.api_client import api_client
        from datetime import date as _date

        logs = await api_client.get_chat_logs()
        now = _now()
        today_str = now.date().isoformat()

        today_logs = [
            l for l in logs if (l.get("timestamp") or "").startswith(today_str)
        ]
        week_start_ord = now.date().toordinal() - now.weekday()
        week_logs: list[dict] = []
        for l in logs:
            try:
                d = _date.fromisoformat(l["timestamp"][:10])
                if d.toordinal() >= week_start_ord:
                    week_logs.append(l)
            except Exception:
                pass

        def _uc(log: dict) -> int:
            return log.get("user_message_count", log.get("message_count", 0) // 2)

        today_msgs = sum(_uc(l) for l in today_logs)
        week_msgs  = sum(_uc(l) for l in week_logs)

        day_names = ["Pazartesi", "Sal\u0131", "\u00c7ar\u015famba", "Per\u015fembe", "Cuma", "Cumartesi", "Pazar"]
        day_counts: Counter = Counter()
        for l in week_logs:
            try:
                d = _date.fromisoformat(l["timestamp"][:10])
                day_counts[day_names[d.weekday()]] += 1
            except Exception:
                pass
        busiest = max(day_counts, key=day_counts.get) if day_counts else "\u2014"
        busiest_count = day_counts.get(busiest, 0)

        lines = [
            "\U0001f465 <b>Ziyaret\u00e7i Durumu</b>\n",
            f"\U0001f4ca Bug\u00fcn: <b>{len(today_logs)} oturum</b>, {today_msgs} mesaj",
            f"\U0001f4c8 Bu hafta: <b>{len(week_logs)} oturum</b>, {week_msgs} mesaj",
            (
                f"\U0001f525 En aktif g\u00fcn: <b>{busiest}</b> ({busiest_count} oturum)"
                if busiest != "\u2014" else ""
            ),
            "",
            "Son 3 sohbet:",
        ]

        for i, log in enumerate(logs[:3], 1):
            ts = log.get("timestamp", "")
            try:
                from datetime import datetime as _dt
                dt = _dt.fromisoformat(ts)
                if _TZ:
                    dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
                ts_fmt = (
                    dt.strftime("%H:%M") if dt.date() == now.date()
                    else dt.strftime("%d.%m %H:%M")
                )
            except Exception:
                ts_fmt = ts[:16]

            uc = _uc(log)
            flag = " \U0001f6a8" if uc >= 6 else ""
            try:
                msgs = await api_client.get_chat_log_messages(log["filename"])
                first = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
                preview = _escape_html(first[:50]) + ("\u2026" if len(first) > 50 else "")
            except Exception:
                preview = ""
            lines.append(f"{i}. {ts_fmt} \u2014 \"{preview}\" ({uc} mesaj){flag}")

        await _reply_plain(update, "\n".join(l for l in lines if l is not None))
    except Exception as exc:
        await _reply_error(update, exc, context="/visitor")
