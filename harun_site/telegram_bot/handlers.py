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
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Istanbul")
except Exception:
    _TZ = None


def _now() -> datetime:
    """Şimdiki zamanı İstanbul timezone'u ile döner."""
    return datetime.now(_TZ) if _TZ else datetime.now()


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


# ── Keyboard helper ────────────────────────────────────────────────────────
def _keyboard():
    """Mute durumuna göre doğru klavyeyi döner."""
    from harun_site.telegram_bot.keyboards import command_keyboard
    from harun_site.telegram_bot.notifier import is_muted
    return command_keyboard(muted=is_muted())


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


async def _reply_plain(update, text: str, *, with_keyboard: bool = True, reply_markup=None) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n…(kısaltıldı)"

    kwargs = {
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    elif with_keyboard:
        kwargs["reply_markup"] = _keyboard()
    await message.reply_text(text, **kwargs)


async def _reply(update, text: str, *, parse_html: bool = True, with_keyboard: bool = True) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>…(mesaj kısaltıldı)</i>"

    kwargs = {"disable_web_page_preview": True}
    if with_keyboard:
        kwargs["reply_markup"] = _keyboard()
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


async def _reply_multipart(update, text: str, *, chunk_size: int = 4000) -> None:
    """4096 karakter limitini aşan uzun metinleri parçalar halinde gönderir."""
    message = _msg(update)
    if not message:
        return
    parts = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    for i, part in enumerate(parts):
        kb = _keyboard() if i == len(parts) - 1 else None
        kwargs = {"parse_mode": "HTML", "disable_web_page_preview": True}
        if kb:
            kwargs["reply_markup"] = kb
        try:
            await message.reply_text(part, **kwargs)
        except Exception:
            plain = re.sub(r"<[^>]+>", "", part)
            await message.reply_text(plain[:chunk_size])


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
        "/help — tam komut rehberi\n"
        "Serbest metin — log analizi (admin asistanı)\n"
        "/sor &lt;mesaj&gt; — portfolyo chat simülasyonu",
    )


