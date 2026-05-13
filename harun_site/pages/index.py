import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.theme import (
    BG,
    BG_CARD,
    BORDER,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    GLOW_PRIMARY,
    FONT_SANS,
    FONT_MONO,
)


class IndexChatState(rx.State):
    query: str = ""

    def set_query(self, value: str):
        self.query = value

    def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
        if key == "Enter":
            return self.submit_query()

    def submit_query(self):
        if self.query.strip():
            return rx.redirect(f"/chat?q={self.query}")


@rx.page(route="/")
def index_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.vstack(
            rx.image(
                src="/avatar.jpg",
                width="260px",
                height="260px",
                object_fit="cover",
                border_radius="50%",
                border=f"2px solid {PRIMARY}",
                box_shadow=GLOW_PRIMARY,
                margin_bottom="1.2em",
            ),
            rx.text(
                "── AI & BACKEND ENGINEER ──",
                color=PRIMARY,
                font_family=FONT_MONO,
                style={
                    "font_size": "0.72em",
                    "letter_spacing": "0.2em",
                    "opacity": "0.8",
                    "margin_bottom": "1.2em",
                },
            ),
            rx.text(
                "Harun Dülger.",
                font_family=FONT_SANS,
                color=TEXT,
                style={
                    "font_size": "3.8em",
                    "font_weight": "700",
                    "line_height": "1.05",
                    "margin_bottom": "0.6em",
                },
            ),
            rx.text(
                "Bilgisayar Mühendisi mezunu · ProudSec AI Intern · Python & AI odaklı",
                color=TEXT_MUTED,
                font_family=FONT_SANS,
                style={"font_size": "0.95em", "margin_bottom": "2em"},
            ),
            rx.hstack(
                rx.link(
                    rx.button(
                        "Hakkımda",
                        color=PRIMARY,
                        background="transparent",
                        border=f"1px solid {PRIMARY}",
                        padding="0.65em 1.6em",
                        border_radius="6px",
                        font_family=FONT_MONO,
                        font_size="0.85em",
                        cursor="pointer",
                        _hover={"background": PRIMARY, "color": BG},
                        transition="all 200ms",
                    ),
                    href="/about",
                ),
                rx.link(
                    rx.button(
                        "Chat",
                        background=PRIMARY,
                        color=BG,
                        padding="0.65em 1.6em",
                        border_radius="6px",
                        font_family=FONT_MONO,
                        font_size="0.85em",
                        font_weight="600",
                        cursor="pointer",
                        _hover={"box_shadow": GLOW_PRIMARY},
                        transition="all 200ms",
                    ),
                    href="/chat",
                ),
                style={"gap": "1em", "margin_bottom": "2em"},
            ),
            rx.box(
                rx.input(
                    placeholder="bir şey sor... · dent-bot nedir?",
                    width="100%",
                    background="#0a1a1d",
                    border=f"1px solid {BORDER}",
                    color=TEXT,
                    color_scheme="teal",
                    font_family=FONT_MONO,
                    font_size="0.85em",
                    padding="0.85em 3em 0.85em 1.2em",
                    border_radius="8px",
                    height="48px",
                    _placeholder={"color": "#7a9ba8"},
                    _focus={
                        "border_color": PRIMARY,
                        "box_shadow": f"0 0 0 1px {PRIMARY}40",
                        "outline": "none",
                    },
                    style={
                        "color": TEXT,
                        "background": BG_CARD,
                        "caretColor": PRIMARY,
                        "::placeholder": {"color": TEXT_MUTED},
                        ":focus": {"borderColor": PRIMARY, "outline": "none"},
                    },
                    on_change=IndexChatState.set_query,
                    on_key_down=IndexChatState.handle_keydown,
                ),
                rx.button(
                    "→",
                    position="absolute",
                    right="0.8em",
                    top="50%",
                    transform="translateY(-50%)",
                    background="transparent",
                    border="none",
                    color=PRIMARY,
                    cursor="pointer",
                    font_size="1.1em",
                    font_family=FONT_MONO,
                    padding="0",
                    on_click=IndexChatState.submit_query,
                ),
                width="100%",
                max_width="480px",
                position="relative",
            ),
            align_items="center",
            text_align="center",
            flex="1",
            width="100%",
            padding="8em 2em 4em 2em",
            style={
                "justify_content": "center",
                "background": "radial-gradient(ellipse at 50% 30%, #00f5d412 0%, transparent 60%)",
            },
        ),
        footer(),
        floating_chat(),
        min_height="100vh",
        width="100%",
        bg=BG,
        spacing="0",
    )