"""
prod_start.py — Production entrypoint for Railway.
Starts Reflex backend + Telegram bot in parallel.
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def _terminate(proc, name):
    if proc is None or proc.poll() is not None:
        return
    print(f"[prod] Stopping {name}…", file=sys.stderr, flush=True)
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main():
    bot_proc = None
    reflex_proc = None

    # --- Telegram bot ---
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
    if token and admin_id:
        print("[prod] Starting Telegram bot…", file=sys.stderr, flush=True)
        bot_proc = subprocess.Popen(
            [sys.executable, str(ROOT / "run_telegram_bot.py")],
            cwd=str(ROOT),
        )
    else:
        print("[prod] TELEGRAM_BOT_TOKEN/ADMIN_ID not set — skipping bot.", file=sys.stderr, flush=True)

    # --- Reflex backend (production mode) ---
    port = os.environ.get("PORT", "8080")
    print(f"[prod] Starting Reflex on port {port}…", file=sys.stderr, flush=True)
    reflex_proc = subprocess.Popen(
        [
            sys.executable, "-m", "reflex", "run",
            "--env", "prod",
            "--backend-only",
            "--backend-port", port,
            "--backend-host", "0.0.0.0",
        ],
        cwd=str(ROOT),
    )

    def _shutdown(*_args):
        _terminate(reflex_proc, "Reflex")
        _terminate(bot_proc, "Telegram bot")
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while reflex_proc.poll() is None:
            time.sleep(1)
        print(f"[prod] Reflex exited with code {reflex_proc.returncode}", file=sys.stderr, flush=True)
    except KeyboardInterrupt:
        _shutdown()
    finally:
        _terminate(bot_proc, "Telegram bot")

    sys.exit(reflex_proc.returncode or 0)


if __name__ == "__main__":
    main()
