"""
prod_start.py — Railway entrypoint, sadece Telegram botu.
"""
import os
import sys
import signal
import subprocess
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

    if not token or not admin_id:
        print("[prod] TELEGRAM_BOT_TOKEN veya ADMIN_ID eksik, çıkılıyor.", file=sys.stderr)
        sys.exit(1)

    print("[prod] Telegram botu başlatılıyor...", file=sys.stderr, flush=True)
    bot_proc = subprocess.Popen(
        [sys.executable, str(ROOT / "run_telegram_bot.py")],
        cwd=str(ROOT),
    )

    def _shutdown(*_):
        if bot_proc.poll() is None:
            bot_proc.terminate()
            bot_proc.wait(timeout=10)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while bot_proc.poll() is None:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        _shutdown()

    sys.exit(bot_proc.returncode or 0)


if __name__ == "__main__":
    main()
