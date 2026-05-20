"""
harun_site/telegram_bot/memory.py
──────────────────────────────────
Persistent, per-session conversation memory for the Telegram admin bot.

Design decisions
────────────────
* JSON-backed so it survives bot restarts.
* Keyed by Telegram chat_id (int) so multi-device admins each get their own
  history (useful if you ever add a second admin device).
* Rolling window: keeps only the last MAX_TURNS user+assistant turn pairs to
  avoid bloating the Groq context.
* Atomic writes — reuses the same helper pattern as the rest of the codebase.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
MAX_TURNS: int = 10          # keep last N turn-pairs (user + assistant = 2 msgs)
_MEMORY_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "tg_memory.json"


# ── Atomic writer (mirrors data_manager._atomic_write_json) ────────────────
def _write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.stem + "_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load() -> dict[str, list[dict]]:
    """Return the full memory store (chat_id → message list)."""
    if not _MEMORY_FILE.exists():
        return {}
    try:
        return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ── Public API ─────────────────────────────────────────────────────────────

def get_history(chat_id: int) -> list[dict]:
    """Return the stored message history for *chat_id* (may be empty)."""
    store = _load()
    return store.get(str(chat_id), [])


def append_turn(chat_id: int, user_msg: str, assistant_msg: str) -> None:
    """Append a user/assistant turn and persist, trimming to MAX_TURNS pairs."""
    store = _load()
    key = str(chat_id)
    history: list[dict] = store.get(key, [])

    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": assistant_msg})

    # Rolling window: keep only the last MAX_TURNS * 2 messages
    max_msgs = MAX_TURNS * 2
    if len(history) > max_msgs:
        history = history[-max_msgs:]

    store[key] = history
    _write(_MEMORY_FILE, store)


def clear_history(chat_id: int) -> None:
    """Wipe conversation history for *chat_id*."""
    store = _load()
    store.pop(str(chat_id), None)
    _write(_MEMORY_FILE, store)
