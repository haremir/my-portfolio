import os
import reflex as rx
from harun_site.theme import APP_THEME

# Exclude directories containing runtime-written files to prevent hot-reload server restarts
# NOTE: data/, posts/, assets/cv, assets/blog are needed in production builds!
# The hot-reload exclusion only applies in dev mode; in production these dirs must exist.
exclude_paths: list[str] = []
os.environ["REFLEX_HOT_RELOAD_EXCLUDE_PATHS"] = ":".join(exclude_paths)


# Production: Railway (for Telegram bot) sets RAILWAY_PUBLIC_DOMAIN
railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
custom_domain = os.environ.get("SITE_DOMAIN", "")

if custom_domain:
    api_url = f"https://{custom_domain}"
elif railway_domain:
    api_url = f"https://{railway_domain}"
else:
    api_url = "http://127.0.0.1:8004"

backend_port = int(os.environ.get("PORT", "8004"))

config = rx.Config(
    app_name="harun_site",
    db_url="sqlite:///reflex.db",
    api_url=api_url,
    backend_port=backend_port,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=APP_THEME),
    ],
)