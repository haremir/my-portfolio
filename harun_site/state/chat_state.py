from __future__ import annotations

import reflex as rx
import sys
from typing import TypedDict


class MessageDict(TypedDict):
    """Typed chat message – content is always str so Reflex serialises it
    as a JS string, never as [object Object]."""
    role: str
    content: str
    provider: str
    model: str

from harun_site.utils.groq_client import (
	complete_chat,
	is_rate_limit_error,
	stream_chat,
	user_message_for_groq_error,
)
from harun_site.utils.chat_enrich import finalize_streamed_project_references
from harun_site.utils.response_formatter import format_chat_response


class ChatState(rx.State):
	messages: list[MessageDict] = []
	current_input: str = ""
	is_loading: bool = False
	current_log_filename: str = ""
	suggestions: list[str] = []
	show_suggestions: bool = True

	@rx.event
	async def on_load(self):
		from harun_site.utils.data_manager import load_suggestions, load_chat_log_messages
		from harun_site.state.language_state import LanguageState
		lang_state = await self.get_state(LanguageState)

		self.suggestions = load_suggestions(lang_state.language)
		if not self.messages and self.current_log_filename:
			restored = load_chat_log_messages(self.current_log_filename)
			if restored:
				self.messages = restored

	@rx.event
	async def load_from_params(self):
		from harun_site.utils.data_manager import load_suggestions
		from harun_site.state.language_state import LanguageState
		lang_state = await self.get_state(LanguageState)

		self.suggestions = load_suggestions(lang_state.language)
		log_filename = ""
		q = ""
		if "?" in self.router.url:
			query_parts = self.router.url.split("?", 1)[-1].split("&")
			for part in query_parts:
				if "=" in part:
					k, v = part.split("=", 1)
					if k in {"c", "log"}:
						import urllib.parse
						log_filename = urllib.parse.unquote(v)
					if k == "q":
						import urllib.parse
						q = urllib.parse.unquote(v)
						break
		if log_filename:
			from harun_site.utils.data_manager import load_chat_log_messages

			self.current_log_filename = log_filename
			self.messages = load_chat_log_messages(log_filename)
			self.current_input = ""
			self.is_loading = False
			return
		if q:
			self.current_input = q
			return self.send_message()

	@rx.event
	def set_current_input(self, value: str):
		self.current_input = value

	@rx.event
	def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
		if key == "Enter":
			return self.send_message()

	@rx.event
	def use_suggestion(self, suggestion: str):
		self.current_input = suggestion
		self.show_suggestions = False
		return ChatState.send_message()

	@rx.event
	async def send_message(self):
		content = self.current_input.strip()
		if not content:
			return

		history = [*self.messages, {"role": "user", "content": content, "provider": "", "model": ""}]
		self.messages = [*self.messages, {"role": "user", "content": content, "provider": "", "model": ""}]
		self.current_input = ""
		self.is_loading = True
		yield

		self.messages = [
			*self.messages,
			{"role": "assistant", "content": "", "provider": "", "model": ""},
		]
		yield

		try:
			raw_assistant_content = ""
			streamed_any_chunk = False
			info = {"provider": "", "model": ""}
			async for chunk in stream_chat(history, info):
				streamed_any_chunk = True
				raw_assistant_content += chunk
				self.messages[-1]["content"] = raw_assistant_content
				if info.get("provider"):
					self.messages[-1]["provider"] = info["provider"]
					self.messages[-1]["model"] = info["model"]
				self.messages = list(self.messages)  # Force dirty tracking
				yield

			if not streamed_any_chunk and not raw_assistant_content:
				raw_assistant_content = await complete_chat(history, info)
				if info.get("provider"):
					self.messages[-1]["provider"] = info["provider"]
					self.messages[-1]["model"] = info["model"]

			if raw_assistant_content:
				formatted = format_chat_response(raw_assistant_content)
				self.messages[-1]["content"] = finalize_streamed_project_references([formatted], content)
				self.messages = list(self.messages)  # Force dirty tracking
				yield
		except Exception as exc:
			err = str(exc)
			if is_rate_limit_error(exc):
				print(f"[GROQ] Rate limit (429): daily token quota exceeded.", file=sys.stderr)
			else:
				print(f"[GROQ ERROR] {type(exc).__name__}: {err}")
				import traceback
				traceback.print_exc()
			if not is_rate_limit_error(exc):
				try:
					from harun_site.telegram_bot.notifier import notify_error
					notify_error(err, context="chat/send_message")
				except Exception:
					pass
			self.messages[-1]["content"] = user_message_for_groq_error(exc)
			self.messages = list(self.messages)  # Force dirty tracking
			yield

		self.is_loading = False

		# Save chat log
		is_new_session = not self.current_log_filename
		from harun_site.utils import data_manager
		self.current_log_filename = data_manager.save_chat_log(
			self.messages,
			self.current_log_filename or None,
		)

		# ── Telegram notification hooks (never crash chat on failure) ──────
		try:
			from harun_site.telegram_bot.notifier import (
				notify_new_visitor,
				notify_hiring_if_warranted,
				notify_watch_if_warranted,
				notify_long_session,
			)
			# Yeni oturumun ilk mesajı kaydedildiğinde ziyaretçi bildirimi
			if is_new_session and self.current_log_filename:
				first_user_msg = next(
					(m["content"] for m in self.messages if m["role"] == "user"),
					"",
				)
				notify_new_visitor(first_user_msg, self.current_log_filename)
			notify_hiring_if_warranted(self.messages, self.current_log_filename)
			notify_watch_if_warranted(self.messages)
			notify_long_session(self.messages, self.current_log_filename)
		except Exception as _notify_err:
			print(f"[NOTIFY] Hook error (non-fatal): {_notify_err}", file=sys.stderr)
		# ──────────────────────────────────────────────────────────────────

		# Summarization logic
		user_msg_count = sum(1 for m in self.messages if m["role"] == "user")
		if user_msg_count >= 6 and user_msg_count % 6 == 0:
			yield ChatState.summarize_and_save()

		yield

	@rx.event
	async def summarize_and_save(self):
		from harun_site.utils.groq_client import summarize_conversation
		from harun_site.utils.data_manager import save_chat_summary

		try:
			data = await summarize_conversation(self.messages)
			if data:
				save_chat_summary(data)
		except Exception as e:
			print(f"[SUMMARY] Failed: {e}", file=sys.stderr)

	@rx.event
	def reset_chat(self):
		self.messages = []
		self.show_suggestions = True
		return rx.window_alert("Sohbet sıfırlandı.")

	@rx.event
	def new_conversation(self):
		self.messages = []
		self.current_input = ""
		self.is_loading = False
		self.current_log_filename = ""
		self.show_suggestions = True
