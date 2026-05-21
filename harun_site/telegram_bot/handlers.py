"""
harun_site/telegram_bot/handlers.py
─────────────────────────────────────
Telegram command and message handlers.

Reuses:
  • answer_admin_chat_about_logs() — admin panel analytics asistanı
  • complete_chat() — portfolyo ziyaretçi sohbeti (/sor)
  • memory.get_history() / append_turn() — kalıcı oturum
"""

from __future__ import annotations

import os
import re
import sys
import traceback
from datetime import date

# ── Auth helper ────────────────────────────────────────────────────────────
def _owner_id() -> int | None:
    raw = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _user_id(update) -> int | None:
    if update.effective_user:
        return update.effective_user.id
    return None


def _is_owner(update) -> bool:
    allowed = _owner_id()
    uid = _user_id(update)
    if allowed is None:
        print("[TELEGRAM] TELEGRAM_ADMIN_ID not set — all handlers blocked.", file=sys.stderr)
        return False
    if uid != allowed:
        print(
            f"[SECURITY] Unauthorized telegram user: {uid} "
            f"(expected TELEGRAM_ADMIN_ID={allowed})",
            file=sys.stderr,
        )
        return False
    return True


async def _deny_if_not_owner(update) -> bool:
    """Return True if caller is owner; otherwise send setup hint and return False."""
    if _is_owner(update):
        return True
    uid = _user_id(update)
    allowed = _owner_id()
    if allowed is None:
        await _reply_plain(
            update,
            "⛔ TELEGRAM_ADMIN_ID .env dosyasında tanımlı değil.\n"
            "Bot yanıt veremez. /whoami ile kendi ID'ni öğrenip .env'e yaz.",
        )
    else:
        await _reply_plain(
            update,
            f"⛔ Bu bot sadece sahibine açık.\n"
            f"Senin Telegram ID: <b>{uid}</b>\n"
            f".env → TELEGRAM_ADMIN_ID={uid}",
        )
    return False


