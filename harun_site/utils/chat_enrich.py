"""Post-process chat replies so project references stay registry-controlled."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from harun_site.utils.data_manager import load_projects
from harun_site.utils.project_registry import (
    canonicalize_project_record,
    normalize_project_text,
    project_reference_payload,
    resolve_project,
)

_PROJECT_REF_TOKEN_RE = re.compile(r"\[\[PROJECT_REF:([a-z0-9][a-z0-9_-]*)\]\]", re.IGNORECASE)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_PORTFOLIO_LINK_RE = re.compile(r"\[([^\]]+)\]\((/portfolio/[^)]+)\)", re.IGNORECASE)
_PORTFOLIO_RAW_URL_RE = re.compile(r"/(?:portfolio|projects)/([a-z0-9_-]+)", re.IGNORECASE)
_PROJECT_SAFE_PLACEHOLDER_RE = re.compile(r"__PROJECT_SAFE_(\d+)__")


def _project_index() -> list[dict]:
    return [canonicalize_project_record(project) for project in load_projects()]


def _project_by_id(project_id: str) -> dict | None:
    normalized_id = normalize_project_text(project_id).replace(" ", "")
    for project in _project_index():
        if normalize_project_text(project.get("id", "")).replace(" ", "") == normalized_id:
            return project
    return None


def _render_project_reference(project: dict) -> str:
    payload = project_reference_payload(project)
    title = payload["title"]
    url = payload["url"]
    return f"[{title}]({url})"


def _replace_project_tokens(text: str) -> str:
    def _token_replacer(match: re.Match[str]) -> str:
        project = _project_by_id(match.group(1))
        if not project:
            return ""
        return _render_project_reference(project)

    return _PROJECT_REF_TOKEN_RE.sub(_token_replacer, text)


def _canonicalize_portfolio_links(text: str) -> str:
    def _link_replacer(match: re.Match[str]) -> str:
        label = match.group(1).strip()
        href = match.group(2).strip()
        slug = href.rsplit("/", 1)[-1].strip()
        project = resolve_project(slug, _project_index())
        if not project:
            return label
        return _render_project_reference(project)

    return _PORTFOLIO_LINK_RE.sub(_link_replacer, text)


def _canonicalize_raw_urls(text: str) -> str:
    def _url_replacer(match: re.Match[str]) -> str:
        project = resolve_project(match.group(1), _project_index())
        if not project:
            return ""
        return project["url"]

    return _PORTFOLIO_RAW_URL_RE.sub(_url_replacer, text)


def _project_mention_pattern(candidate: str) -> re.Pattern[str] | None:
    normalized = normalize_project_text(candidate)
    if not normalized:
        return None
    parts = normalized.split()
    escaped_parts = [re.escape(part) for part in parts]
    joined = r"[\s\-_/]*".join(escaped_parts)
    return re.compile(rf"(?<![a-z0-9]){joined}(?![a-z0-9])", re.IGNORECASE)


def _protect_spans(text: str) -> tuple[str, list[str]]:
    protected: list[str] = []

    def _store(segment: str) -> str:
        placeholder = f"__PROJECT_SAFE_{len(protected)}__"
        protected.append(segment)
        return placeholder

    text = _MARKDOWN_LINK_RE.sub(lambda match: _store(match.group(0)), text)
    text = _PORTFOLIO_RAW_URL_RE.sub(lambda match: _store(match.group(0)), text)
    return text, protected


def _restore_spans(text: str, protected: list[str]) -> str:
    def _restore(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if 0 <= index < len(protected):
            return protected[index]
        return ""

    return _PROJECT_SAFE_PLACEHOLDER_RE.sub(_restore, text)


def _canonicalize_plain_project_mentions(text: str) -> str:
    protected_text, protected = _protect_spans(text)
    canonical_projects = _project_index()
    patterns: list[tuple[re.Pattern[str], str]] = []
    seen: set[str] = set()

    for project in canonical_projects:
        title = str(project.get("title") or "").strip()
        if not title:
            continue
        candidates = [project.get("id", ""), project.get("title", ""), project.get("name", ""), project.get("slug", "")]
        candidates.extend(project.get("aliases") or [])
        for candidate in candidates:
            pattern = _project_mention_pattern(str(candidate or ""))
            if not pattern:
                continue
            pattern_key = pattern.pattern
            if pattern_key in seen:
                continue
            seen.add(pattern_key)
            patterns.append((pattern, title))

    out = protected_text
    for pattern, title in sorted(patterns, key=lambda item: len(item[0].pattern), reverse=True):
        out = pattern.sub(title, out)

    return _restore_spans(out, protected)


def finalize_project_references(text: str, user_query: str = "") -> str:
    """Render structured project tokens and canonicalize any portfolio links.

    If the text contains no canonical project token or registry-resolvable link,
    it is returned mostly unchanged. Invalid project URLs are never emitted.
    """
    if not text:
        return text

    out = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    out = _replace_project_tokens(out)
    out = _canonicalize_portfolio_links(out)
    out = _canonicalize_raw_urls(out)
    out = _canonicalize_plain_project_mentions(out)

    # Last-resort fallback: if the model explicitly mentioned a known project
    # name but no link survived, append a canonical link for the best match.
    if user_query.strip():
        matched = resolve_project(user_query, _project_index())
        if matched and matched.get("url") and matched.get("title"):
            canonical_link = _render_project_reference(matched)
            if matched["url"] not in out and canonical_link not in out:
                out = f"{out}\n\n{canonical_link}".strip()
    return out


def finalize_streamed_project_references(chunks: Iterable[str], user_query: str = "") -> str:
    """Finalize a buffered stream only after all chunks have been assembled."""
    return finalize_project_references("".join(chunk for chunk in chunks if chunk), user_query)


def ensure_case_study_links(text: str, user_query: str) -> str:
    """Compatibility wrapper for existing callers."""
    return finalize_project_references(text, user_query)
