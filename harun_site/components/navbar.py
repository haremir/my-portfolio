import reflex as rx
from harun_site.theme import BG, BORDER, PRIMARY, TEXT, FONT_MONO, GLOW_PRIMARY

def navbar() -> rx.Component:
    return rx.center(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.text(
                        "HARUN",
                        font_family=FONT_MONO,
                        font_weight="700",
                        font_size="1em",
                        color=TEXT,
                    ),
                    rx.text(
                        ".",
                        font_family=FONT_MONO,
                        font_weight="700",
                        font_size="1em",
                        color=PRIMARY,
                        style={"text_shadow": GLOW_PRIMARY},
                    ),
                    spacing="0",
                    align="center",
                ),
                href="/",
                text_decoration="none",
            ),
            rx.spacer(),
            rx.hstack(
                rx.link("Ana Sayfa", href="/", color=TEXT, font_family=FONT_MONO, font_size="0.75em", _hover={"color": PRIMARY}, text_decoration="none"),
                rx.link("Hakkımda", href="/about", color=TEXT, font_family=FONT_MONO, font_size="0.75em", _hover={"color": PRIMARY}, text_decoration="none"),
                rx.link("Portfolyo", href="/portfolio", color=TEXT, font_family=FONT_MONO, font_size="0.75em", _hover={"color": PRIMARY}, text_decoration="none"),
                rx.link("Blog", href="/blog", color=TEXT, font_family=FONT_MONO, font_size="0.75em", _hover={"color": PRIMARY}, text_decoration="none"),
                rx.link("Chat", href="/chat", color=TEXT, font_family=FONT_MONO, font_size="0.75em", _hover={"color": PRIMARY}, text_decoration="none"),
                spacing="5",
                align="center",
            ),
            width="100%",
            align="center",
            padding=["0.6em 1em", "0.8em 2em"],
            overflow_x="auto",
        ),
        background=f"{BG}aa",
        backdrop_filter="blur(10px)",
        border=f"1px solid {BORDER}",
        border_radius="100px",
        width=["95%", "95%", "auto"],
        min_width=["auto", "auto", "600px"],
        position="fixed",
        top="1.5em",
        z_index="1000",
        style={"left": "50%", "transform": "translateX(-50%)"},
    )