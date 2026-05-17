import reflex as rx

from harun_site.pages.index import index
from harun_site.state.index_state import IndexState

# Import all pages so their routes are registered.
from harun_site.pages import (
    about,
    blog,
    blog_post,
    chat,
    admin,
    portfolio,
)
from harun_site import models
from harun_site.theme import APP_THEME

app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
    ],
    head_components=[
        rx.script(
            src=(
                "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700"
                "&family=JetBrains+Mono:wght@400;600&display=swap"
            )
        )
    ]
)

app.add_page(index, route="/", on_load=IndexState.on_load)
