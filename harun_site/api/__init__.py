"""
harun_site/api/__init__.py
──────────────────────────
REST API endpoints for the Telegram bot to consume.

These endpoints expose chat logs, statistics, projects, and other
data that the bot (running on Railway) needs to read from the
Reflex Cloud deployment.
"""
from harun_site.api.endpoints import register_api_routes

__all__ = ["register_api_routes"]