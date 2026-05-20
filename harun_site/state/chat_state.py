from __future__ import annotations

import reflex as rx
import sys
from typing import TypedDict


class MessageDict(TypedDict):
    """Typed chat message – content is always str so Reflex serialises it
    as a JS string, never as [object Object]."""
    role: str
    content: str

from harun_site.utils.groq_client import complete_chat, stream_chat
from harun_site.utils.response_formatter import format_chat_response


class ChatState(rx.State):
	messages: list[MessageDict] = []
	current_input: str = ""
	is_loading: bool = False
	current_log_filename: str = ""
	suggestions: list[str] = []
	show_suggestions: bool = True

	@rx.event
	def on_load(self):
		from harun_site.utils.data_manager import load_suggestions

		self.suggestions = load_suggestions()

	@rx.event
	def load_from_params(self):
		from harun_site.utils.data_manager import load_suggestions

		self.suggestions = load_suggestions()
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

		history = [*self.messages, {"role": "user", "content": content}]
		self.messages = [*self.messages, {"role": "user", "content": content}]
		self.current_input = ""
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
				raw_assistant_content = await complete_chat(history)
				self.messages = [
					*self.messages[:-1],
					{"role": "assistant", "content": raw_assistant_content},
				]
				yield
			self.messages[-1]["content"] = format_chat_response(raw_assistant_content)
			yield
		except Exception as exc:
			err = str(exc)
			print(f"[GROQ ERROR] {type(exc).__name__}: {err}")
			import traceback
			traceback.print_exc()
			# ── Telegram error alert ───────────────────────────────────────
			try:
				from harun_site.telegram_bot.notifier import notify_error
				notify_error(err, context="chat/send_message")
			except Exception:
				pass
			# ──────────────────────────────────────────────────────────────
			if "api_key" in err.lower() or "authentication" in err.lower() or "invalid_api_key" in err.lower():
				self.messages[-1]["content"] = (
					"⚠️ Yapay zeka servisi şu an yapılandırılmamış. "
					"Lütfen daha sonra tekrar deneyin."
				)
			else:
				if raw_assistant_content:
					self.messages[-1]["content"] = format_chat_response(raw_assistant_content)
				else:
					self.messages[-1]["content"] = "⚠️ Bir hata oluştu, lütfen tekrar deneyin."
			yield

		self.is_loading = False

		# Save chat log
		from harun_site.utils import data_manager
		self.current_log_filename = data_manager.save_chat_log(
			self.messages,
			self.current_log_filename or None,
		)

		# ── Telegram notification hooks (never crash chat on failure) ──────
		try:
			from harun_site.telegram_bot.notifier import (
				notify_hiring_if_warranted,
				notify_watch_if_warranted,
				notify_long_session,
			)
			notify_hiring_if_warranted(self.messages)
			notify_watch_if_warranted(self.messages)
			notify_long_session(self.messages)
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
		from harun_site.utils.groq_client import stream_chat
		from harun_site.utils.data_manager import save_chat_summary
		import json, re, sys

		summary_prompt = f"""Aşağıdaki portfolyo sitesi ziyaretçi konuşmasını analiz et.
SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{"summary": "2-3 cümle Türkçe özet", "top_topics": ["konu1", "konu2"], "message_count": {len(self.messages)}}}

Konuşma:
{chr(10).join(f'{m["role"]}: {m["content"][:200]}' for m in self.messages)}"""

		result = ""
		try:
			async for chunk in stream_chat([{"role": "user", "content": summary_prompt}]):
				result += chunk

			# Remove markdown code blocks if present
			clean = re.sub(r"```json|```", "", result).strip()
			data = json.loads(clean)
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
