from __future__ import annotations

import re


_NUMBERED_LIST_RE = re.compile(r"^(\d+)[.)]\s+(.*)$")
_LIST_PREFIX_RE = re.compile(r"^(?:[-*•]|\d+[.)])\s+")


def _is_structural_line(line: str) -> bool:
	return line.startswith("#") or line.startswith(">") or _LIST_PREFIX_RE.match(line) is not None


def format_chat_response(text: str) -> str:
	text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
	if not text:
		return text

	lines = [line.rstrip() for line in text.split("\n")]
	paragraphs: list[str] = []
	buffer: list[str] = []
	previous_line = ""

	def flush_buffer():
		nonlocal buffer
		if buffer:
			paragraphs.append(" ".join(buffer).strip())
			buffer = []

	for raw_line in lines:
		line = raw_line.strip()
		if not line:
			flush_buffer()
			previous_line = ""
			continue

		numbered_match = _NUMBERED_LIST_RE.match(line)
		if numbered_match:
			line = f"- {numbered_match.group(2).strip()}"

		if line == previous_line:
			continue

		if _is_structural_line(line):
			flush_buffer()
			paragraphs.append(line)
		else:
			buffer.append(line)

		previous_line = line

	flush_buffer()

	cleaned: list[str] = []
	for paragraph in paragraphs:
		if cleaned and cleaned[-1] == paragraph:
			continue
		cleaned.append(paragraph)

	result_lines: list[str] = []
	for paragraph in cleaned:
		if result_lines:
			previous = result_lines[-1]
			if _LIST_PREFIX_RE.match(previous) and _LIST_PREFIX_RE.match(paragraph):
				result_lines.append(paragraph)
			else:
				result_lines.extend(["", paragraph])
		else:
			result_lines.append(paragraph)

	return "\n".join(result_lines).strip()