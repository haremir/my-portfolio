"""Inline command buttons — her bot yanıtının altında."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def command_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Özet", callback_data="cmd:summary"),
                InlineKeyboardButton("📈 Stats", callback_data="cmd:stats"),
                InlineKeyboardButton("🔥 Hot", callback_data="cmd:hot"),
            ],
            [
                InlineKeyboardButton("🩺 Panic", callback_data="cmd:panic"),
                InlineKeyboardButton("📋 Help", callback_data="cmd:help"),
                InlineKeyboardButton("🧹 Clear", callback_data="cmd:clear"),
            ],
            [
                InlineKeyboardButton("👀 Watchlist", callback_data="cmd:watchlist"),
                InlineKeyboardButton("🏓 Ping", callback_data="cmd:ping"),
            ],
            [
                InlineKeyboardButton(
                    "💬 Portfolyo /sor",
                    callback_data="cmd:sor_hint",
                ),
            ],
        ]
    )
