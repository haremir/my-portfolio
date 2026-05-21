"""
prod_start.py — Railway entrypoint: Telegram botu + healthcheck HTTP.

Railway /ping endpoint'ine HTTP isteği yaparak container'ın sağlıklı
olduğunu doğrular. Bu yüzden basit bir HTTP sunucusu çalıştırıyoruz.
"""
import os
import sys
import signal
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


# ── Minimal healthcheck HTTP server ──────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    """Responds to GET /ping with 200 OK for Railway healthcheck."""

    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"pong")
        else:
            self.send_response(404)
            self.end_headers()

    # Suppress request logs to keep output clean
    def log_message(self, format, *args):
        pass


def _start_health_server(port: int) -> HTTPServer:
    """Start the healthcheck server in a daemon thread."""
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[prod] Healthcheck server listening on 0.0.0.0:{port}/ping", file=sys.stderr, flush=True)
    return server


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    admin_id = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()

    if not token or not admin_id:
        print("[prod] TELEGRAM_BOT_TOKEN veya ADMIN_ID eksik, çıkılıyor.", file=sys.stderr)
        sys.exit(1)

    # Railway sets PORT env var — healthcheck server must listen on it
    port = int(os.environ.get("PORT", "8080"))

    # Start healthcheck HTTP server first so Railway can verify quickly
    health_server = _start_health_server(port)

    print("[prod] Telegram botu başlatılıyor...", file=sys.stderr, flush=True)
    bot_proc = subprocess.Popen(
        [sys.executable, str(ROOT / "run_telegram_bot.py")],
        cwd=str(ROOT),
    )

    def _shutdown(*_):
        health_server.shutdown()
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
