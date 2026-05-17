import reflex as rx

from harun_site.theme import BG, BORDER, PRIMARY, TEXT_MUTED, FONT_MONO


def footer() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(
                "© 2026 Harun Emirhan Bostancı",
                font_family=FONT_MONO,
                font_size="0.75em",
                color=TEXT_MUTED,
            ),
            rx.hstack(
                rx.link(
                    "GitHub",
                    href="https://github.com/haremir",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                rx.link(
                    "LinkedIn",
                    href="https://linkedin.com/in/haremir826",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                rx.link(
                    "Email",
                    href="mailto:harunemirhan826@gmail.com",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                style={"gap": "1.5em"},
            ),
            justify="between",
            align="center",
            style={"max_width": "1100px", "margin": "0 auto", "width": "100%"},
            width="100%",
        ),
        background=f"{BG}aa",
        backdrop_filter="blur(10px)",
        border_top=f"1px solid {BORDER}",
        padding="1.5em 3em",
        width="100%",
        margin_top="auto",
    )