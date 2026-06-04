"""Tek komutla Reflex + Telegram bot — `uv run site`"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _popen(cmd: list[str]) -> subprocess.Popen:
    kwargs: dict = {"cwd": str(ROOT), "env": os.environ.copy()}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(cmd, **kwargs)


def _terminate(proc: subprocess.Popen | None, name: str) -> None:
    if proc is None or proc.poll() is not None:
        return
    print(f"[dev] Stopping {name}…", file=sys.stderr)
    if sys.platform == "win32":
        try:
            # On Windows, kill the process tree recursively using taskkill to prevent orphaned Vite/backend processes
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            proc.terminate()
    else:
        proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            proc.kill()
        proc.wait(timeout=3)


def run_all(*, with_bot: bool = True) -> int:
    from dotenv import load_dotenv
    import time

    load_dotenv(ROOT / ".env", override=True)

    bot_proc: subprocess.Popen | None = None
    reflex_proc: subprocess.Popen | None = None

    if with_bot:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        admin_id = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
        if not token or not admin_id:
            print(
                "[dev] WARNING: TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_ID eksik — "
                "sadece Reflex başlatılıyor.",
                file=sys.stderr,
            )
            with_bot = False
        else:
            print("[dev] Telegram bot başlatılıyor…", file=sys.stderr)
            bot_proc = _popen([sys.executable, str(ROOT / "run_telegram_bot.py")])

    print("[dev] Reflex başlatılıyor…", file=sys.stderr)
    reflex_proc = _popen(["uv", "run", "reflex", "run"])

    def _shutdown(*_args):
        _terminate(reflex_proc, "Reflex")
        _terminate(bot_proc, "Telegram bot")
        sys.exit(0)

    if sys.platform != "win32":
        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

    try:
        # On Windows, wait() blocks KeyboardInterrupt, so we poll and sleep instead
        while reflex_proc.poll() is None:
            time.sleep(0.5)
        return reflex_proc.returncode
    except KeyboardInterrupt:
        _shutdown()
        return 0
    finally:
        _terminate(bot_proc, "Telegram bot")


def main() -> None:
    parser = argparse.ArgumentParser(description="Portfolio dev — site + bot")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run"],
    )
    parser.add_argument("--no-bot", action="store_true")
    args = parser.parse_args()
    if args.command == "run":
        raise SystemExit(run_all(with_bot=not args.no_bot))


if __name__ == "__main__":
    main()
