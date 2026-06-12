# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/handlers/_auth.py
──────────────────────────────────────────
Low-level auth primitives.  No Telegram send calls here — zero circular deps.
"""
from __future__ import annotations

import os
import sys


def _owner_id() -> int | None:
    """Return the configured admin Telegram ID, or None if not set."""
    raw = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _user_id(update) -> int | None:
    """Return the Telegram user ID from an update, or None."""
    if update.effective_user:
        return update.effective_user.id
    return None


def _is_owner(update) -> bool:
    """Return True if the update's sender is the configured admin."""
    allowed = _owner_id()
    uid = _user_id(update)
    if allowed is None:
        print(
            "[TELEGRAM] TELEGRAM_ADMIN_ID not set \u2014 all handlers blocked.",
            file=sys.stderr,
        )
        return False
    if uid != allowed:
        print(
            f"[SECURITY] Unauthorised telegram user: {uid} "
            f"(expected TELEGRAM_ADMIN_ID={allowed})",
            file=sys.stderr,
        )
        return False
    return True
