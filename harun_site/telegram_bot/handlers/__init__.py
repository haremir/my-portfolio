# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/__init__.py
─────────────────────────────────────────────
Public API of the handlers package.

Re-exports every symbol that bot.py (and any future caller) needs so that:
    from harun_site.telegram_bot.handlers import cmd_stats, handle_callback
continues to work without modification after the package refactor.
"""
from __future__ import annotations

# Auth helpers (used externally only for _is_owner, kept for compat)
from harun_site.telegram_bot.handlers._auth import (
    _is_owner,
    _owner_id,
    _user_id,
)

# Reply / formatting helpers
from harun_site.telegram_bot.handlers._reply import (
    _deny_if_not_owner,
    _escape_html,
    _keyboard,
    _msg,
    _now,
    _reply,
    _reply_error,
    _reply_multipart,
    _reply_plain,
    _thinking,
    format_markdown_to_tg_html,
)

# Analytics commands
from harun_site.telegram_bot.handlers._analytics import (
    _build_log_payload,
    _run_analytics_query,
    _run_portfolio_query,
    cmd_hot,
    cmd_panic,
    cmd_stats,
    cmd_summary,
    cmd_visitor,
)

# Chat-log commands
from harun_site.telegram_bot.handlers._chat import (
    cmd_export,
    cmd_read,
    cmd_sor,
)

# Administrative commands
from harun_site.telegram_bot.handlers._admin import (
    cmd_clear,
    cmd_help,
    cmd_mute,
    cmd_newvisitor,
    cmd_ping,
    cmd_start,
    cmd_unmute,
    cmd_unwatch,
    cmd_watch,
    cmd_watchlist,
    cmd_whoami,
)

# Dispatcher
from harun_site.telegram_bot.handlers._dispatch import (
    handle_callback,
    handle_message,
)

__all__ = [
    # Auth
    "_is_owner", "_owner_id", "_user_id",
    # Reply
    "_deny_if_not_owner", "_escape_html", "_keyboard", "_msg", "_now",
    "_reply", "_reply_error", "_reply_multipart", "_reply_plain",
    "_thinking", "format_markdown_to_tg_html",
    # Analytics
    "_build_log_payload", "_run_analytics_query", "_run_portfolio_query",
    "cmd_hot", "cmd_panic", "cmd_stats", "cmd_summary", "cmd_visitor",
    # Chat
    "cmd_export", "cmd_read", "cmd_sor",
    # Admin
    "cmd_clear", "cmd_help", "cmd_mute", "cmd_newvisitor", "cmd_ping",
    "cmd_start", "cmd_unmute", "cmd_unwatch", "cmd_watch", "cmd_watchlist",
    "cmd_whoami",
    # Dispatch
    "handle_callback", "handle_message",
]