# ── Analytics bridge ───────────────────────────────────────────────────────
def _build_log_payload(max_logs: int = 12) -> list[dict]:
    from harun_site.utils.data_manager import load_chat_log_messages, load_chat_logs

    logs = load_chat_logs()
    payload = []
    for log in logs[:max_logs]:
        messages = load_chat_log_messages(log["filename"])
        payload.append({
            "filename": log["filename"],
            "timestamp": log.get("timestamp", ""),
            "message_count": log.get("message_count", 0),
            "user_samples": [
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
    from harun_site.utils.groq_client import answer_admin_chat_about_logs
    from harun_site.telegram_bot.memory import append_turn, get_history

    payload = _build_log_payload()
    history = get_history(chat_id)
    history_with_question = [*history, {"role": "user", "content": question}]
    answer = await answer_admin_chat_about_logs(history_with_question, payload)
    append_turn(chat_id, question, answer)
    return answer


async def _run_portfolio_query(question: str) -> str:
    """Ziyaretçi sitesindeki gibi portfolyo sohbeti (tek tur)."""
    from harun_site.utils.groq_client import complete_chat

    return await complete_chat([{"role": "user", "content": question}])


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_markdown_to_tg_html(text: str) -> str:
    """
    Convert basic markdown styling (**bold**, *italic*, `code`, [text](url))
    into Telegram-compatible HTML tags after escaping raw HTML characters.
    """
    if not text:
        return ""
    # 1. Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 2. Markdown Links: [text](url) -> <a href="url">text</a>
    # If the URL is relative (starts with /), prepend the site URL (default http://localhost:3000)
    site_url = os.environ.get("SITE_URL", "http://localhost:3000").rstrip("/")
    def link_repl(match):
        label = match.group(1)
        url = match.group(2)
        if url.startswith("/"):
            url = site_url + url
        return f'<a href="{url}">{label}</a>'
    
    text = re.sub(r"\[(.*?)\]\((.*?)\)", link_repl, text)

    # 3. Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # 4. Italic: *text* -> <i>text</i> or _text_ -> <i>text</i>
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.*?)_", r"<i>\1</i>", text)

    # 5. Inline Code: `code` -> <code>code</code>
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)

    return text


def _msg(update):
    return update.effective_message


async def _reply_plain(update, text: str, *, with_keyboard: bool = True) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n…(kısaltıldı)"
    from harun_site.telegram_bot.keyboards import command_keyboard

    kwargs = {
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if with_keyboard:
        kwargs["reply_markup"] = command_keyboard()
    await message.reply_text(text, **kwargs)


async def _reply(update, text: str, *, parse_html: bool = True, with_keyboard: bool = True) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>…(mesaj kısaltıldı)</i>"
    from harun_site.telegram_bot.keyboards import command_keyboard

    kwargs = {"disable_web_page_preview": True}
    if with_keyboard:
        kwargs["reply_markup"] = command_keyboard()
    try:
        await message.reply_text(
            text,
            parse_mode="HTML" if parse_html else None,
            **kwargs,
        )
    except Exception as exc:
        print(f"[TELEGRAM] HTML reply failed ({exc}), retrying plain.", file=sys.stderr)
        plain = re.sub(r"<[^>]+>", "", text) if parse_html else text
        await message.reply_text(plain[:4000], **kwargs)


async def _reply_error(update, exc: Exception, *, context: str) -> None:
    from harun_site.utils.groq_client import is_rate_limit_error, user_message_for_groq_error

    print(f"[TELEGRAM] {context} error: {exc}", file=sys.stderr)
    if not is_rate_limit_error(exc):
        traceback.print_exc()
    msg = user_message_for_groq_error(exc)
    await _reply_plain(update, _escape_html(msg))


async def _thinking(update, context) -> None:
    if update.effective_chat:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing",
        )


# ── /whoami (herkese — .env kurulumu için) ─────────────────────────────────
async def cmd_whoami(update, context) -> None:
    uid = _user_id(update) or "?"
    allowed = _owner_id()
    match = "✅ Sahip ID ile eşleşiyor." if allowed and uid == allowed else (
        f"⚠️ .env TELEGRAM_ADMIN_ID={allowed} — senin ID ile eşleşmiyor."
        if allowed else "⚠️ TELEGRAM_ADMIN_ID henüz tanımlı değil."
    )
    await _reply_plain(update, f"🆔 Telegram ID: <b>{uid}</b>\n{match}")


# ── /ping ──────────────────────────────────────────────────────────────────
async def cmd_ping(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    await _reply_plain(update, "🏓 pong — bot ayakta.")


# ── /start ─────────────────────────────────────────────────────────────────
async def cmd_start(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    print("[TELEGRAM] /start from owner", file=sys.stderr)
    await _reply_plain(
        update,
        "👋 <b>Portföy Ops Bot</b> hazır.\n\n"
        "/help — komutlar\n"
        "Serbest metin — ziyaretçi log analizi (admin asistanı gibi)\n"
        "/sor &lt;mesaj&gt; — portfolyo ziyaretçi sohbeti simülasyonu",
    )


# ── /help ──────────────────────────────────────────────────────────────────
async def cmd_help(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    await _reply_plain(
        update,
        "📋 <b>Komutlar</b>\n\n"
        "/ping — Bot ayakta mı?\n"
        "/summary — Günlük özet (Groq yok)\n"
        "/stats — Hızlı istatistik\n"
        "/hot — İlginç oturumlar (AI)\n"
        "/panic — Sistem raporu\n"
        "/sor &lt;mesaj&gt; — Portfolyo chat (site ziyaretçisi gibi)\n"
        "/watch /unwatch /watchlist — Proje takibi\n"
        "/clear — Analiz sohbet geçmişini sil\n\n"
        "💬 Serbest metin → admin panelindeki <b>log analist</b> asistanı\n"
        "<i>Örn: \"Bugün kim ne sordu?\" \"CebirX kaç kez geçti?\"</i>",
    )


# ── /sor — portfolyo ziyaretçi chat ────────────────────────────────────────
async def cmd_sor(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await _reply_plain(update, "Kullanım: /sor CebirX nedir?")
        return
    await _thinking(update, context)
    msg = _msg(update)
    if msg:
        await msg.reply_text("💬 Portfolyo yanıtı hazırlanıyor…")
    try:
        from harun_site.utils.chat_enrich import ensure_case_study_links

        answer = await _run_portfolio_query(question)
        answer = ensure_case_study_links(answer, question)
        formatted_answer = format_markdown_to_tg_html(answer)
        await _reply(update, formatted_answer, parse_html=True)
    except Exception as exc:
        await _reply_error(update, exc, context="/sor")


# ── /summary ───────────────────────────────────────────────────────────────
async def cmd_summary(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    print("[TELEGRAM] /summary requested", file=sys.stderr)
    if _msg(update):
        await _msg(update).reply_text("⏳ Özet hazırlanıyor…")
    try:
        from harun_site.telegram_bot.scheduler import build_daily_summary
        summary = await build_daily_summary()
        await _reply_plain(update, summary)
    except Exception as exc:
        print(f"[TELEGRAM] /summary error: {exc}", file=sys.stderr)
        await _reply_plain(update, "⚠️ Özet oluşturulamadı.")


# ── /stats ─────────────────────────────────────────────────────────────────
async def cmd_stats(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    try:
        from harun_site.utils.data_manager import load_chat_logs
        from harun_site.telegram_bot.notifier import load_watchlist
        logs = load_chat_logs()
        today_str = date.today().isoformat()
        today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
        total_msgs = sum(l.get("message_count", 0) for l in logs)
        today_msgs = sum(l.get("message_count", 0) for l in today_logs)
        watchlist = load_watchlist()
        await _reply_plain(
            update,
            f"📈 <b>İstatistikler</b>\n\n"
            f"📁 Toplam kayıt: <b>{len(logs)}</b>\n"
            f"💬 Toplam mesaj: <b>{total_msgs}</b>\n"
            f"👥 Bugünkü oturum: <b>{len(today_logs)}</b>\n"
            f"📩 Bugünkü mesaj: <b>{today_msgs}</b>\n"
            f"👀 Watchlist: {', '.join(watchlist) if watchlist else '—'}",
        )
    except Exception as exc:
        print(f"[TELEGRAM] /stats error: {exc}", file=sys.stderr)
        await _reply_plain(update, "⚠️ İstatistikler alınamadı.")


# ── /hot ───────────────────────────────────────────────────────────────────
async def cmd_hot(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    await _thinking(update, context)
    if _msg(update):
        await _msg(update).reply_text("🔍 Analiz ediliyor…")
    try:
        chat_id = update.effective_chat.id
        question = (
            "Son oturumlarda öne çıkan ilginç konuşmalar hangileri? "
            "Recruiter, hiring, derin teknik soru veya conversion sinyali olanları kısaca listele."
        )
        answer = await _run_analytics_query(chat_id, question)
        formatted_answer = format_markdown_to_tg_html(answer)
        await _reply(update, formatted_answer, parse_html=True)
    except Exception as exc:
        await _reply_error(update, exc, context="/hot")


# ── /panic ─────────────────────────────────────────────────────────────────
async def cmd_panic(update, context) -> None:
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
        groq_line = "✅ Groq erişilebilir" if groq_ok else "❌ Groq erişilemiyor / kota dolu olabilir"
        await _reply_plain(update, report + f"\n{groq_line}")
    except Exception as exc:
        print(f"[TELEGRAM] /panic error: {exc}", file=sys.stderr)
        await _reply_plain(update, "⚠️ Sağlık raporu alınamadı.")


# ── /watch ─────────────────────────────────────────────────────────────────
async def cmd_watch(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    args = context.args
    if not args:
        await _reply_plain(update, "Kullanım: /watch &lt;proje&gt;\nÖrnek: /watch cebirx")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_add
    if watch_add(project):
        await _reply_plain(update, f"✅ <b>{_escape_html(project)}</b> takibe alındı.")
    else:
        await _reply_plain(update, f"ℹ️ <b>{_escape_html(project)}</b> zaten takipte.")


# ── /unwatch ───────────────────────────────────────────────────────────────
async def cmd_unwatch(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    args = context.args
    if not args:
        await _reply_plain(update, "Kullanım: /unwatch &lt;proje&gt;")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_remove
    if watch_remove(project):
        await _reply_plain(update, f"🗑 <b>{_escape_html(project)}</b> takipten çıkarıldı.")
    else:
        await _reply_plain(update, f"ℹ️ <b>{_escape_html(project)}</b> takipte değildi.")


# ── /watchlist ─────────────────────────────────────────────────────────────
async def cmd_watchlist(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import load_watchlist
    wl = load_watchlist()
    if wl:
        items = "\n".join(f"• {_escape_html(p)}" for p in wl)
        await _reply_plain(update, f"👀 <b>Watchlist:</b>\n{items}")
    else:
        await _reply_plain(update, "👀 Watchlist boş.")


# ── /clear ─────────────────────────────────────────────────────────────────
async def cmd_clear(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.memory import clear_history
    clear_history(update.effective_chat.id)
    await _reply_plain(update, "🧹 Analiz sohbet geçmişi temizlendi.")


# ── Inline butonlar (callback) ─────────────────────────────────────────────
async def handle_callback(update, context) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if not _is_owner(update):
        return

    cmd = (query.data or "").replace("cmd:", "", 1)
    print(f"[TELEGRAM] Button: {cmd}", file=sys.stderr)

    if cmd == "sor_hint":
        await _reply_plain(
            update,
            "💬 Portfolyo ziyaretçi sohbeti:\n"
            "<code>/sor CebirX nedir?</code>\n\n"
            "Log analizi için doğrudan mesaj yaz.",
        )
        return

    dispatch = {
        "summary": cmd_summary,
        "stats": cmd_stats,
        "hot": cmd_hot,
        "panic": cmd_panic,
        "help": cmd_help,
        "clear": cmd_clear,
        "watchlist": cmd_watchlist,
        "ping": cmd_ping,
        "start": cmd_start,
    }
    handler = dispatch.get(cmd)
    if handler:
        await handler(update, context)
    else:
        await _reply_plain(update, f"⚠️ Bilinmeyen komut: {cmd}")


# ── Free-text → log analisti (admin panel ile aynı) ───────────────────────
async def handle_message(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    text = (update.message.text or "").strip()
    if not text:
        return

    print(f"[TELEGRAM] Free-text query: {text[:80]}", file=sys.stderr)
    await _thinking(update, context)
    status = None
    if _msg(update):
        status = await _msg(update).reply_text("🤔 Log analizi yapılıyor…")
    try:
        chat_id = update.effective_chat.id
        answer = await _run_analytics_query(chat_id, text)
        try:
            await status.delete()
        except Exception:
            pass
        formatted_answer = format_markdown_to_tg_html(answer)
        await _reply(update, formatted_answer, parse_html=True)
    except Exception as exc:
        await _reply_error(update, exc, context="message")
