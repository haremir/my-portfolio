import reflex as rx
from harun_site.theme import APP_THEME

config = rx.Config(
    app_name="harun_site",
    db_url="sqlite:///reflex.db",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.RadixThemesPlugin(theme=APP_THEME),
    ],
)