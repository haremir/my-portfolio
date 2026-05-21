import os
import platform
from pathlib import Path
import reflex as rx
from harun_site.theme import APP_THEME

# Exclude directories containing runtime-written files to prevent hot-reload server restarts
exclude_paths = [
    "data",
    "posts",
    "assets/cv",
]
os.environ["REFLEX_HOT_RELOAD_EXCLUDE_PATHS"] = ":".join(exclude_paths)

config = rx.Config(
    app_name="harun_site",
    db_url="sqlite:///reflex.db",
    api_url="http://127.0.0.1:8004",
    backend_port=8004,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=APP_THEME),
    ],
)