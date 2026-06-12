# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_reply.py
───────────────────────────────────────────
Reply helpers, formatting utilities, and the auth gate (_deny_if_not_owner).
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
    return datetime.now(_TZ) if _TZ else datetime.now()


def _keyboard():
    """Return InlineKeyboardMarkup respecting current mute state."""
    from harun_site.telegram_bot.keyboards import command_keyboard
    from harun_site.telegram_bot.notifier import is_muted
    return command_keyboard(muted=is_muted())


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_markdown_to_tg_html(text: str) -> str:
    """Convert basic markdown (**bold**, *italic*, `code`, [text](url)) to Telegram HTML."""
    if not text:
        return ""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    site_url = os.environ.get("SITE_URL", "http://localhost:3000").rstrip("/")

    def link_repl(m):
        label = m.group(1)
        url = m.group(2)
        if url.startswith("/"):
            url = site_url + url
        return f'<a href="{url}">{label}</a>'

    text = re.sub(r"\[(.*?)\]\((.*?)\)", link_repl, text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.*?)_", r"<i>\1</i>", text)
    text = re.sub(r"`(.*?)`", r"<code>\1</code>", text)
    return text


def _msg(update):
    return update.effective_message


async def _reply_plain(
    update,
    text: str,
    *,
    with_keyboard: bool = True,
    reply_markup=None,
) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n\u2026(k\u0131salt\u0131ld\u0131)"
    kwargs: dict = {"parse_mode": "HTML", "disable_web_page_preview": True}
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    elif with_keyboard:
        kwargs["reply_markup"] = _keyboard()
    await message.reply_text(text, **kwargs)


async def _reply(
    update,
    text: str,
    *,
    parse_html: bool = True,
    with_keyboard: bool = True,
) -> None:
    message = _msg(update)
    if not message:
        return
    if len(text) > 4000:
        text = text[:4000] + "\n\n<i>\u2026(mesaj k\u0131salt\u0131ld\u0131)</i>"
    kwargs: dict = {"disable_web_page_preview": True}
    if with_keyboard:
        kwargs["reply_markup"] = _keyboard()
    try:
        await message.reply_text(
            text, parse_mode="HTML" if parse_html else None, **kwargs
        )
    except Exception as exc:
        print(f"[TELEGRAM] HTML reply failed ({exc}), retrying plain.", file=sys.stderr)
        plain = re.sub(r"<[^>]+>", "", text) if parse_html else text
        await message.reply_text(plain[:4000], **kwargs)


async def _reply_multipart(update, text: str, *, chunk_size: int = 4000) -> None:
    """Split long text into Telegram-safe chunks and send each."""
    message = _msg(update)
    if not message:
        return
    parts = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    for i, part in enumerate(parts):
        kb = _keyboard() if i == len(parts) - 1 else None
        kwargs: dict = {"parse_mode": "HTML", "disable_web_page_preview": True}
        if kb:
            kwargs["reply_markup"] = kb
        try:
            await message.reply_text(part, **kwargs)
        except Exception:
            plain = re.sub(r"<[^>]+>", "", part)
            await message.reply_text(plain[:chunk_size])


async def _reply_error(update, exc: Exception, *, context: str) -> None:
    """Log exception and send a user-friendly error message."""
    from harun_site.telegram_bot.api_client import ReflexApiError
    from harun_site.utils.groq_client import is_rate_limit_error, user_message_for_groq_error

    print(f"[TELEGRAM] {context} error: {exc}", file=sys.stderr)
    if isinstance(exc, ReflexApiError):
        await _reply_plain(update, exc.user_message())
        return
    if not is_rate_limit_error(exc):
        traceback.print_exc()
    msg = user_message_for_groq_error(exc)
    await _reply_plain(update, _escape_html(msg))


async def _thinking(update, context) -> None:
    if update.effective_chat:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )


async def _deny_if_not_owner(update) -> bool:
    """Return True if caller is the owner; else send a hint and return False."""
    from harun_site.telegram_bot.handlers._auth import _is_owner, _user_id, _owner_id

    if _is_owner(update):
        return True
    uid = _user_id(update)
    allowed = _owner_id()
    if allowed is None:
        await _reply_plain(
            update,
            "\u26d4 TELEGRAM_ADMIN_ID .env dosyas\u0131nda tan\u0131ml\u0131 de\u011fil.\n"
            "Bot yan\u0131t veremez. /whoami ile kendi ID'ni \u00f6\u011frenip .env'e yaz.",
        )
    else:
        await _reply_plain(
            update,
            f"\u26d4 Bu bot sadece sahibine a\u00e7\u0131k.\n"
            f"Senin Telegram ID: <b>{uid}</b>\n"
            f".env \u2192 TELEGRAM_ADMIN_ID={uid}",
        )
    return False