# ── /help ──────────────────────────────────────────────────────────────────
async def cmd_help(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import is_muted, get_mute_state
    mute_state = get_mute_state()
    mute_line = ""
    if mute_state["muted"]:
        if mute_state["until"] == -1:
            mute_line = "\n🔇 <b>Bildirimler: MUTE (açana kadar)</b>\n"
        else:
            from datetime import datetime as _dt
            until_dt = _dt.fromtimestamp(mute_state["until"], tz=_TZ) if _TZ else _dt.fromtimestamp(mute_state["until"])
            mute_line = f"\n🔇 <b>Bildirimler: MUTE (kadar: {until_dt.strftime('%H:%M')})</b>\n"

    await _reply_plain(
        update,
        f"📋 <b>Portföy Ops Bot — Komut Rehberi</b>{mute_line}\n"
        "📊 <b>ANALİZ</b>\n"
        "  /summary — Günlük rapor (oturum, mesaj, projeler, trendler)\n"
        "  /stats — Hızlı rakamlar (toplam / bugün)\n"
        "  /hot — AI ile ilginç oturumları bul (recruiter, hiring...)\n"
        "  /visitor — Ziyaretçi durumu + son sohbetler\n\n"
        "📖 <b>SOHBET</b>\n"
        "  /read — Son 5 sohbeti listele\n"
        "  /read 1 — En son sohbetin tam içeriği\n"
        "  /read 2 — 2. sohbetin içeriği (vb.)\n"
        "  /sor &lt;mesaj&gt; — Portfolyo chatını test et (ziyaretçi gibi)\n"
        "  /export — Tüm logları düz metin dosyası olarak al\n"
        "  /export today — Sadece bugünkü loglar\n"
        "  /export last5 — Son 5 sohbet\n\n"
        "🔧 <b>YÖNETİM</b>\n"
        "  /watch &lt;proje&gt; — Projeyi takibe al (konuşulunca bildirim gelir)\n"
        "  /unwatch &lt;proje&gt; — Takipten çıkar\n"
        "  /watchlist — Takipteki projeler\n"
        "  /newvisitor on/off — Yeni ziyaretçi bildirimini aç/kapat\n"
        "  /mute — Bildirimleri geçici sustur (süre seçersin)\n"
        "  /unmute — Bildirimleri hemen aç\n"
        "  /clear — Analiz sohbet geçmişini sil\n\n"
        "🩺 <b>SİSTEM</b>\n"
        "  /ping — Bot ayakta mı?\n"
        "  /panic — Sistem sağlık raporu + Groq durumu\n"
        "  /whoami — Telegram ID kontrolü (herkese açık)\n\n"
        "💬 <b>Serbest metin</b> → AI log analisti\n"
        "   <i>Örn: \"Bugün kim ne sordu?\" \"CebirX kaç kez geçti?\"</i>",
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
        from harun_site.utils.chat_enrich import finalize_project_references

        answer = await _run_portfolio_query(question)
        answer = finalize_project_references(answer, question)
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
        today_str = _now().date().isoformat()
        today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
        total_msgs  = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in logs)
        today_msgs  = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in today_logs)
        watchlist   = load_watchlist()
        await _reply_plain(
            update,
            f"📈 <b>İstatistikler</b>\n\n"
            f"📁 Toplam kayıt: <b>{len(logs)}</b>\n"
            f"💬 Toplam kullanıcı mesajı: <b>{total_msgs}</b>\n"
            f"👥 Bugünkü oturum: <b>{len(today_logs)}</b>\n"
            f"📩 Bugünkü kullanıcı mesajı: <b>{today_msgs}</b>\n"
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
        await _reply_plain(update, "👀 Watchlist boş.\n\nProje takibe almak için:\n<code>/watch cebirx</code>")


# ── /clear ─────────────────────────────────────────────────────────────────
async def cmd_clear(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.memory import clear_history
    clear_history(update.effective_chat.id)
    await _reply_plain(update, "🧹 Analiz sohbet geçmişi temizlendi.")


# ── /read — sohbet içeriğini oku ──────────────────────────────────────────
async def cmd_read(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages

    logs = load_chat_logs()
    if not logs:
        await _reply_plain(update, "📭 Henüz hiç sohbet kaydı yok.")
        return

    args = context.args
    # /read <numara> → belirli sohbeti göster
    if args:
        try:
            idx = int(args[0]) - 1
            if idx < 0 or idx >= len(logs):
                await _reply_plain(update, f"⚠️ Geçersiz numara. 1–{len(logs)} arasında bir değer gir.")
                return
        except ValueError:
            await _reply_plain(update, "Kullanım: /read veya /read 1")
            return

        log = logs[idx]
        messages = load_chat_log_messages(log["filename"])
        ts = log.get("timestamp", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(ts)
            if _TZ:
                dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
            ts_fmt = dt.strftime("%-d %B %Y, %H:%M") if sys.platform != "win32" else dt.strftime("%d %B %Y, %H:%M")
        except Exception:
            ts_fmt = ts[:16]

        user_count = sum(1 for m in messages if m.get("role") == "user")
        lines = [f"📖 <b>Sohbet #{idx+1}</b> — {ts_fmt}\n💬 {user_count} kullanıcı mesajı\n"]
        for m in messages:
            role = m.get("role", "")
            content = _escape_html(m.get("content", ""))[:600]
            if role == "user":
                lines.append(f"👤 {content}")
            elif role == "assistant":
                lines.append(f"🤖 {content}")
            lines.append("")

        full_text = "\n".join(lines)
        await _reply_multipart(update, full_text)
        return

    # /read → son 5 sohbeti listele
    display = logs[:5]
    lines = ["📖 <b>Son Sohbetler:</b>\n"]
    for i, log in enumerate(display, 1):
        ts = log.get("timestamp", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(ts)
            if _TZ:
                dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
            now = _now()
            if dt.date() == now.date():
                ts_fmt = dt.strftime("%H:%M")
            else:
                ts_fmt = "Dün " + dt.strftime("%H:%M") if (now.date() - dt.date()).days == 1 else dt.strftime("%d.%m %H:%M")
        except Exception:
            ts_fmt = ts[:16]

        user_count = log.get("user_message_count", log.get("message_count", 0) // 2)
        # Hiring sinyali varsa bayrak ekle
        flag = " 🔥" if user_count >= 8 else ""
        # İlk user mesajını önizle
        try:
            from harun_site.utils.data_manager import load_chat_log_messages as _lcm
            msgs = _lcm(log["filename"])
            first_msg = next((m.get("content", "") for m in msgs if m.get("role") == "user"), "")
            preview = _escape_html(first_msg[:60]) + ("…" if len(first_msg) > 60 else "")
        except Exception:
            preview = ""

        num_emoji = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣"][i-1]
        lines.append(f"{num_emoji} [{ts_fmt}] \"{preview}\" ({user_count} mesaj){flag}")

    lines.append(f"\n<i>Detay için: /read 1 … /read {len(display)}</i>")
    await _reply_plain(update, "\n".join(lines))


# ── /visitor — anlık ziyaretçi durumu ─────────────────────────────────────
async def cmd_visitor(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages

    logs = load_chat_logs()
    now = _now()
    today_str  = now.date().isoformat()
    week_start = (now.date().toordinal() - now.weekday())

    today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
    week_logs  = [
        l for l in logs
        if (l.get("timestamp") or "") >= today_str[:4]  # same year
        and _log_date_ordinal(l) >= week_start
    ]

    today_msgs = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in today_logs)
    week_msgs  = sum(l.get("user_message_count", l.get("message_count", 0) // 2) for l in week_logs)

    # En aktif gün bu hafta
    from collections import Counter
    day_counts: Counter = Counter()
    for l in week_logs:
        try:
            from datetime import date as _date
            d = _date.fromisoformat(l["timestamp"][:10])
            day_names = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]
            day_counts[day_names[d.weekday()]] += 1
        except Exception:
            pass
    busiest = max(day_counts, key=day_counts.get) if day_counts else "—"
    busiest_count = day_counts.get(busiest, 0)

    lines = [
        "👥 <b>Ziyaretçi Durumu</b>\n",
        f"📊 Bugün: <b>{len(today_logs)} oturum</b>, {today_msgs} mesaj",
        f"📈 Bu hafta: <b>{len(week_logs)} oturum</b>, {week_msgs} mesaj",
        f"🔥 En aktif gün: <b>{busiest}</b> ({busiest_count} oturum)" if busiest != "—" else "",
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
            ts_fmt = dt.strftime("%H:%M") if dt.date() == now.date() else dt.strftime("%d.%m %H:%M")
        except Exception:
            ts_fmt = ts[:16]
        uc = log.get("user_message_count", log.get("message_count", 0) // 2)
        flag = " 🚨" if uc >= 6 else ""
        try:
            from harun_site.utils.data_manager import load_chat_log_messages as _lcm
            msgs = _lcm(log["filename"])
            first = next((m.get("content","") for m in msgs if m.get("role") == "user"), "")
            preview = _escape_html(first[:50]) + ("…" if len(first) > 50 else "")
        except Exception:
            preview = ""
        lines.append(f"{i}. {ts_fmt} — \"{preview}\" ({uc} mesaj){flag}")

    await _reply_plain(update, "\n".join(l for l in lines if l is not None))


def _log_date_ordinal(log: dict) -> int:
    try:
        from datetime import date as _date
        return _date.fromisoformat(log["timestamp"][:10]).toordinal()
    except Exception:
        return 0


# ── /export — logları düz metin dosyası olarak gönder ─────────────────────
async def cmd_export(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages

    mode = (context.args[0].lower() if context.args else "all")
    logs = load_chat_logs()
    if not logs:
        await _reply_plain(update, "📭 Henüz hiç sohbet kaydı yok.")
        return

    # Filtrele
    if mode == "today":
        today_str = _now().date().isoformat()
        filtered = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
        if not filtered:
            await _reply_plain(update, "📭 Bugün hiç sohbet yok.")
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
        await status.reply_text(f"📤 {len(filtered)} sohbet hazırlanıyor…")

    # Dosya içeriği oluştur
    separator = "═" * 40
    thin_sep  = "─" * 40
    content_parts = [
        f"PORTFÖY SOHBET KAYITLARI",
        f"Oluşturulma: {_now().strftime('%d.%m.%Y %H:%M')} (İstanbul)",
        f"Toplam sohbet: {len(filtered)}",
        "",
    ]

    for i, log in enumerate(filtered, 1):
        ts = log.get("timestamp", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(ts)
            if _TZ:
                dt = dt.replace(tzinfo=_TZ) if dt.tzinfo is None else dt.astimezone(_TZ)
            ts_fmt = dt.strftime("%d %B %Y, %H:%M")
        except Exception:
            ts_fmt = ts[:16]

        messages = load_chat_log_messages(log["filename"])
        user_count = sum(1 for m in messages if m.get("role") == "user")

        content_parts += [
            separator,
            f"SOHBET #{i} — {ts_fmt}",
            f"Kullanıcı mesaj sayısı: {user_count}",
            separator,
            "",
        ]
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "").strip()
            if role == "user":
                content_parts.append(f"[Ziyaretçi]\n{content}")
            elif role == "assistant":
                content_parts.append(f"[Harun]\n{content}")
            content_parts.append("")
        content_parts.append(thin_sep)
        content_parts.append("")

    full_content = "\n".join(content_parts)
    filename = f"portfolio_sohbetler_{label}_{_now().strftime('%Y%m%d_%H%M')}.txt"

    try:
        from harun_site.telegram_bot.notifier import send_document_async
        await send_document_async(filename, full_content)
        # Küçük onay mesajı
        await _reply_plain(update, f"✅ <b>{len(filtered)}</b> sohbet dosya olarak gönderildi.")
    except Exception as exc:
        print(f"[TELEGRAM] /export error: {exc}", file=sys.stderr)
        await _reply_plain(update, "⚠️ Dosya gönderilemedi.")


# ── /mute ─────────────────────────────────────────────────────────────────
async def cmd_mute(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.keyboards import mute_duration_keyboard
    from harun_site.telegram_bot.notifier import is_muted, get_mute_state

    if is_muted():
        ms = get_mute_state()
        if ms["until"] == -1:
            current = "açana kadar"
        else:
            from datetime import datetime as _dt
            until_dt = _dt.fromtimestamp(ms["until"], tz=_TZ) if _TZ else _dt.fromtimestamp(ms["until"])
            current = f"{until_dt.strftime('%H:%M')}'e kadar"
        await _reply_plain(
            update,
            f"🔇 Bildirimler zaten susturulmuş ({current}).\n"
            "Değiştirmek için yeni süre seç:",
            reply_markup=mute_duration_keyboard(),
        )
    else:
        await _reply_plain(
            update,
            "🔇 <b>Bildirimleri ne kadar süre susturmak istiyorsun?</b>",
            reply_markup=mute_duration_keyboard(),
        )


# ── /unmute ────────────────────────────────────────────────────────────────
async def cmd_unmute(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import clear_mute
    clear_mute()
    await _reply_plain(update, "🔔 Bildirimler açıldı.")


# ── /newvisitor on|off ─────────────────────────────────────────────────────
async def cmd_newvisitor(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import (
        is_new_visitor_notify_enabled,
        set_new_visitor_notify,
    )
    args = context.args
    if not args:
        current = "✅ açık" if is_new_visitor_notify_enabled() else "🔕 kapalı"
        await _reply_plain(
            update,
            f"🆕 Yeni ziyaretçi bildirimi şu an: <b>{current}</b>\n\n"
            "Değiştirmek için:\n"
            "<code>/newvisitor on</code> — aç\n"
            "<code>/newvisitor off</code> — kapat",
        )
        return
    val = args[0].lower()
    if val in ("on", "aç", "1", "true"):
        set_new_visitor_notify(True)
        await _reply_plain(update, "✅ Yeni ziyaretçi bildirimi açıldı.")
    elif val in ("off", "kapat", "0", "false"):
        set_new_visitor_notify(False)
        await _reply_plain(update, "🔕 Yeni ziyaretçi bildirimi kapatıldı.")
    else:
        await _reply_plain(update, "Kullanım: /newvisitor on veya /newvisitor off")


# ── Inline butonlar (callback) ─────────────────────────────────────────────
async def handle_callback(update, context) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    if not _is_owner(update):
        return

    data = query.data or ""

    # ── Mute süresi seçimi ─────────────────────────────────────────────
    if data.startswith("mute:"):
        duration = data.split(":", 1)[1]  # "1h", "1d", "forever"
        from harun_site.telegram_bot.notifier import set_mute
        until = set_mute(duration)

        if duration == "1h":
            label = "1 saat"
        elif duration == "1d":
            label = "1 gün"
        else:
            label = "açana kadar"

        if until == -1:
            time_info = "süresiz"
        else:
            from datetime import datetime as _dt
            until_dt = _dt.fromtimestamp(until, tz=_TZ) if _TZ else _dt.fromtimestamp(until)
            time_info = f"otomatik açılma: {until_dt.strftime('%H:%M')}"

        await _reply_plain(
            update,
            f"🔇 Bildirimler <b>{label}</b> süreyle susturuldu.\n"
            f"⏰ {time_info}\n\n"
            "Bildirimleri açmak için: /unmute",
        )
        return

    # ── Komut butonları ────────────────────────────────────────────────
    cmd = data.replace("cmd:", "", 1)
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
        "summary":    cmd_summary,
        "stats":      cmd_stats,
        "hot":        cmd_hot,
        "panic":      cmd_panic,
        "help":       cmd_help,
        "clear":      cmd_clear,
        "watchlist":  cmd_watchlist,
        "ping":       cmd_ping,
        "start":      cmd_start,
        "visitor":    cmd_visitor,
        "read":       cmd_read,
        "export":     cmd_export,
        "mute":       cmd_mute,
        "unmute":     cmd_unmute,
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
