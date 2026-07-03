import os
import reflex as rx
from harun_site.theme import APP_THEME

# Exclude directories containing runtime-written files to prevent hot-reload server restarts
# NOTE: data/, posts/, assets/cv, assets/blog are needed in production builds!
# The hot-reload exclusion only applies in dev mode; in production these dirs must exist.
exclude_paths: list[str] = []
os.environ["REFLEX_HOT_RELOAD_EXCLUDE_PATHS"] = ":".join(exclude_paths)


import sys

# Determine the API URL: Check environment variables first (Reflex Cloud sets REFLEX_API_URL or API_URL)
api_url = os.environ.get("REFLEX_API_URL") or os.environ.get("API_URL")

if not api_url:
    # If compiling during 'reflex deploy' or 'reflex export', use the production backend URL on Reflex Cloud
    if any(arg in sys.argv for arg in ["deploy", "export"]):
        api_url = "https://7be2c768-4224-4737-8cbe-bca20c8477e9.fly.dev"
    else:
        railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
        custom_domain = os.environ.get("SITE_DOMAIN", "")

        if custom_domain:
            api_url = f"https://{custom_domain}"
        elif railway_domain:
            api_url = f"https://{railway_domain}"
        else:
            api_url = "http://127.0.0.1:8004"

# Backend port: use PORT env var if set (Reflex Cloud sets this), otherwise
# default to 8000 (Reflex's standard default, which Caddy reverse proxy expects).
# For local dev, set PORT=8004 in .env or override via command line.
backend_port = int(os.environ.get("PORT", "8000"))

config = rx.Config(
    app_name="harun_site",
    db_url="sqlite:///reflex.db",
    api_url=api_url,
    backend_port=backend_port,
    cors_allowed_origins=[
        "https://harunemirhan-gray-orca.reflex.run",
        "https://7be2c768-4224-4737-8cbe-bca20c8477e9.fly.dev",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8004",
        "http://127.0.0.1:8004",
    ],
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=APP_THEME),
    ],
)