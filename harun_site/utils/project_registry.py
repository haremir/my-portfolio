"""Canonical project registry helpers.

This module keeps project identity deterministic:
- text normalization is only used for matching
- slugs and URLs are never generated from free-form text
- canonical records always carry id, title, slug, url, and aliases
"""

from __future__ import annotations

import re
import sys
from typing import Iterable


def normalize_project_text(text: str) -> str:
    """Normalize user/project text for matching only.

    The result is lowercased, trimmed, punctuation-stripped, and duplicate
    whitespace is collapsed. This is used for matching aliases/title/id, not
    for slug creation.
    """
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(text or "").strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _normalize_aliases(aliases: object) -> list[str]:
    if not isinstance(aliases, list):
        return []
    normalized: list[str] = []
    for alias in aliases:
        alias_text = str(alias or "").strip().lower()
        if alias_text and alias_text not in normalized:
            normalized.append(alias_text)
    return normalized


def canonicalize_project_record(project: dict) -> dict:
    """Return a project record with canonical identity fields.

    Existing legacy fields are preserved, but the returned record always
    exposes the canonical keys used by the rest of the app.
    """
    title = str(project.get("title") or project.get("name") or "").strip()
    slug = str(project.get("slug") or "").strip()
    project_id = str(project.get("id") or slug or "").strip()
    aliases = _normalize_aliases(project.get("aliases") or [])
    url = str(project.get("url") or project_url_from_slug(slug)).strip()

    canonical = dict(project)
    canonical["id"] = project_id or slug
    canonical["title"] = title
    canonical["name"] = title
    canonical["slug"] = slug
    canonical["url"] = url
    canonical["aliases"] = aliases
    return canonical


def project_url_from_slug(slug: str) -> str:
    """Return the canonical portfolio URL for a known slug."""
    slug_text = str(slug or "").strip()
    return f"/portfolio/{slug_text}" if slug_text else ""


def project_ref_token(project_id: str) -> str:
    """Return a structured reference token for a project id."""
    return f"[[PROJECT_REF:{normalize_project_text(project_id).replace(' ', '')}]]"


def project_reference_payload(project: dict) -> dict:
    """Return the canonical reference payload sent to or rendered from AI."""
    canonical = canonicalize_project_record(project)
    return {
        "project_id": canonical.get("id", ""),
        "title": canonical.get("title", ""),
        "url": canonical.get("url", ""),
        "aliases": canonical.get("aliases", []),
    }


def _candidate_values(project: dict) -> list[str]:
    aliases = project.get("aliases") or []
    values = [
        project.get("id", ""),
        project.get("title", ""),
        project.get("name", ""),
        project.get("slug", ""),
        project.get("url", ""),
        *aliases,
    ]
    return [str(value).strip() for value in values if str(value).strip()]


def _phrase_in_text(needle: str, haystack: str) -> bool:
    if not needle or not haystack:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) is not None


def _match_project_candidates(query_norm: str, project: dict) -> bool:
    if not query_norm:
        return False
    for candidate in _candidate_values(project):
        candidate_norm = normalize_project_text(candidate)
        if not candidate_norm:
            continue
        if _phrase_in_text(candidate_norm, query_norm):
            return True
    return False


def match_projects(query: str, projects: Iterable[dict]) -> list[dict]:
    """Return canonical projects matched by aliases/title/id/slug.

    Matching is deterministic: no slug inference, no fuzzy reconstruction.
    """
    query_norm = normalize_project_text(query)
    if not query_norm:
        return []

    matched: list[dict] = []
    for project in projects:
        canonical = canonicalize_project_record(project)
        if _match_project_candidates(query_norm, canonical):
            matched.append(canonical)
    return matched


def resolve_project(query: str, projects: Iterable[dict]) -> dict | None:
    """Resolve *query* to a single canonical project, or None.

    Logs the decision path to stderr for debugging.
    """
    query_norm = normalize_project_text(query)
    if not query_norm:
        print(
            "[PROJECT_RESOLVER] input='' matched=None slug=None reason=empty",
            file=sys.stderr,
        )
        return None

    canonical_projects = [canonicalize_project_record(project) for project in projects]
    matched = [
        project
        for project in canonical_projects
        if _match_project_candidates(query_norm, project)
    ]

    if len(matched) == 1:
        project = matched[0]
        print(
            f"[PROJECT_RESOLVER] input={query!r} matched={project.get('title')!r} "
            f"slug={project.get('slug')!r} reason=exact_phrase",
            file=sys.stderr,
        )
        return project

    if len(matched) > 1:
        print(
            f"[PROJECT_RESOLVER] input={query!r} matched=None slug=None reason=ambiguous",
            file=sys.stderr,
        )
        return None

    print(
        f"[PROJECT_RESOLVER] input={query!r} matched=None slug=None reason=unresolved",
        file=sys.stderr,
    )
    return None
