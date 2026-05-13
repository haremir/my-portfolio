from __future__ import annotations

import reflex as rx

from harun_site.utils.groq_client import stream_chat


class ChatState(rx.State):
	messages: list[dict] = []
	current_input: str = ""
	is_loading: bool = False

	def load_from_params(self):
		q = self.router.page.params.get("q", "")
		if q:
			self.current_input = q
			return ChatState.send_message()

	def set_current_input(self, value: str):
		self.current_input = value

	def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
		if key == "Enter":
			return self.send_message()

	async def send_message(self):
		content = self.current_input.strip()
		if not content:
			return

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
			async for chunk in stream_chat(self.messages):
				self.messages[-1]["content"] += chunk
				yield
		except RuntimeError as exc:
			self.messages[-1]["content"] = (
				"GROQ_API_KEY is not set. Update .env and reload."
			)
			yield

		self.is_loading = False
		
		# Save chat log
		from harun_site.utils import data_manager
		data_manager.save_chat_log(self.messages)
		
		yield