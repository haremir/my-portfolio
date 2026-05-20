from __future__ import annotations

import reflex as rx
from typing import TypedDict


class MessageDict(TypedDict):
    """Typed chat message – content is always str so Reflex serialises it
    as a JS string and never passes [object Object] to rx.markdown()."""
    role: str
    content: str

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
from harun_site.utils.groq_client import complete_chat, stream_chat


class FloatingChatState(rx.State):
    is_open: bool = False
    messages: list[MessageDict] = []
    input_value: str = ""
    is_loading: bool = False
    show_redirect: bool = False
    current_log_filename: str = ""
    suggestions: list[str] = []
    show_suggestions: bool = True

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_suggestions

        self.suggestions = load_suggestions()

    @rx.event
    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open and not self.suggestions:
            return FloatingChatState.on_load()

    @rx.event
    def set_input_value(self, value: str):
        self.input_value = value

    @rx.event
    def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
        if key == "Enter":
            return self.send_message()

    @rx.event
    def use_suggestion(self, suggestion: str):
        self.input_value = suggestion
        self.show_suggestions = False
        return FloatingChatState.send_message()

    @rx.event
    async def send_message(self):
        if not self.input_value.strip():
            return

        user_input = self.input_value
        history = [*self.messages, {"role": "user", "content": user_input}]
        self.messages = [
            *self.messages,
            {"role": "user", "content": user_input},
        ]
        self.input_value = ""
        self.is_loading = True
        yield

        self.messages = [
            *self.messages,
            {"role": "assistant", "content": ""},
        ]
        yield

        try:
            raw_assistant_content = ""
            streamed_any_chunk = False
            async for chunk in stream_chat(history):
                streamed_any_chunk = True
                raw_assistant_content += chunk
                self.messages = [
                    *self.messages[:-1],
                    {"role": "assistant", "content": raw_assistant_content},
                ]
                yield

            if not streamed_any_chunk and not raw_assistant_content:
                fallback_content = await complete_chat(history)
                self.messages = [
                    *self.messages[:-1],
                    {"role": "assistant", "content": fallback_content},
                ]
                yield
        except Exception as exc:
            err = str(exc)
            if "api_key" in err.lower() or "authentication" in err.lower():
                self.messages[-1]["content"] = (
                    "⚠️ Yapay zeka servisi şu an yapılandırılmamış."
                )
            else:
                if not self.messages[-1]["content"]:
                    self.messages[-1]["content"] = (
                        "⚠️ Bir hata oluştu, lütfen tekrar deneyin."
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
        self.show_suggestions = True
        return rx.window_alert("Sohbet sıfırlandı.")

    @rx.event
    def clear_chat(self):
        self.messages = []
        self.input_value = ""
        self.show_suggestions = True
        self.is_loading = False
        self.show_redirect = False
        self.current_log_filename = ""

    @rx.event
    def go_fullscreen_chat(self):
        if self.current_log_filename:
            return rx.redirect(f"/chat?c={self.current_log_filename}")
        return rx.redirect("/chat")


def _message_bubble(message: MessageDict) -> rx.Component:
    # Guard: only render rx.markdown when content is a non-empty string.
    # Without this, a temporarily-empty or mis-typed content value would
    # reach react-markdown as [object Object] and crash the frontend.
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
            rx.cond(
                message["content"] != "",
                rx.markdown(message["content"]),
                rx.text(
                    "●●●",
                    color=TEXT_MUTED,
                    font_size="0.75em",
                    letter_spacing="0.15em",
                ),
            ),
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
            rx.cond(
                FloatingChatState.show_suggestions & (FloatingChatState.messages.length() == 0),
                rx.vstack(
                    rx.text("Bir soru seç:", font_family=FONT_MONO,
                            font_size="0.72em", color=TEXT_MUTED),
                    rx.vstack(
                        rx.foreach(
                            FloatingChatState.suggestions,
                            lambda s: rx.button(
                                s,
                                on_click=FloatingChatState.use_suggestion(s),
                                font_family=FONT_MONO,
                                font_size="0.75em",
                                background="transparent",
                                color=TEXT_MUTED,
                                border=f"1px solid {BORDER}",
                                padding="0.3em 0.8em",
                                border_radius="16px",
                                cursor="pointer",
                                width="100%",
                                text_align="left",
                                transition="all 150ms",
                                _hover={"color": PRIMARY, "border_color": PRIMARY},
                            )
                        ),
                        gap="0.4em",
                        width="100%",
                    ),
                    align_items="flex-start",
                    gap="0.5em",
                    padding="0.5em",
                ),
                rx.fragment(),
            ),
            spacing="2",
        ),
        # id is picked up by chat_scroll.js to wire the
        # MutationObserver that drives streaming auto-scroll.
        id="chat-messages-floating",
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
        toggle_button,
        rx.cond(FloatingChatState.is_open, popup, rx.fragment()),
        position="fixed",
        bottom="1.5em",
        left="1.5em",
        z_index="1000",
        display="flex",
        flex_direction="column",
        align_items="flex-start",
        gap="0.5em",
    )
