# -*- coding: utf-8 -*-
"""
harun_site/telegram_bot/api_client.py
──────────────────────────────────────
HTTP client for the Reflex Cloud REST API endpoints.

Used by Telegram bot handlers to read chat logs, stats, projects, etc.
When the bot runs on Railway, it calls the Reflex Cloud API instead of
reading local disk files.

Usage:
    from harun_site.telegram_bot.api_client import api_client
    logs = await api_client.get_chat_logs()

Error handling:
    All public methods return empty/default values on failure and log the
    reason to stderr.  Handlers should treat an empty result as a soft
    failure and show the user a friendly "API unavailable" message rather
    than crashing.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx


# ── Custom exception ────────────────────────────────────────────────────────
class ReflexApiError(Exception):
    """Raised when the Reflex API returns an error or is unreachable.

    Attributes:
        status_code: HTTP status code (0 if network-level failure).
        url: The endpoint URL that was called.
    """

    def __init__(self, message: str, *, status_code: int = 0, url: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.url = url

    def user_message(self) -> str:
        """Return a human-readable message suitable for Telegram replies."""
        if self.status_code == 401:
            return "\U0001f512 API yetkilendirme hatas\u0131 \u2014 TELEGRAM_API_SECRET kontrol et."
        if self.status_code == 0:
            return "\U0001f6ab Reflex API'sine ula\u015f\u0131lamad\u0131 \u2014 REFLEX_API_URL kontrol et."
        return f"\u26a0\ufe0f API hatas\u0131 (HTTP {self.status_code}) \u2014 daha sonra tekrar dene."


# ── Client ──────────────────────────────────────────────────────────────────
class ReflexApiClient:
    """Async HTTP client for the Reflex Cloud REST API."""

    def __init__(self, base_url: str = "", secret: str = "") -> None:
        self.base_url = (base_url or os.environ.get(
            "REFLEX_API_URL", "http://localhost:3000"
        )).rstrip("/")
        self.secret = secret or os.environ.get("TELEGRAM_API_SECRET", "")
        self._headers = {"Authorization": f"Bearer {self.secret}"} if self.secret else {}

    async def _get(self, path: str) -> Any:
        """GET *path* and return parsed JSON.

        Returns the parsed body on HTTP 200.
        Raises ReflexApiError on auth failure (401) or server error (5xx).
        Returns None on any other failure (logged to stderr).
        """
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._headers)

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 401:
                raise ReflexApiError(
                    f"Unauthorised: {url}",
                    status_code=401,
                    url=url,
                )

            print(
                f"[API_CLIENT] {url} \u2192 HTTP {resp.status_code}: {resp.text[:200]}",
                file=sys.stderr,
            )
            return None

        except ReflexApiError:
            raise
        except httpx.ConnectError as exc:
            print(f"[API_CLIENT] Connection failed to {url}: {exc}", file=sys.stderr)
            raise ReflexApiError(
                f"Cannot connect to {self.base_url}",
                status_code=0,
                url=url,
            ) from exc
        except httpx.TimeoutException as exc:
            print(f"[API_CLIENT] Timeout calling {url}: {exc}", file=sys.stderr)
            raise ReflexApiError(
                f"Timeout calling {url}",
                status_code=0,
                url=url,
            ) from exc
        except Exception as exc:
            print(f"[API_CLIENT] Unexpected error calling {url}: {exc}", file=sys.stderr)
            return None

    # ── Public methods ──────────────────────────────────────────────────────
    async def ping(self) -> bool:
        """Return True if the API is reachable and healthy."""
        try:
            data = await self._get("/api/ping")
            return data is not None and data.get("ok") is True
        except ReflexApiError:
            return False

    async def get_chat_logs(self) -> list[dict]:
        """Fetch all chat log metadata. Returns [] on failure."""
        try:
            data = await self._get("/api/chat-logs")
            return data if isinstance(data, list) else []
        except ReflexApiError:
            raise
        except Exception as exc:
            print(f"[API_CLIENT] get_chat_logs error: {exc}", file=sys.stderr)
            return []

    async def get_chat_log_messages(self, filename: str) -> list[dict]:
        """Fetch messages for a specific chat log. Returns [] on failure."""
        if not filename:
            return []
        try:
            data = await self._get(f"/api/chat-logs/{filename}")
            if isinstance(data, dict):
                return data.get("messages", [])
            return []
        except ReflexApiError:
            raise
        except Exception as exc:
            print(f"[API_CLIENT] get_chat_log_messages({filename}) error: {exc}", file=sys.stderr)
            return []

    async def get_stats(self) -> dict:
        """Fetch aggregated stats. Returns {} on failure."""
        try:
            data = await self._get("/api/stats")
            return data if isinstance(data, dict) else {}
        except ReflexApiError:
            raise
        except Exception as exc:
            print(f"[API_CLIENT] get_stats error: {exc}", file=sys.stderr)
            return {}

    async def get_projects(self) -> list[dict]:
        """Fetch project list (slug + name only). Returns [] on failure."""
        try:
            data = await self._get("/api/projects")
            return data if isinstance(data, list) else []
        except ReflexApiError:
            raise
        except Exception as exc:
            print(f"[API_CLIENT] get_projects error: {exc}", file=sys.stderr)
            return []


# Singleton instance — imported everywhere in the bot package.
api_client = ReflexApiClient()