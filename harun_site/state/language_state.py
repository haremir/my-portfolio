"""Global language state for the portfolio site (TR / EN)."""

from __future__ import annotations

import reflex as rx


class LanguageState(rx.State):
    """Manages the current display language across the entire site."""

    language: str = "tr"

    @rx.event
    def set_language(self, lang: str):
        """Switch site language. Accepts 'tr' or 'en'."""
        if lang in ("tr", "en"):
            self.language = lang

    @rx.event
    def toggle_language(self):
        """Toggle between TR and EN."""
        self.language = "en" if self.language == "tr" else "tr"

    def tr(self, texts: dict[str, str]) -> str:
        """Convenience: return the text for the current language.
        Usage:  LanguageState.tr({"tr": "Merhaba", "en": "Hello"})
        """
        return texts.get(self.language, texts.get("tr", ""))

    def _(self, texts: dict[str, str]) -> str:
        """Shorthand alias for tr()."""
        return self.tr(texts)