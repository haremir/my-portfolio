import reflex as rx

from harun_site.theme import APP_THEME


config = rx.Config(
    app_name="harun_site",
    frontend_port=3000,
    backend_port=8000,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
    ],
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=APP_THEME),
    ],
)