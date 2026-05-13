import reflex as rx

from harun_site.pages.index import index_page
from harun_site.pages.about import about_page
from harun_site.pages import blog, blog_post, chat


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
app.add_page(index_page, route="/")
app.add_page(about_page, route="/about")
