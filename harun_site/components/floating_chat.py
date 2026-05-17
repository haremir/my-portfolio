from __future__ import annotations

import reflex as rx

from harun_site.theme import (
    BG,
    BG_CARD,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    BORDER,
    ACCENT,
    GLOW_PRIMARY,
    FONT_MONO,
    FONT_SANS,
)
from harun_site.utils.groq_client import stream_chat


class FloatingChatState(rx.State):
    is_open: bool = False
    messages: list[dict] = []
    input_value: str = ""
    is_loading: bool = False
    show_redirect: bool = False
    current_log_filename: str = ""

    @rx.event
    def toggle(self):
        self.is_open = not self.is_open

    @rx.event
    def set_input_value(self, value: str):
        self.input_value = value

    @rx.event
    def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
        if key == "Enter":
            return self.send_message()

    @rx.event
    async def send_message(self):
        if not self.input_value.strip():
            return

        self.messages = [
            *self.messages,
            {"role": "user", "content": self.input_value},
        ]
        user_input = self.input_value
        self.input_value = ""
        self.is_loading = True
        yield

        self.messages = [
            *self.messages,
            {"role": "assistant", "content": ""},
        ]
        yield

        try:
            async for chunk in stream_chat(
                self.messages[:-1] + [{"role": "user", "content": user_input}]
            ):
                self.messages[-1]["content"] += chunk
                yield
        except RuntimeError:
            self.messages[-1]["content"] = (
                "GROQ_API_KEY is not set. Update .env and reload."
            )
            yield

        self.is_loading = False
        from harun_site.utils import data_manager

        self.current_log_filename = data_manager.save_chat_log(
            self.messages,
            self.current_log_filename or None,
        )
        user_count = sum(1 for message in self.messages if message["role"] == "user")
        if user_count >= 2:
            self.show_redirect = True
        yield

    @rx.event
    def reset_chat(self):
        self.messages = []
        return rx.window_alert("Sohbet sıfırlandı.")

    @rx.event
    def clear_chat(self):
        self.messages = []
        self.input_value = ""
        self.is_loading = False
        self.show_redirect = False
        self.current_log_filename = ""

    @rx.event
    def go_fullscreen_chat(self):
        if self.current_log_filename:
            return rx.redirect(f"/chat?c={self.current_log_filename}")
        return rx.redirect("/chat")


def _message_bubble(message: dict) -> rx.Component:
    return rx.cond(
        message["role"] == "user",
        rx.box(
            message["content"],
            align_self="flex-end",
            background_color=PRIMARY,
            color=BG,
            padding="0.4em 0.8em",
            border_radius="18px 18px 4px 18px",
            font_size="0.8em",
            max_width="85%",
            font_family=FONT_SANS,
        ),
        rx.box(
            rx.markdown(message["content"]),
            align_self="flex-start",
            background_color=BG,
            border=f"1px solid {BORDER}",
            padding="0.4em 0.8em",
            border_radius="18px 18px 18px 4px",
            font_size="0.8em",
            max_width="85%",
            font_family=FONT_SANS,
        ),
    )


def floating_chat(show: bool = True) -> rx.Component:
    if not show:
        return rx.fragment()

    header = rx.box(
        rx.hstack(
            rx.text(
                "harun.",
                font_family=FONT_MONO,
                font_size="0.8em",
                color=PRIMARY,
                style={"letter_spacing": "0.1em"},
            ),
            rx.button(
                "↺", 
                on_click=FloatingChatState.clear_chat, 
                background="transparent", 
                border="none", 
                color=TEXT_MUTED, 
                cursor="pointer", 
                font_size="0.85em", 
                padding="0 0.3em", 
                _hover={"color": PRIMARY}
            ),
            rx.spacer(),
            rx.button(
                "×",
                on_click=FloatingChatState.toggle,
                variant="ghost",
                color=TEXT_MUTED,
                padding="0",
                size="1",
                _hover={"color": PRIMARY},
            ),
            width="100%",
            padding="1em 1.2em",
            border_bottom=f"1px solid {BORDER}",
            align="center",
        ),
        background=BG,
    )

    empty_state = rx.text(
        "Portfolyo, projeler veya teknik beceriler hakkında soru sor.",
        color=TEXT_MUTED,
        font_size="0.8em",
        font_family=FONT_SANS,
        text_align="center",
        margin_top="2em",
    )

    messages_panel = rx.box(
        rx.vstack(
            rx.foreach(FloatingChatState.messages, _message_bubble),
            rx.cond(
                FloatingChatState.is_loading,
                rx.text(
                    "...",
                    color=TEXT_MUTED,
                    font_size="0.8em",
                    align_self="flex-start",
                ),
                rx.fragment(),
            ),
            spacing="2",
        ),
        height="420px",
        overflow_y="auto",
        padding="1.2em",
        flex="1",
    )

    redirect_banner = rx.cond(
        FloatingChatState.show_redirect,
        rx.box(
            rx.hstack(
                rx.text(
                    "Daha derin sohbet için →",
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    color=TEXT_MUTED,
                ),
                rx.button(
                    "Tam ekran aç",
                    on_click=FloatingChatState.go_fullscreen_chat,
                    background="transparent",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    padding="0",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            background="#00f5d410",
            border_top=f"1px solid {BORDER}",
            padding="0.5em 1em",
            display="flex",
            align_items="center",
            justify_content="space-between",
        ),
        rx.fragment(),
    )

    input_bar = rx.hstack(
        rx.input(
            flex="1",
            placeholder="sor...",
            background=BG,
            border=f"1px solid {BORDER}",
            color=TEXT,
            font_family=FONT_MONO,
            font_size="0.8em",
            border_radius="10px",
            focus_border_color=PRIMARY,
            value=FloatingChatState.input_value,
            on_change=FloatingChatState.set_input_value,
            on_key_down=FloatingChatState.handle_keydown,
            _placeholder={"color": TEXT_MUTED},
        ),
        rx.button(
            "→",
            background=PRIMARY,
            color=BG,
            border_radius="10px",
            padding="0 0.8em",
            font_weight="600",
            on_click=FloatingChatState.send_message,
        ),
        spacing="2",
        width="100%",
        style={"gap": "0.4em"},
    )

    popup = rx.box(
        header,
        messages_panel,
        redirect_banner,
        rx.box(
            input_bar,
            padding="0.6em",
            border_top=f"1px solid {BORDER}",
            display="flex",
            gap="0.4em",
        ),
        width="320px",
        background=BG_CARD,
        border=f"1px solid {PRIMARY}",
        box_shadow=GLOW_PRIMARY,
        border_radius="14px",
        overflow="hidden",
        display="flex",
        flex_direction="column",
    )

    toggle_button = rx.button(
        rx.text(
            "AI",
            font_family=FONT_MONO,
            font_size="0.75em",
            font_weight="700",
        ),
        on_click=FloatingChatState.toggle,
        width="52px",
        height="52px",
        border_radius="50%",
        background=PRIMARY,
        color=BG,
        font_size="1.3em",
        box_shadow=GLOW_PRIMARY,
        transition="all 200ms",
        _hover={"transform": "scale(1.08)"},
        style={"cursor": "pointer"},
    )

    return rx.box(
        rx.cond(FloatingChatState.is_open, popup, rx.fragment()),
        toggle_button,
        position="fixed",
        bottom="1.5em",
        right="1.5em",
        z_index="1000",
        display="flex",
        flex_direction="column",
        align_items="flex-end",
        gap="0.5em",
    )
