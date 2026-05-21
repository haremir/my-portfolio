import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.state.chat_state import ChatState, MessageDict
from harun_site.utils.groq_client import MODEL_FAST
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


def message_row(message: MessageDict) -> rx.Component:
    # Guard: only render rx.markdown when content is a non-empty string.
    # ChatState.messages is now list[MessageDict] (TypedDict with content: str)
    # so Reflex knows the field type, but we also guard with rx.cond so that
    # the initial empty-string placeholder during streaming never reaches
    # react-markdown as a JS object.
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
                    "white_space": "pre-wrap",
                    "word_break": "break-word",
                },
                max_width="70%",
            ),
            width="100%",
            justify="end",
        ),
        rx.hstack(
            rx.box(
                rx.cond(
                    message["content"] != "",
                    rx.markdown(message["content"]),
                    rx.text(
                        "●●●",
                        color=TEXT_MUTED,
                        font_size="0.8em",
                        letter_spacing="0.15em",
                    ),
                ),
                background_color=BG_CARD,
                color=TEXT,
                style={
                    "padding": "0.6em 1em",
                    "border_radius": "18px 18px 18px 4px",
                    "border": f"1px solid {BORDER}",
                    "font_family": FONT_SANS,
                    "font_size": "0.9em",
                    "word_break": "break-word",
                },
                max_width="80%",
            ),
            width="100%",
            justify="start",
        ),
    )


def chat_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "HARUN İLE SOHBET",
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
                    rx.spacer(),
                    rx.button(
                        "+ Yeni Sohbet",
                        on_click=ChatState.new_conversation,
                        font_family=FONT_MONO,
                        font_size="0.75em",
                        background="transparent",
                        color=TEXT_MUTED,
                        border=f"1px solid {BORDER}",
                        padding="0.4em 0.9em",
                        border_radius="6px",
                        cursor="pointer",
                        _hover={"color": PRIMARY, "border_color": PRIMARY},
                        transition="all 150ms"
                    ),
                    width="100%",
                    align="center",
                    justify="between",
                ),
                rx.text(
                    "Portfolyo, projeler ve teknik beceriler hakkinda soru sorabilirsiniz.",
                    color=TEXT_MUTED,
                    font_family=FONT_SANS,
                    style={"font_size": "0.85em", "margin_bottom": "1.5em"},
                ),
                rx.box(
                    rx.hstack(
                        rx.text("⚙", font_size="0.8em"),
                        rx.text("Nasıl çalışır?", font_family=FONT_MONO,
                                font_size="0.75em", color=PRIMARY, font_weight="600"),
                        rx.text("·", color=BORDER),
                        rx.text(f"Groq API · {MODEL_FAST} · Dinamik context · Streaming",
                                font_family=FONT_MONO, font_size="0.72em", color=TEXT_MUTED),
                        gap="0.5em",
                        align="center",
                        flex_wrap="wrap",
                    ),
                    padding="0.6em 1em",
                    background=BG_CARD,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    margin_bottom="1em",
                    width="100%",
                ),
                rx.cond(
                    ChatState.show_suggestions & (ChatState.messages.length() == 0),
                    rx.vstack(
                        rx.text("Başlamak için bir soru seç:", font_family=FONT_MONO,
                                font_size="0.75em", color=TEXT_MUTED),
                        rx.hstack(
                            rx.foreach(
                                ChatState.suggestions,
                                lambda s: rx.button(
                                    s,
                                    on_click=ChatState.use_suggestion(s),
                                    font_family=FONT_MONO,
                                    font_size="0.78em",
                                    background="transparent",
                                    color=TEXT_MUTED,
                                    border=f"1px solid {BORDER}",
                                    padding="0.4em 0.9em",
                                    border_radius="20px",
                                    cursor="pointer",
                                    transition="all 150ms",
                                    _hover={"color": PRIMARY, "border_color": PRIMARY},
                                )
                            ),
                            flex_wrap="wrap",
                            gap="0.5em",
                        ),
                        align_items="flex-start",
                        gap="0.8em",
                        padding="1em",
                        margin_bottom="1em",
                    ),
                    rx.fragment(),
                ),
                rx.vstack(
                    rx.foreach(ChatState.messages, message_row),
                    rx.cond(
                        ChatState.is_loading,
                        rx.text("...", color=TEXT_MUTED),
                        rx.fragment(),
                    ),
                    # id is picked up by chat_scroll.js to wire the
                    # MutationObserver that drives streaming auto-scroll.
                    id="chat-messages-main",
                    spacing="3",
                    height="50vh",
                    max_height="450px",
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
            flex="1",
        ),
        footer(),
        floating_chat(show=False),
        width="100%",
        min_height="100vh",
        bg=BG,
        spacing="0",
    )
