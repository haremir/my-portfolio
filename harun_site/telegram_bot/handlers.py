"""
harun_site/telegram_bot/handlers.py
─────────────────────────────────────
Telegram command and message handlers.

Each handler follows the same contract:
  async def handle_xxx(update, context) -> None

All handlers silently no-op for non-authorised users (auth checked first).

Reuses:
  • answer_admin_chat_about_logs() — exact same pipeline as admin panel
  • load_chat_logs() / load_chat_log_messages() — no duplication
  • memory.get_history() / append_turn() — persistent per-session context
  • scheduler.build_daily_summary() / build_health_report()
"""

from __future__ import annotations

import os
import sys
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

# ── Auth helper ────────────────────────────────────────────────────────────
def _is_owner(update) -> bool:
    allowed_str = os.environ.get("TELEGRAM_ADMIN_ID", "")
    if not allowed_str:
        return False
    try:
        allowed_id = int(allowed_str)
    except ValueError:
        return False
    uid = update.effective_user.id if update.effective_user else None
    if uid != allowed_id:
        print(f"[TELEGRAM] Unauthorized access attempt from user_id={uid}", file=sys.stderr)
        return False
    return True


# ── Analytics bridge helpers ───────────────────────────────────────────────
async def _run_analytics_query(chat_id: int, question: str) -> str:
    """
    Run an admin analytics question through the SAME pipeline the admin panel uses.
    Maintains persistent per-session conversation history via memory module.
    """
    from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages
    from harun_site.utils.groq_client import answer_admin_chat_about_logs
    from harun_site.telegram_bot.memory import get_history, append_turn

    logs = load_chat_logs()
    payload = []
    for log in logs[:25]:
        messages = load_chat_log_messages(log["filename"])
        user_samples = [
            m.get("content", "")[:200]
            for m in messages if m.get("role") == "user"
        ][:5]
        assistant_samples = [
            m.get("content", "")[:120]
            for m in messages if m.get("role") == "assistant"
        ][:2]
        payload.append({
            "filename":        log["filename"],
            "timestamp":       log.get("timestamp", ""),
            "message_count":   log.get("message_count", 0),
            "user_samples":    user_samples,
            "assistant_samples": assistant_samples,
        })

    # Persistent conversation history
    history = get_history(chat_id)
    history_with_question = [*history, {"role": "user", "content": question}]

    answer = await answer_admin_chat_about_logs(history_with_question, payload)
    append_turn(chat_id, question, answer)
    return answer


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def _reply(update, text: str, parse_html: bool = True) -> None:
    """Safe reply — truncates at Telegram's 4096-char limit."""
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>…(mesaj kısaltıldı)</i>"
    await update.message.reply_text(
        text,
        parse_mode="HTML" if parse_html else None,
        disable_web_page_preview=True,
    )


# ── /start ─────────────────────────────────────────────────────────────────
async def cmd_start(update, context) -> None:
    if not _is_owner(update):
        return
    print("[TELEGRAM] /start from owner", file=sys.stderr)
    await _reply(update, (
        "👋 <b>Portföy Ops Bot</b> hazır.\n\n"
        "Komutlar için /help — ya da doğrudan soru sor."
    ))


# ── /help ──────────────────────────────────────────────────────────────────
async def cmd_help(update, context) -> None:
    if not _is_owner(update):
        return
    await _reply(update, (
        "📋 <b>Komutlar</b>\n\n"
        "/summary — Günlük özet\n"
        "/hot — Son ilginç oturumlar\n"
        "/panic — Sistem sağlık raporu\n"
        "/watch &lt;proje&gt; — Proje takibine ekle\n"
        "/unwatch &lt;proje&gt; — Proje takibinden çıkar\n"
        "/watchlist — Aktif takip listesi\n"
        "/clear — Konuşma geçmişini sıfırla\n"
        "/stats — Hızlı istatistikler\n\n"
        "💬 Veya doğrudan soru sor:\n"
        "<i>\"Bugün kim ne sordu?\", \"En uzun oturum hangisi?\", "
        "\"Recruiter sinyali var mı?\"</i>"
    ))


# ── /summary ───────────────────────────────────────────────────────────────
async def cmd_summary(update, context) -> None:
    if not _is_owner(update):
        return
    print("[TELEGRAM] /summary requested", file=sys.stderr)
    await update.message.reply_text("⏳ Özet hazırlanıyor…")
    try:
        from harun_site.telegram_bot.scheduler import build_daily_summary
        summary = await build_daily_summary()
        await _reply(update, summary)
    except Exception as exc:
        print(f"[TELEGRAM] /summary error: {exc}", file=sys.stderr)
        await _reply(update, "⚠️ Özet oluşturulamadı. Logları kontrol et.")


