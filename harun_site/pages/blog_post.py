from __future__ import annotations

import reflex as rx
import markdown as md

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.theme import BG, BG_CARD, PRIMARY, TEXT, TEXT_MUTED, BORDER, FONT_SANS
from harun_site.utils.markdown_parser import get_post_by_slug


class BlogPostState(rx.State):
    post_title: str = ""
    post_date: str = ""
    post_content_html: str = ""
    post_tags: list[str] = []
    post_cover: str = ""
    not_found: bool = False
    is_loaded: bool = False

    def load_post(self):
        slug = self.router.url.path.rsplit("/", 1)[-1]
        post = get_post_by_slug(slug)
        if post is None:
            self.not_found = True
            self.post_title = ""
            self.post_date = ""
            self.post_content_html = ""
            self.post_tags = []
            self.post_cover = ""
            self.is_loaded = True
        else:
            self.not_found = False
            self.post_title = post.title
            
            months_tr = {
                "01": "Oca", "02": "Şub", "03": "Mar", "04": "Nis",
                "05": "May", "06": "Haz", "07": "Tem", "08": "Ağu",
                "09": "Eyl", "10": "Eki", "11": "Kas", "12": "Ara"
            }
            try:
                from datetime import datetime
                dt = datetime.strptime(post.date, "%Y-%m-%d")
                month_tr = months_tr.get(dt.strftime("%m"), dt.strftime("%b"))
                self.post_date = f"{dt.strftime('%d')} {month_tr} {dt.strftime('%Y')}"
            except Exception:
                self.post_date = post.date

            # Convert markdown to HTML on the backend
            raw_md = post.content or ""
            self.post_content_html = md.markdown(
                raw_md,
                extensions=["fenced_code", "tables", "nl2br"],
            )
            self.post_tags = post.tags
            self.post_cover = getattr(post, "cover", "")
            self.is_loaded = True


@rx.page(route="/blog/[slug]", on_load=BlogPostState.load_post)
def blog_post_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.cond(
                BlogPostState.not_found,
                rx.text("Yazi bulunamadi.", color=TEXT_MUTED),
                rx.vstack(
                    rx.heading(BlogPostState.post_title, size="8", color=PRIMARY),
                    rx.hstack(
                        rx.text(BlogPostState.post_date, color=TEXT_MUTED),
                        rx.hstack(
                            rx.foreach(
                                BlogPostState.post_tags,
                                lambda tag: rx.badge(
                                    tag,
                                    color=TEXT_MUTED,
                                    border=f"1px solid {BORDER}",
                                    background_color="transparent",
                                ),
                            ),
                            spacing="2",
                            wrap="wrap",
                        ),
                        spacing="3",
                        wrap="wrap",
                        align="center",
                    ),
                    rx.cond(
                        BlogPostState.post_cover != "",
                        rx.image(
                            src=BlogPostState.post_cover,
                            width="100%",
                            border_radius="12px",
                            margin_top="1em",
                            margin_bottom="2em",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        BlogPostState.is_loaded,
                        rx.html(BlogPostState.post_content_html),
                        rx.text("", color=TEXT_MUTED),
                    ),
                    spacing="4",
                    width="100%",
                ),
            ),
            style={"max_width": "800px", "margin": "0 auto", "padding": "6em 2em 3em 2em"},
            width="100%",
            flex="1",
        ),
        footer(),
        floating_chat(),
        min_height="100vh",
        width="100%",
        bg=BG,
        spacing="0",
    )

