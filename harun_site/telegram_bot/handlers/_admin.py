# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_admin.py
───────────────────────────────────────────
Administrative and system management commands.

Commands: /whoami, /ping, /start, /help,
          /watch, /unwatch, /watchlist, /clear,
          /mute, /unmute, /newvisitor
"""
from __future__ import annotations

import sys

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Istanbul")
except Exception:
    _TZ = None

from harun_site.telegram_bot.handlers._auth import _owner_id, _user_id
from harun_site.telegram_bot.handlers._reply import (
    _deny_if_not_owner,
    _escape_html,
    _reply_plain,
)


# ── /whoami ────────────────────────────────────────────────────────────────
async def cmd_whoami(update, context) -> None:
    """Show current Telegram user ID (anyone can call)."""
    uid     = _user_id(update) or "?"
    allowed = _owner_id()
    if allowed and uid == allowed:
        match = "\u2705 Sahip ID ile e\u015fle\u015fiyor."
    elif allowed:
        match = f"\u26a0\ufe0f .env TELEGRAM_ADMIN_ID={allowed} \u2014 senin ID ile e\u015fle\u015fmiyor."
    else:
        match = "\u26a0\ufe0f TELEGRAM_ADMIN_ID hen\u00fcz tan\u0131ml\u0131 de\u011fil."
    await _reply_plain(update, f"\U0001f194 Telegram ID: <b>{uid}</b>\n{match}")


# ── /ping ──────────────────────────────────────────────────────────────────
async def cmd_ping(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    await _reply_plain(update, "\U0001f3d3 pong \u2014 bot ayakta.")


# ── /start ─────────────────────────────────────────────────────────────────
async def cmd_start(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    print("[TELEGRAM] /start from owner", file=sys.stderr)
    await _reply_plain(
        update,
        "\U0001f44b <b>Portf\u00f6y Ops Bot</b> haz\u0131r.\n\n"
        "/help \u2014 tam komut rehberi\n"
        "Serbest metin \u2014 log analizi (admin asistan\u0131)\n"
        "/sor &lt;mesaj&gt; \u2014 portfolyo chat sim\u00fclasyonu",
    )


# ── /help ──────────────────────────────────────────────────────────────────
async def cmd_help(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import get_mute_state

    mute_state = get_mute_state()
    mute_line  = ""
    if mute_state["muted"]:
        if mute_state["until"] == -1:
            mute_line = "\n\U0001f507 <b>Bildirimler: MUTE (a\u00e7ana kadar)</b>\n"
        else:
            from datetime import datetime as _dt
            until_dt = (
                _dt.fromtimestamp(mute_state["until"], tz=_TZ)
                if _TZ
                else _dt.fromtimestamp(mute_state["until"])
            )
            mute_line = (
                f"\n\U0001f507 <b>Bildirimler: MUTE (kadar: {until_dt.strftime('%H:%M')})</b>\n"
            )

    await _reply_plain(
        update,
        f"\U0001f4cb <b>Portf\u00f6y Ops Bot \u2014 Komut Rehberi</b>{mute_line}\n"
        "\U0001f4ca <b>ANAL\u0130Z</b>\n"
        "  /summary \u2014 G\u00fcnl\u00fck rapor (oturum, mesaj, projeler, trendler)\n"
        "  /stats \u2014 H\u0131zl\u0131 rakamlar (toplam / bug\u00fcn)\n"
        "  /hot \u2014 AI ile ilgin\u00e7 oturumlar\u0131 bul (recruiter, hiring...)\n"
        "  /visitor \u2014 Ziyaret\u00e7i durumu + son sohbetler\n\n"
        "\U0001f4d6 <b>SOHBET</b>\n"
        "  /read \u2014 Son 5 sohbeti listele\n"
        "  /read 1 \u2014 En son sohbetin tam i\u00e7eri\u011fi\n"
        "  /read 2 \u2014 2. sohbetin i\u00e7eri\u011fi (vb.)\n"
        "  /sor &lt;mesaj&gt; \u2014 Portfolyo chat\u0131n\u0131 test et (ziyaret\u00e7i gibi)\n"
        "  /export \u2014 T\u00fcm loglar\u0131 d\u00fcz metin dosyas\u0131 olarak al\n"
        "  /export today \u2014 Sadece bug\u00fcnk\u00fc loglar\n"
        "  /export last5 \u2014 Son 5 sohbet\n\n"
        "\U0001f527 <b>Y\u00d6NET\u0130M</b>\n"
        "  /watch &lt;proje&gt; \u2014 Projeyi takibe al (konu\u015fulunca bildirim gelir)\n"
        "  /unwatch &lt;proje&gt; \u2014 Takipten \u00e7\u0131kar\n"
        "  /watchlist \u2014 Takipteki projeler\n"
        "  /newvisitor on/off \u2014 Yeni ziyaret\u00e7i bildirimini a\u00e7/kapat\n"
        "  /mute \u2014 Bildirimleri ge\u00e7ici sustur (s\u00fcre se\u00e7ersin)\n"
        "  /unmute \u2014 Bildirimleri hemen a\u00e7\n"
        "  /clear \u2014 Analiz sohbet ge\u00e7mi\u015fini sil\n\n"
        "\U0001fa79 <b>S\u0130STEM</b>\n"
        "  /ping \u2014 Bot ayakta m\u0131?\n"
        "  /panic \u2014 Sistem sa\u011fl\u0131k raporu + Groq durumu\n"
        "  /whoami \u2014 Telegram ID kontrol\u00fc (herkese a\u00e7\u0131k)\n\n"
        "\U0001f4ac <b>Serbest metin</b> \u2192 AI log analisti\n"
        '   <i>\u00d6rn: "Bug\u00fcn kim ne sordu?" "CebirX ka\u00e7 kez ge\u00e7ti?"</i>',
    )


# ── /watch ─────────────────────────────────────────────────────────────────
async def cmd_watch(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    args = context.args
    if not args:
        await _reply_plain(update, "Kullan\u0131m: /watch &lt;proje&gt;\n\u00d6rnek: /watch cebirx")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_add
    if watch_add(project):
        await _reply_plain(update, f"\u2705 <b>{_escape_html(project)}</b> takibe al\u0131nd\u0131.")
    else:
        await _reply_plain(update, f"\u2139\ufe0f <b>{_escape_html(project)}</b> zaten takipte.")


# ── /unwatch ───────────────────────────────────────────────────────────────
async def cmd_unwatch(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    args = context.args
    if not args:
        await _reply_plain(update, "Kullan\u0131m: /unwatch &lt;proje&gt;")
        return
    project = " ".join(args).lower().strip()
    from harun_site.telegram_bot.notifier import watch_remove
    if watch_remove(project):
        await _reply_plain(
            update, f"\U0001f5d1 <b>{_escape_html(project)}</b> takipten \u00e7\u0131kar\u0131ld\u0131."
        )
    else:
        await _reply_plain(
            update, f"\u2139\ufe0f <b>{_escape_html(project)}</b> takipte de\u011fildi."
        )


# ── /watchlist ─────────────────────────────────────────────────────────────
async def cmd_watchlist(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import load_watchlist

    wl = load_watchlist()
    if wl:
        items = "\n".join(f"\u2022 {_escape_html(p)}" for p in wl)
        await _reply_plain(update, f"\U0001f440 <b>Watchlist:</b>\n{items}")
    else:
        await _reply_plain(
            update,
            "\U0001f440 Watchlist bo\u015f.\n\nProje takibe almak i\u00e7in:\n<code>/watch cebirx</code>",
        )


# ── /clear ─────────────────────────────────────────────────────────────────
async def cmd_clear(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.memory import clear_history
    clear_history(update.effective_chat.id)
    await _reply_plain(update, "\U0001f9f9 Analiz sohbet ge\u00e7mi\u015fi temizlendi.")


# ── /mute ──────────────────────────────────────────────────────────────────
async def cmd_mute(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.keyboards import mute_duration_keyboard
    from harun_site.telegram_bot.notifier import get_mute_state, is_muted

    if is_muted():
        ms = get_mute_state()
        if ms["until"] == -1:
            current = "a\u00e7ana kadar"
        else:
            from datetime import datetime as _dt
            until_dt = (
                _dt.fromtimestamp(ms["until"], tz=_TZ)
                if _TZ
                else _dt.fromtimestamp(ms["until"])
            )
            current = f"{until_dt.strftime('%H:%M')}'e kadar"
        await _reply_plain(
            update,
            f"\U0001f507 Bildirimler zaten susturulmu\u015f ({current}).\n"
            "De\u011fi\u015ftirmek i\u00e7in yeni s\u00fcre se\u00e7:",
            reply_markup=mute_duration_keyboard(),
        )
    else:
        await _reply_plain(
            update,
            "\U0001f507 <b>Bildirimleri ne kadar s\u00fcre susturmak istiyorsun?</b>",
            reply_markup=mute_duration_keyboard(),
        )


# ── /unmute ────────────────────────────────────────────────────────────────
async def cmd_unmute(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import clear_mute
    clear_mute()
    await _reply_plain(update, "\U0001f515 Bildirimler a\u00e7\u0131ld\u0131.")


# ── /newvisitor ────────────────────────────────────────────────────────────
async def cmd_newvisitor(update, context) -> None:
    if not await _deny_if_not_owner(update):
        return
    from harun_site.telegram_bot.notifier import (
        is_new_visitor_notify_enabled,
        set_new_visitor_notify,
    )

    args = context.args
    if not args:
        current = "\u2705 a\u00e7\u0131k" if is_new_visitor_notify_enabled() else "\U0001f515 kapal\u0131"
        await _reply_plain(
            update,
            f"\U0001f195 Yeni ziyaret\u00e7i bildirimi \u015fu an: <b>{current}</b>\n\n"
            "De\u011fi\u015ftirmek i\u00e7in:\n"
            "<code>/newvisitor on</code> \u2014 a\u00e7\n"
            "<code>/newvisitor off</code> \u2014 kapat",
        )
        return

    val = args[0].lower()
    if val in ("on", "a\u00e7", "1", "true"):
        set_new_visitor_notify(True)
        await _reply_plain(update, "\u2705 Yeni ziyaret\u00e7i bildirimi a\u00e7\u0131ld\u0131.")
    elif val in ("off", "kapat", "0", "false"):
        set_new_visitor_notify(False)
        await _reply_plain(update, "\U0001f515 Yeni ziyaret\u00e7i bildirimi kapat\u0131ld\u0131.")
    else:
        await _reply_plain(update, "Kullan\u0131m: /newvisitor on veya /newvisitor off")
