import reflex as rx

from harun_site.theme import (
    BORDER,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    GLOW_PRIMARY,
    FONT_MONO,
    FONT_SANS,
)


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.link(
                rx.text(
                    "harun.",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    style={"font_size": "1.2em", "font_weight": "700", "letter_spacing": "-0.5px"},
                    text_shadow=GLOW_PRIMARY,
                ),
                href="/",
                _hover={"text_decoration": "none"},
            ),
            rx.spacer(),
            rx.hstack(
                rx.link(
                    "Ana Sayfa",
                    href="/",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "font_weight": "500"},
                    transition="color 150ms",
                    _hover={"color": TEXT, "text_decoration": "none"},
                ),
                rx.link(
                    "Hakkımda",
                    href="/about",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "font_weight": "500"},
                    transition="color 150ms",
                    _hover={"color": TEXT, "text_decoration": "none"},
                ),
                rx.link(
                    "Blog",
                    href="/blog",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "font_weight": "500"},
                    transition="color 150ms",
                    _hover={"color": TEXT, "text_decoration": "none"},
                ),
                rx.link(
                    "Chat",
                    href="/chat",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "font_weight": "500"},
                    transition="color 150ms",
                    _hover={"color": TEXT, "text_decoration": "none"},
                ),
                align="center",
                style={"gap": "1.5em"},
            ),
            width="100%",
            align="center",
            padding="0.8em 1.5em",
            background_color="#050d0fcc",
            border=f"1px solid {BORDER}",
            border_radius="20px",
            box_shadow="0 4px 30px rgba(0, 0, 0, 0.1)",
            style={"backdrop_filter": "blur(12px)"},
        ),
        position="fixed",
        top="1em",
        left="0",
        right="0",
        z_index="100",
        width="100%",
        style={"max_width": "800px", "margin": "0 auto", "padding": "0 1em"},
    )