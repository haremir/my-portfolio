import reflex as rx
from harun_site.theme import BG, BORDER, PRIMARY, TEXT, TEXT_MUTED, FONT_MONO, GLOW_PRIMARY
from harun_site.state.language_state import LanguageState
from harun_site.utils.i18n import TXT


def _nav_link(text_key, href):
    return rx.link(
        rx.cond(
            LanguageState.language == "en",
            TXT[text_key]["en"],
            TXT[text_key]["tr"],
        ),
        href=href, color=TEXT, font_family=FONT_MONO, font_size="0.75em",
        _hover={"color": PRIMARY}, text_decoration="none",
    )


def _lang_toggle():
    return rx.button(
        rx.cond(
            LanguageState.language == "en",
            rx.hstack(
                rx.text("TR", font_size="0.65em", font_weight="600", color=TEXT_MUTED, opacity="0.5"),
                rx.text("|", font_size="0.6em", color=TEXT_MUTED, opacity="0.3"),
                rx.text("EN", font_size="0.65em", font_weight="700", color=PRIMARY),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.text("TR", font_size="0.65em", font_weight="700", color=PRIMARY),
                rx.text("|", font_size="0.6em", color=TEXT_MUTED, opacity="0.3"),
                rx.text("EN", font_size="0.65em", font_weight="600", color=TEXT_MUTED, opacity="0.5"),
                spacing="1", align="center",
            ),
        ),
        on_click=LanguageState.toggle_language,
        background="transparent", border=f"1px solid {BORDER}",
        border_radius="6px", padding="0.1em 0.4em",
        cursor="pointer", _hover={"border_color": PRIMARY}, transition="all 150ms",
    )


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
                _nav_link("nav_home", "/"),
                _nav_link("nav_about", "/about"),
                _nav_link("nav_portfolio", "/portfolio"),
                _nav_link("nav_blog", "/blog"),
                _nav_link("nav_chat", "/chat"),
                _lang_toggle(),
                spacing="4",
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