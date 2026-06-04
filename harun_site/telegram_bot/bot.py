"""
harun_site/telegram_bot/bot.py
────────────────────────────────
Main Telegram bot entry point.

Startup sequence
────────────────
1. Validate TELEGRAM_BOT_TOKEN and TELEGRAM_ADMIN_ID from env.
2. Build the Application with the token.
3. Register all command and message handlers.
4. Start the scheduler as an asyncio background Task.
5. Run polling (blocking until interrupted).

Isolation guarantee
───────────────────
This module must NEVER be imported by Reflex pages or state classes.
It is only imported by run_telegram_bot.py (standalone process).
"""

from __future__ import annotations

import asyncio
import os
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from harun_site.telegram_bot.handlers import (
    cmd_clear,
    cmd_export,
    cmd_help,
    cmd_hot,
    cmd_mute,
    cmd_newvisitor,
    cmd_panic,
    cmd_ping,
    cmd_read,
    cmd_sor,
    cmd_start,
    cmd_stats,
    cmd_summary,
    cmd_unmute,
    cmd_unwatch,
    cmd_visitor,
    cmd_watch,
    cmd_watchlist,
    cmd_whoami,
    handle_callback,
    handle_message,
)
from harun_site.telegram_bot.notifier import send_notification_async
from harun_site.telegram_bot.scheduler import scheduler_loop


# ── Startup validation ─────────────────────────────────────────────────────
def _validate_env() -> tuple[str, int] | None:
    """
    Returns (token, admin_id) if valid, else None.
    Logs descriptive warnings — never raises.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

    if not token:
        print(
            "[TELEGRAM] WARNING: TELEGRAM_BOT_TOKEN is not set. "
            "Telegram bot will not start.",
            file=sys.stderr,
        )
        return None
    if not admin_id_str:
        print(
            "[TELEGRAM] WARNING: TELEGRAM_ADMIN_ID is not set. "
            "Bot would be open to everyone — refusing to start.",
            file=sys.stderr,
        )
        return None
    try:
        admin_id = int(admin_id_str)
    except ValueError:
        print(
            f"[TELEGRAM] WARNING: TELEGRAM_ADMIN_ID='{admin_id_str}' is not a valid integer.",
            file=sys.stderr,
        )
        return None

    return token, admin_id


# ── Post-init: send startup message + launch scheduler ─────────────────────
async def _post_init(application: Application) -> None:
    """Called by python-telegram-bot after Application is fully initialised."""
    admin_id_str = os.environ.get("TELEGRAM_ADMIN_ID", "")
    token        = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    # Webhook aktifse polling mesaj alamaz — sıfırla
    try:
        await application.bot.delete_webhook(drop_pending_updates=False)
        print("[TELEGRAM] Webhook cleared (polling mode).", file=sys.stderr)
    except Exception as exc:
        print(f"[TELEGRAM] delete_webhook warning: {exc}", file=sys.stderr)

    # Announce online status to owner
    if admin_id_str and token:
        try:
            admin_id = int(admin_id_str)
            await send_notification_async(
                "✅ <b>Portföy Ops Bot</b> başlatıldı.\n"
                "/help ile komutları görebilirsin."
            )
            print("[TELEGRAM] Startup message sent to owner.", file=sys.stderr)
        except Exception as exc:
            print(f"[TELEGRAM] Could not send startup message: {exc}", file=sys.stderr)

    # Create a send-function closure for the scheduler
    async def _send(text: str) -> None:
        await send_notification_async(text)

    # Launch scheduler as a background Task
    asyncio.create_task(scheduler_loop(_send))
    print("[TELEGRAM] Scheduler task created.", file=sys.stderr)


# ── Application builder ────────────────────────────────────────────────────
def build_application(token: str) -> Application:
    app = (
        Application.builder()
        .token(token)
        .post_init(_post_init)
        .build()
    )

    # Kurulum ve sağlık kontrolü
    app.add_handler(CommandHandler("whoami",      cmd_whoami))
    app.add_handler(CommandHandler("ping",        cmd_ping))
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("help",        cmd_help))

    # Analiz
    app.add_handler(CommandHandler("summary",     cmd_summary))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("hot",         cmd_hot))
    app.add_handler(CommandHandler("visitor",     cmd_visitor))

    # Sohbet okuma / export
    app.add_handler(CommandHandler("read",        cmd_read))
    app.add_handler(CommandHandler("export",      cmd_export))
    app.add_handler(CommandHandler("sor",         cmd_sor))

    # Watchlist
    app.add_handler(CommandHandler("watch",       cmd_watch))
    app.add_handler(CommandHandler("unwatch",     cmd_unwatch))
    app.add_handler(CommandHandler("watchlist",   cmd_watchlist))

    # Bildirim yönetimi
    app.add_handler(CommandHandler("mute",        cmd_mute))
    app.add_handler(CommandHandler("unmute",      cmd_unmute))
    app.add_handler(CommandHandler("newvisitor",  cmd_newvisitor))

    # Sistem
    app.add_handler(CommandHandler("panic",       cmd_panic))
    app.add_handler(CommandHandler("clear",       cmd_clear))

    # Inline keyboard → komutlar
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Free-text messages (non-command)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    return app


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> None:
    """Entry point called by run_telegram_bot.py."""
    from dotenv import load_dotenv
    load_dotenv(override=True)

    creds = _validate_env()
    if creds is None:
        print("[TELEGRAM] Bot not started (missing/invalid env vars).", file=sys.stderr)
        sys.exit(1)

    token, admin_id = creds
    print(f"[TELEGRAM] Starting bot. Owner ID: {admin_id}", file=sys.stderr)

    app = build_application(token)

    # run_polling is blocking and handles its own event loop
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,   # ignore any backlog from when bot was offline
    )
