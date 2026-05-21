"""Post-process chat replies — case study links when model skips them."""

from __future__ import annotations

from harun_site.utils.context_builder import match_projects_for_query


def ensure_case_study_links(text: str, user_query: str) -> str:
    """Model linki unuttuysa, eşleşen projeler için markdown link ekle."""
    if not text or not user_query.strip():
        return text

    out = text.rstrip()
    for proj in match_projects_for_query(user_query):
        slug = (proj.get("slug") or "").strip()
        if not slug or not proj.get("case_study"):
            continue
        path = f"/projects/{slug}"
        if path in out:
            continue
        out += f"\n\n[→ Case Study'yi Gör]({path})"
    return out
