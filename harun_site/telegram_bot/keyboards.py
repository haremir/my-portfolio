"""Inline command buttons — her bot yanıtının altında."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def command_keyboard(muted: bool = False) -> InlineKeyboardMarkup:
    """
    Ana komut klavyesi. *muted* True ise Mute butonu → Unmute'a dönüşür.
    Mute/Unmute durumu için bot handler'ı get_mute_state() ile doldurur.
    """
    mute_btn = (
        InlineKeyboardButton("🔔 Unmute", callback_data="cmd:unmute")
        if muted else
        InlineKeyboardButton("🔇 Mute",   callback_data="cmd:mute")
    )
    return InlineKeyboardMarkup(
        [
            # Satır 1 — En sık kullanılan analiz komutları
            [
                InlineKeyboardButton("📊 Özet",    callback_data="cmd:summary"),
                InlineKeyboardButton("📈 Stats",   callback_data="cmd:stats"),
                InlineKeyboardButton("👥 Visitor", callback_data="cmd:visitor"),
            ],
            # Satır 2 — Sohbet okuma / hot spots
            [
                InlineKeyboardButton("🔥 Hot",    callback_data="cmd:hot"),
                InlineKeyboardButton("📖 Read",   callback_data="cmd:read"),
                InlineKeyboardButton("📤 Export", callback_data="cmd:export"),
            ],
            # Satır 3 — Sistem / sağlık
            [
                InlineKeyboardButton("🩺 Panic",  callback_data="cmd:panic"),
                InlineKeyboardButton("📋 Help",   callback_data="cmd:help"),
                mute_btn,
            ],
            # Satır 4 — Watchlist + yönetim
            [
                InlineKeyboardButton("👀 Watchlist", callback_data="cmd:watchlist"),
                InlineKeyboardButton("🏓 Ping",      callback_data="cmd:ping"),
                InlineKeyboardButton("🧹 Clear",     callback_data="cmd:clear"),
            ],
            # Satır 5 — Portfolyo test
            [
                InlineKeyboardButton(
                    "💬 Portfolyo /sor",
                    callback_data="cmd:sor_hint",
                ),
            ],
        ]
    )


def mute_duration_keyboard() -> InlineKeyboardMarkup:
    """/mute komutu çağrıldığında gösterilen süre seçim klavyesi."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏱ 1 Saat",       callback_data="mute:1h"),
                InlineKeyboardButton("📅 1 Gün",        callback_data="mute:1d"),
                InlineKeyboardButton("🔕 Açana Kadar",  callback_data="mute:forever"),
            ],
        ]
    )
