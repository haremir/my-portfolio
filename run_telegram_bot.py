"""
run_telegram_bot.py
────────────────────
Standalone launcher for the Telegram admin ops bot.

Run this in a SEPARATE terminal from the Reflex app:

    python run_telegram_bot.py

Requirements in .env:
    TELEGRAM_BOT_TOKEN=<your-bot-token>
    TELEGRAM_ADMIN_ID=<your-telegram-user-id>

The bot NEVER shares a process or event loop with Reflex.
If the bot crashes, the portfolio site is unaffected.
"""

import sys
import os

# Ensure the project root is on sys.path so harun_site imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from harun_site.telegram_bot.bot import main
    main()
except KeyboardInterrupt:
    print("\n[TELEGRAM] Bot stopped by user.", file=sys.stderr)
except Exception as exc:
    print(f"[TELEGRAM] Fatal error: {exc}", file=sys.stderr)
    sys.exit(1)
