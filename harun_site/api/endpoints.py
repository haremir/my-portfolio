"""
harun_site/api/endpoints.py
─────────────────────────────
REST API endpoints exposed by the Reflex backend.

All endpoints return JSON.  The Telegram bot calls these to read
chat logs, statistics, projects, etc. from the Reflex Cloud instance.

Usage in harun_site.py or any state file:
    from harun_site.api import register_api_routes
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.applications import Starlette

from harun_site.utils.data_manager import (
    load_chat_logs,
    load_chat_log_messages,
    load_projects,
    load_suggestions,
    load_skills,
)

# ── Auth helper ──────────────────────────────────────────────────────────
# Simple shared secret token so the bot can prove it's the owner.
# Set TELEGRAM_API_SECRET on BOTH Railway AND Reflex Cloud to the same value.
_API_SECRET = os.environ.get("TELEGRAM_API_SECRET", "")

# Explicit opt-in to allow unauthenticated access (dev only).
# Set API_ALLOW_OPEN=true in .env for local development WITHOUT a secret.
# In production (Railway) this must NEVER be set — leave it unset.
_ALLOW_OPEN = os.environ.get("API_ALLOW_OPEN", "false").lower() == "true"


def _check_auth(request: Request) -> bool:
    """Return True if the request carries a valid Bearer token.

    Security policy:
      - If TELEGRAM_API_SECRET is set  → require matching Bearer token.
      - If secret is NOT set AND API_ALLOW_OPEN=true → allow (dev mode).
      - If secret is NOT set AND API_ALLOW_OPEN unset → BLOCK (secure default).
    """
    if not _API_SECRET:
        if _ALLOW_OPEN:
            if not hasattr(_check_auth, "_warned"):
                _check_auth._warned = True
                print(
                    "[API] ⚠️  TELEGRAM_API_SECRET not set — running in OPEN mode (API_ALLOW_OPEN=true).",
                    file=sys.stderr,
                )
            return True
        # Secure by default: block all requests when no secret is configured.
        if not hasattr(_check_auth, "_blocked_warned"):
            _check_auth._blocked_warned = True
            print(
                "[API] 🔒 TELEGRAM_API_SECRET not set — all /api/* requests blocked. "
                "Set TELEGRAM_API_SECRET or API_ALLOW_OPEN=true for dev.",
                file=sys.stderr,
            )
        return False
    auth = request.headers.get("Authorization", "")
    token = auth[len("Bearer "):].strip() if auth.startswith("Bearer ") else ""
    return token == _API_SECRET


# ── Route registration ───────────────────────────────────────────────────
def register_api_routes(app) -> None:
    """
    Register API routes on a Reflex App or bare FastAPI app.

    Reflex 0.9+ exposes the underlying FastAPI app as `app.api`.
    Call this AFTER `rx.App(…)` is constructed.
    """

    try:
        fastapi_app = getattr(app, "api", None)
        if fastapi_app is None:
            # Fallback: older Reflex versions stored it as app._api
            fastapi_app = getattr(app, "_api", None)
            if fastapi_app is None:
                # Fallback: check if the app itself has add_route (bare FastAPI/Starlette or test mocks)
                if hasattr(app, "add_route"):
                    fastapi_app = app
                else:
                    print(
                        "[API] ERROR: Cannot find underlying FastAPI app — "
                        "no API routes registered.",
                        file=sys.stderr,
                    )
                    return
    except Exception as exc:
        print(f"[API] ERROR accessing FastAPI app: {exc}", file=sys.stderr)
        return

    # ── Health check ──────────────────────────────────────────────────
    async def ping(request: Request):
        return JSONResponse({"ok": True, "service": "harun-site-api"})
    fastapi_app.add_route("/api/ping", ping, methods=["GET"])

    # ── Chat logs ─────────────────────────────────────────────────────
    async def chat_logs(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            logs = load_chat_logs()
            return JSONResponse(logs)
        except Exception as exc:
            return JSONResponse(
                {"error": str(exc)}, status_code=500,
            )
    fastapi_app.add_route("/api/chat-logs", chat_logs, methods=["GET"])

    async def chat_log_detail(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        filename = request.path_params.get("filename", "")
        if not filename or ".." in filename or "/" in filename:
            return JSONResponse({"error": "invalid filename"}, status_code=400)
        try:
            messages = load_chat_log_messages(filename)
            return JSONResponse({"filename": filename, "messages": messages})
        except Exception as exc:
            return JSONResponse(
                {"error": str(exc)}, status_code=500,
            )
    fastapi_app.add_route("/api/chat-logs/{filename}", chat_log_detail, methods=["GET"])

    # ── Stats ─────────────────────────────────────────────────────────
    async def stats(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            from datetime import datetime
            from harun_site.telegram_bot.notifier import load_watchlist

            logs = load_chat_logs()
            today_str = datetime.now().date().isoformat()
            today_logs = [l for l in logs if (l.get("timestamp") or "").startswith(today_str)]
            total_msgs = sum(
                l.get("user_message_count", l.get("message_count", 0) // 2)
                for l in logs
            )
            today_msgs = sum(
                l.get("user_message_count", l.get("message_count", 0) // 2)
                for l in today_logs
            )
            watchlist = load_watchlist()

            return JSONResponse({
                "total_sessions": len(logs),
                "today_sessions": len(today_logs),
                "total_user_messages": total_msgs,
                "today_user_messages": today_msgs,
                "watchlist": watchlist,
            })
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
    fastapi_app.add_route("/api/stats", stats, methods=["GET"])

    # ── Projects ──────────────────────────────────────────────────────
    async def projects(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            projs = load_projects()
            # Return only slug + name so the bot can resolve them
            return JSONResponse([
                {
                    "slug": p.get("slug", ""),
                    "name": p.get("name", p.get("title", "")),
                }
                for p in projs
            ])
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
    fastapi_app.add_route("/api/projects", projects, methods=["GET"])

    # ── Suggestions ───────────────────────────────────────────────────
    async def suggestions(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        lang = request.query_params.get("lang", "tr")
        try:
            sugs = load_suggestions(lang)
            return JSONResponse(sugs)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
    fastapi_app.add_route("/api/suggestions", suggestions, methods=["GET"])

    # ── Skills ────────────────────────────────────────────────────────
    async def skills(request: Request):
        if not _check_auth(request):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        try:
            s = load_skills()
            return JSONResponse(s)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
    fastapi_app.add_route("/api/skills", skills, methods=["GET"])

    print(
        "[API] \u2705 Routes registered: "
        "/api/ping, /api/chat-logs, /api/stats, "
        "/api/projects, /api/suggestions, /api/skills",
        file=sys.stderr,
    )