# ── /stats ─────────────────────────────────────────────────────────────────
async def cmd_stats(update, context) -> None:
    if not _is_owner(update):
        return
    print("[TELEGRAM] /stats requested", file=sys.stderr)
    try:
        from harun_site.utils.data_manager import load_chat_logs
        from harun_site.telegram_bot.notifier import load_watchlist
        logs = load_chat_logs()
        today_str = date.today().isoformat()
        today_logs    = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
        total_msgs    = sum(l.get("message_count", 0) for l in logs)
        today_msgs    = sum(l.get("message_count", 0) for l in today_logs)
        watchlist     = load_watchlist()
        text = (
            f"📈 <b>İstatistikler</b>\n\n"
            f"📁 Toplam kayıt: <b>{len(logs)}</b>\n"
            f"💬 Toplam mesaj: <b>{total_msgs}</b>\n"
            f"👥 Bugünkü oturum: <b>{len(today_logs)}</b>\n"
            f"📩 Bugünkü mesaj: <b>{today_msgs}</b>\n"
            f"👀 Watchlist: {', '.join(watchlist) if watchlist else '—'}"
        )
        await _reply(update, text)
    except Exception as exc:
        print(f"[TELEGRAM] /stats error: {exc}", file=sys.stderr)
        await _reply(update, "⚠️ İstatistikler alınamadı.")


# ── /hot ───────────────────────────────────────────────────────────────────
async def cmd_hot(update, context) -> None:
    if not _is_owner(update):
        return
    print("[TELEGRAM] /hot requested", file=sys.stderr)
    await update.message.reply_text("🔍 En ilginç oturumlar analiz ediliyor…")
    try:
        chat_id = update.effective_chat.id
        question = (
            "Son oturumlarda öne çıkan ilginç konuşmalar hangileri? "
            "İşe alım sinyali, derin teknik soru veya olağandışı ilgi göster. "
            "Her biri için kısaca: ne soruldu, neden dikkat çekici."
        )
        answer = await _run_analytics_query(chat_id, question)
        await _reply(update, answer)
    except Exception as exc:
        print(f"[TELEGRAM] /hot error: {exc}", file=sys.stderr)
        await _reply(update, "⚠️ Analiz başarısız oldu.")


# ── /panic ─────────────────────────────────────────────────────────────────
async def cmd_panic(update, context) -> None:
    if not _is_owner(update):
        return
    print("[TELEGRAM] /panic requested", file=sys.stderr)
    try:
        from harun_site.telegram_bot.scheduler import build_health_report
        report = await build_health_report()

        # Groq reachability check
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

        groq_line = "✅ Groq API erişilebilir" if groq_ok else "❌ Groq API erişilemiyor"
        full = report + f"\n{groq_line}"
        await _reply(update, full)
    except Exception as exc:
        print(f"[TELEGRAM] /panic error: {exc}", file=sys.stderr)
        await _reply(update, "⚠️ Sağlık raporu alınamadı.")


# ── /watch ─────────────────────────────────────────────────────────────────
async def cmd_watch(update, context) -> None:
    if not _is_owner(update):
        return
    args = context.args
    if not args:
        await _reply(update, "Kullanım: /watch &lt;proje-adı&gt;\nÖrnek: /watch dentbot")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_add
    added = watch_add(project)
    if added:
        print(f"[WATCH] Added: {project}", file=sys.stderr)
        await _reply(update, f"✅ <b>{_escape_html(project)}</b> takibe alındı.")
    else:
        await _reply(update, f"ℹ️ <b>{_escape_html(project)}</b> zaten takipte.")


# ── /unwatch ───────────────────────────────────────────────────────────────
async def cmd_unwatch(update, context) -> None:
    if not _is_owner(update):
        return
    args = context.args
    if not args:
        await _reply(update, "Kullanım: /unwatch &lt;proje-adı&gt;")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_remove
    removed = watch_remove(project)
    if removed:
        print(f"[WATCH] Removed: {project}", file=sys.stderr)
        await _reply(update, f"🗑 <b>{_escape_html(project)}</b> takipten çıkarıldı.")
    else:
        await _reply(update, f"ℹ️ <b>{_escape_html(project)}</b> takipte değildi.")


# ── /watchlist ─────────────────────────────────────────────────────────────
async def cmd_watchlist(update, context) -> None:
    if not _is_owner(update):
        return
    from harun_site.telegram_bot.notifier import load_watchlist
    wl = load_watchlist()
    if wl:
        items = "\n".join(f"• {_escape_html(p)}" for p in wl)
        await _reply(update, f"👀 <b>Aktif Watchlist:</b>\n{items}")
    else:
        await _reply(update, "👀 Watchlist boş. /watch &lt;proje&gt; ile ekle.")


# ── /clear ─────────────────────────────────────────────────────────────────
async def cmd_clear(update, context) -> None:
    if not _is_owner(update):
        return
    from harun_site.telegram_bot.memory import clear_history
    clear_history(update.effective_chat.id)
    await _reply(update, "🧹 Konuşma geçmişi temizlendi.")


# ── Free-text message (AI analytics query) ─────────────────────────────────
async def handle_message(update, context) -> None:
    if not _is_owner(update):
        return
    text = (update.message.text or "").strip()
    if not text:
        return

    print(f"[TELEGRAM] Free-text query: {text[:80]}", file=sys.stderr)
    await update.message.reply_text("🤔 Analiz ediliyor…")
    try:
        chat_id = update.effective_chat.id
        answer = await _run_analytics_query(chat_id, text)
        await _reply(update, answer)
    except Exception as exc:
        print(f"[TELEGRAM] Message handler error: {exc}", file=sys.stderr)
        await _reply(update, "⚠️ Sorgu işlenirken bir hata oluştu.")
