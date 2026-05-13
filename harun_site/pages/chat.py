import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.floating_chat import floating_chat
from harun_site.state.chat_state import ChatState
from harun_site.theme import (
    BG,
    BG_CARD,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    BORDER,
    ACCENT,
    GLOW_PRIMARY,
    GLOW_ACCENT,
    FONT_MONO,
    FONT_SANS,
)


def message_row(message) -> rx.Component:
    return rx.cond(
        message["role"] == "user",
        rx.hstack(
            rx.box(
                message["content"],
                background_color=PRIMARY,
                color=BG,
                style={
                    "padding": "0.6em 1em",
                    "border_radius": "18px 18px 4px 18px",
                    "font_family": FONT_SANS,
                    "font_size": "0.9em",
                },
                max_width="70%",
            ),
            width="100%",
            justify="end",
        ),
        rx.hstack(
            rx.box(
                message["content"],
                background_color=BG_CARD,
                color=TEXT,
                style={
                    "padding": "0.6em 1em",
                    "border_radius": "18px 18px 18px 4px",
                    "border": f"1px solid {BORDER}",
                    "font_family": FONT_SANS,
                    "font_size": "0.9em",
                },
                max_width="80%",
            ),
            width="100%",
            justify="start",
        ),
    )


@rx.page(route="/chat", on_load=ChatState.load_from_params)
def chat_page() -> rx.Component:
    return rx.box(
        navbar(),
        rx.box(
            rx.vstack(
                rx.heading(
                    "Harun ile Sohbet",
                    size="4",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    style={
                        "font_size": "0.75em",
                        "letter_spacing": "0.2em",
                        "text_transform": "uppercase",
                        "text_shadow": GLOW_PRIMARY,
                    },
                ),
                rx.text(
                    "Portfolyo, projeler ve teknik beceriler hakkinda soru sorabilirsiniz.",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "margin_bottom": "1.5em"},
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(ChatState.messages, message_row),
                        rx.cond(
                            ChatState.is_loading,
                            rx.text("...", color=TEXT_MUTED),
                            rx.fragment(),
                        ),
                        spacing="3",
                    ),
                    flex="1",
                    overflow_y="auto",
                    background_color=BG_CARD,
                    border=f"1px solid {PRIMARY}",
                    style={
                        "border_radius": "16px",
                        "padding": "1.5em",
                        "box_shadow": "0 0 15px #00f5d420",
                    },
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        flex="1",
                        placeholder="bir şey sor...",
                        background_color=BG_CARD,
                        border=f"1px solid {BORDER}",
                        color=TEXT,
                        font_family=FONT_MONO,
                        style={"font_size": "0.9em", "border_radius": "10px"},
                        focus_border_color=PRIMARY,
                        value=ChatState.current_input,
                        on_change=ChatState.set_current_input,
                        on_key_down=ChatState.handle_keydown,
                        _placeholder={"color": TEXT_MUTED},
                    ),
                    rx.button(
                        "gönder",
                        background_color=PRIMARY,
                        color=BG,
                        font_family=FONT_MONO,
                        font_weight="600",
                        style={"border_radius": "10px", "padding": "0 1.5em"},
                        _hover={"box_shadow": GLOW_PRIMARY},
                        transition="all 200ms",
                        on_click=ChatState.send_message,
                    ),
                    spacing="2",
                    width="100%",
                    style={"gap": "0.5em"},
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            style={
                "max_width": "800px",
                "margin": "0 auto",
                "padding": "8em 2em 3em 2em",
                "height": "100vh",
                "display": "flex",
                "flex_direction": "column",
            },
            width="100%",
        ),
        floating_chat(show=False),
        width="100%",
        min_height="100vh",
        bg=BG,
    )
