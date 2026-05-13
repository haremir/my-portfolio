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
		
		# Summarization logic
		user_msg_count = sum(1 for m in self.messages if m["role"] == "user")
		if user_msg_count >= 6 and user_msg_count % 6 == 0:
			yield ChatState._summarize_and_save
		
		yield

	async def _summarize_and_save(self):
		from harun_site.utils.groq_client import stream_chat
		from harun_site.utils.data_manager import save_chat_summary
		import json, re, sys

		summary_prompt = f"""Aşağıdaki portfolyo sitesi ziyaretçi konuşmasını analiz et.
SADECE şu JSON formatında yanıt ver, başka hiçbir şey yazma:
{{"summary": "2-3 cümle Türkçe özet", "top_topics": ["konu1", "konu2"], "message_count": {len(self.messages)}}}

Konuşma:
{chr(10).join(f'{m["role"]}: {m["content"][:200]}' for m in self.messages)}"""

		result = ""
		async for chunk in stream_chat([{"role": "user", "content": summary_prompt}]):
			result += chunk

		try:
			# Remove markdown code blocks if present
			clean = re.sub(r"```json|```", "", result).strip()
			data = json.loads(clean)
			save_chat_summary(data)
		except Exception as e:
			print(f"[SUMMARY] Failed: {e}", file=sys.stderr)