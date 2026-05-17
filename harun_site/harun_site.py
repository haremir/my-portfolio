import reflex as rx

from harun_site.pages.index import index
from harun_site.pages.blog import blog
from harun_site.pages.blog_post import blog_post
from harun_site.pages.about import about
from harun_site.pages.chat import chat
from harun_site.pages.admin import admin
from harun_site.pages.portfolio import portfolio
from harun_site.state.index_state import IndexState
from harun_site.state.blog_state import BlogState
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
app.add_page(about, route="/about")
app.add_page(portfolio, route="/portfolio")
app.add_page(blog, route="/blog", on_load=BlogState.on_load)
app.add_page(blog_post, route="/blog/[slug]")
app.add_page(chat, route="/chat")
app.add_page(admin, route="/admin")
