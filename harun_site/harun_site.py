import reflex as rx

# Import all pages to trigger @rx.page decorators
from harun_site.pages import (
    index,
    about,
    blog,
    blog_post,
    chat,
    admin,
)

app = rx.App(
	head_components=[
		rx.script(
			src=(
				"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700"
				"&family=JetBrains+Mono:wght@400;600&display=swap"
			)
		)
	]
)
