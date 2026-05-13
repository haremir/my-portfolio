import reflex as rx
from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.state.blog_state import BlogState
from harun_site.theme import (
	BG,
	BG_CARD,
	PRIMARY,
	TEXT,
	TEXT_MUTED,
	BORDER,
	GLOW_PRIMARY,
	FONT_SANS,
	FONT_MONO,
	ACCENT,
)


def blog_card(post: dict) -> rx.Component:
    return rx.link(
        rx.box(
            rx.cond(
                post["cover"] != "",
                rx.box(
                    rx.image(
                        src=post["cover"],
                        width="100%",
                        height="auto",
                        border_bottom=f"1px solid {BORDER}",
                    ),
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.text(
                    post["title"],
                    font_family=FONT_SANS,
                    font_weight="700",
                    color=TEXT,
                    font_size="1.2em",
                ),
                rx.text(
                    post["description"],
                    font_family=FONT_SANS,
                    color=TEXT_MUTED,
                    font_size="0.9em",
                    line_height="1.5",
                ),
                rx.hstack(
                    rx.foreach(
                        post["tags"],
                        lambda tag: rx.text(
                            tag,
                            color=ACCENT,
                            border=f"1px solid {ACCENT}44",
                            font_family=FONT_MONO,
                            font_size="0.7em",
                            padding="0.15em 0.5em",
                            border_radius="3px",
                        ),
                    ),
                    wrap="wrap",
                    style={"gap": "0.4em", "margin_top": "0.5em"},
                ),
                rx.spacer(),
                rx.text(
                    f"{post['day']} {post['month']} {post['year']}",
                    font_size="0.7em",
                    font_family=FONT_MONO,
                    color=TEXT_MUTED,
                    style={"text_transform": "uppercase", "margin_top": "0.8em", "opacity": "0.8"},
                ),
                padding="1.5em",
                align_items="start",
                gap="0.5em",
                flex="1",
            ),
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            overflow="hidden",
            margin_bottom="1.5em",
            cursor="pointer",
            transition="all 200ms",
            height="100%",
            display="flex",
            flex_direction="column",
            _hover={
                "border_color": PRIMARY,
                "box_shadow": f"0 4px 20px {PRIMARY}15",
                "transform": "translateY(-2px)",
            },
        ),
        href=f"/blog/{post['slug']}",
        text_decoration="none",
        width="100%",
        display="block",
    )


@rx.page(route="/blog", on_load=BlogState.on_load)
def blog_page() -> rx.Component:
	return rx.vstack(
		navbar(),
		rx.box(
			rx.vstack(
				rx.hstack(
					rx.text(
						"BLOG",
						font_family=FONT_MONO,
						font_size="0.75em",
						letter_spacing="0.2em",
						color=PRIMARY,
						text_shadow=GLOW_PRIMARY,
					),
					rx.hstack(
						rx.foreach(
							BlogState.all_tags,
							lambda tag: rx.button(
								tag,
								on_click=BlogState.toggle_tag(tag),
								font_family=FONT_MONO,
								font_size="0.72em",
								padding="0.2em 0.7em",
								border_radius="4px",
								cursor="pointer",
								transition="all 150ms",
								background=rx.cond(
									BlogState.selected_tags_str.contains(tag),
									PRIMARY,
									"transparent",
								),
								color=rx.cond(
									BlogState.selected_tags_str.contains(tag),
									BG,
									TEXT_MUTED,
								),
								border=rx.cond(
									BlogState.selected_tags_str.contains(tag),
									f"1px solid {PRIMARY}",
									f"1px solid {BORDER}",
								),
							),
						),
						rx.cond(
							BlogState.has_filter,
							rx.button(
								"✕ temizle",
								on_click=BlogState.clear_tags,
								font_family=FONT_MONO,
								font_size="0.72em",
								padding="0.2em 0.7em",
								border_radius="4px",
								background="transparent",
								color=ACCENT,
								border=f"1px solid {ACCENT}66",
								cursor="pointer",
								transition="all 150ms",
								_hover={"border_color": ACCENT, "color": ACCENT},
							),
							rx.fragment(),
						),
						wrap="wrap",
						style={"gap": "0.5em"},
					),
					justify="between",
					align="center",
					style={"margin_bottom": "1.5em"},
				),
				rx.box(
					rx.foreach(BlogState.filtered_posts, blog_card),
					display="grid",
					grid_template_columns=["1fr", "repeat(2, 1fr)", "repeat(3, 1fr)"],
					gap="1.5em",
					width="100%",
				),
				spacing="0",
				width="100%",
			),
			style={"max_width": "1100px", "margin": "0 auto", "padding": "8em 2em 3em 2em"},
			width="100%",
		),
		footer(),
		floating_chat(),
		min_height="100vh",
		width="100%",
		bg=BG,
	)