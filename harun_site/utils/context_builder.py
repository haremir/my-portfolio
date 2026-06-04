"""Portfolio context for Groq — routed by user intent + file mtime cache."""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path
import json

from harun_site.utils.data_manager import (
    DATA_DIR,
    PROJECTS_FILE,
    load_education,
    load_experience,
    load_projects,
    load_skills,
    get_localized,
)
from harun_site.utils.markdown_parser import get_all_posts
from harun_site.utils.project_registry import (
    match_projects,
    project_ref_token,
    project_reference_payload,
)

POSTS_DIR = DATA_DIR.parent / "posts"

_PERSONAL = """## Kişisel
- Harun Emirhan Bostancı · Erzurum · Data Science & AI Engineer | LLM Orchestrator
- Bilgisayar Mühendisliği mezunu · RAG, LLM, üretim odaklı AI/backend"""

_BLOG_KEYWORDS = ("blog", "yazı", "yazılar", "post", "makale")
_CAREER_KEYWORDS = (
    "iş", "kariyer", "deneyim", "cv", "özgeçmiş", "eğitim", "mezun",
    "proudsec", "staj", "freelance", "işbirliği", "iş birliği", "iletişim",
    "linkedin", "mail", "github", "recruiter", "işe alım",
)
_TECH_KEYWORDS = (
    "teknoloji", "tech", "stack", "beceri", "skill", "araç", "tool",
    "ne kullanıyor", "hangi dil", "programlama", "framework",
)
_DEEP_TECH_IN_QUERY = re.compile(
    r"(mimari|architecture|trade.?off|multi.?tenant|case\s*study|implementasyon|"
    r"production|ölçek|backend|rag|pipeline|postgresql|redis|fastapi)",
    re.I,
)


def _data_fingerprint() -> str:
    parts: list[str] = []
    for path in (PROJECTS_FILE, POSTS_DIR):
        p = Path(path)
        if p.exists():
            if p.is_file():
                parts.append(f"{p}:{p.stat().st_mtime_ns}")
            else:
                for child in sorted(p.glob("*.md")):
                    parts.append(f"{child}:{child.stat().st_mtime_ns}")
    try:
        for row in load_education() + load_experience():
            parts.append(str(row))
    except Exception:
        pass
    return "|".join(parts)


@lru_cache(maxsize=8)
def _cached_projects(_fp: str) -> list[dict]:
    return load_projects()


@lru_cache(maxsize=8)
def _cached_posts(_fp: str) -> list:
    try:
        return get_all_posts()
    except Exception:
        return []


def _last_user_text(messages: list[dict]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _match_posts(query: str, posts: list) -> list:
    q = query.lower()
    return [
        p for p in posts
        if p.title.lower() in q
        or any(t.lower() in q for t in (p.tags or []))
        or (p.slug and p.slug.lower() in q)
    ]


def _project_block(proj: dict, *, detailed: bool, lang: str = "tr") -> str:
    title = proj.get("title", proj.get("name", ""))
    url = proj.get("url", "")
    payload = project_reference_payload(proj)
    has_cs = bool(proj.get("case_study"))
    lines = [
        f"### {title}",
        project_ref_token(payload.get("project_id", "")),
        json.dumps(payload, ensure_ascii=False),
        f"- Özet: {get_localized(proj, 'desc', lang)}",
        f"- Teknolojiler: {', '.join(proj.get('tags') or [])}",
        f"- ID: {proj.get('id', '')}",
        f"- URL: {url}",
    ]
    if has_cs and url:
        lines.append(f"- Case Study: {url}")
    if detailed and has_cs:
        cs = proj.get("case_study") or {}
        for key, label in (
            ("problem", "Problem"),
            ("architecture", "Mimari"),
            ("why_this_stack", "Stack"),
            ("stack_reason", "Stack"),
            ("challenges", "Zorluklar"),
            ("lessons_learned", "Öğrenilenler"),
            ("learnings", "Öğrenilenler"),
        ):
            val = get_localized(cs, key, lang)
            if isinstance(val, str) and val.strip() and "placeholder" not in val.lower():
                lines.append(f"- {label}: {val[:280]}")
    return "\n".join(lines)


def _projects_index(projects: list[dict], *, exclude_slugs: set[str] | None = None, lang: str = "tr") -> str:
    exclude = exclude_slugs or set()
    lines = ["## Proje indeksi (kısa)" if lang == "tr" else "## Project index (short)"]
    for proj in projects:
        slug = proj.get("slug", "")
        if slug in exclude:
            continue
        cs = " [CS]" if proj.get("case_study") else ""
        lines.append(
            f"- {proj.get('title', proj.get('name', ''))}: {get_localized(proj, 'desc', lang)[:100]} "
            f"({', '.join((proj.get('tags') or [])[:4])}){cs}"
        )
    return "\n".join(lines)


def _experience_section(lang: str = "tr") -> str:
    experiences = load_experience()
    if not experiences:
        return ""
    lines = ["## İş deneyimi" if lang == "tr" else "## Work Experience"]
    role_key = "role_en" if lang == "en" else "role"
    desc_key = "description_en" if lang == "en" else "description"
    for exp in experiences:
        lines.append(
            f"- {exp.get('company', '')} / {exp.get(role_key, '')} "
            f"({exp.get('start_date', '')}–{exp.get('end_date', '')}): "
            f"{(exp.get(desc_key) or '')[:200]}"
        )
    return "\n".join(lines)


def _education_section(lang: str = "tr") -> str:
    education = load_education()
    if not education:
        return ""
    lines = ["## Eğitim" if lang == "tr" else "## Education"]
    dept_key = "department_en" if lang == "en" else "department"
    degree_key = "degree_en" if lang == "en" else "degree"
    for edu in education:
        degree_part = f" ({edu.get(degree_key)})" if edu.get(degree_key) else ""
        lines.append(
            f"- {edu.get('school', '')} · {edu.get(dept_key, '')}{degree_part} "
            f"({edu.get('start_year', '')}–{edu.get('end_year', '')})"
        )
    return "\n".join(lines)


def _blog_section(posts: list, *, matched: list | None = None, lang: str = "tr") -> str:
    if not posts:
        return ""
    show = matched if matched else posts[:5]
    lines = ["## Blog"]
    title_key = "title_en" if lang == "en" else "title"
    desc_key = "description_en" if lang == "en" else "description"
    for post in show:
        title = getattr(post, title_key, "") or post.title
        desc = getattr(post, desc_key, "") or post.description
        lines.append(
            f"- {title} ({post.date}): {desc} "
            f"[{', '.join(post.tags[:4])}]"
        )
    return "\n".join(lines)


def _skills_section(lang: str = "tr") -> str:
    skills = load_skills()
    if not skills:
        return ""
    lines = ["## Beceriler (kategorili)" if lang == "tr" else "## Skills (categorized)"]
    cat_key = "category_en" if lang == "en" else "category"
    for cat in skills:
        category = cat.get(cat_key, cat.get("category", ""))
        skills_list = cat.get("skills", [])
        if category and skills_list:
            lines.append(f"- **{category}**: {', '.join(skills_list)}")
    return "\n".join(lines)


def match_projects_for_query(query: str) -> list[dict]:
    """Projeleri kullanıcı metnine göre eşleştir (context routing ile aynı)."""
    fp = _data_fingerprint()
    return match_projects(query, _cached_projects(fp))


def build_case_study_directive(query: str) -> str:
    """LLM'e ilk yanıtta case study linki zorunluluğu — token dostu kısa blok."""
    matched = match_projects_for_query(query)
    lines: list[str] = []
    
    for proj in matched[:3]:
        payload = project_reference_payload(proj)
        if not payload.get("url") or not proj.get("case_study"):
            continue
        lines.append(
            f"- {payload['title']}: yanıtın sonuna mutlaka ekle → "
            f"{project_ref_token(payload['project_id'])}"
        )
        lines.append(json.dumps(payload, ensure_ascii=False))
        lines.append(
            "- Project names and URLs are immutable registry-controlled identifiers. "
            "Never invent, rewrite, pluralize, abbreviate, or autocorrect them."
        )
    
    if not lines:
        return ""
    return "## ZORUNLU (bu tur)\n" + "\n".join(lines)


def build_context_for_query(query: str, lang: str = "tr") -> str:
    """Intent-routed context — smaller than full dump for most messages."""
    fp = _data_fingerprint()
    projects = _cached_projects(fp)
    posts = _cached_posts(fp)
    q = query.lower()

    sections = [_PERSONAL]
    matched_projects = match_projects(query, projects)
    matched_posts = _match_posts(query, posts) if posts else []

    # Always include categorized skills for tech/skill queries
    skills_ctx = _skills_section(lang)
    is_tech_query = any(k in q for k in _TECH_KEYWORDS)

    # Intro or personal about keywords
    _INTRO_KEYWORDS = ("kimsin", "kendinden", "tanıt", "hakkında", "biyografi", "özet", "who are you", "yourself", "introduce", "about you")
    is_intro_query = any(k in q for k in _INTRO_KEYWORDS)

    if matched_projects:
        detailed = bool(_DEEP_TECH_IN_QUERY.search(query))
        sections.append("## İlgili proje(ler)" if lang == "tr" else "## Related project(s)")
        for proj in matched_projects[:2]:
            sections.append(_project_block(proj, detailed=detailed, lang=lang))
        exclude = {p.get("slug", "") for p in matched_projects}
        sections.append(_projects_index(projects, exclude_slugs=exclude, lang=lang))

    elif is_tech_query:
        if skills_ctx:
            sections.append(skills_ctx)
        sections.append(_projects_index(projects, lang=lang))

    elif any(k in q for k in _BLOG_KEYWORDS) or matched_posts:
        sections.append(_blog_section(posts, matched=matched_posts or None, lang=lang))

    elif any(k in q for k in _CAREER_KEYWORDS) or is_intro_query:
        exp = _experience_section(lang)
        edu = _education_section(lang)
        if exp:
            sections.append(exp)
        if edu:
            sections.append(edu)
        if skills_ctx:
            sections.append(skills_ctx)
        sections.append(_projects_index(projects, lang=lang))

    else:
        # Fallback to general info including all experiences, education, and skills.
        # This ensures the chatbot has a comprehensive view for greetings or general questions.
        exp = _experience_section(lang)
        edu = _education_section(lang)
        if exp:
            sections.append(exp)
        if edu:
            sections.append(edu)
        if skills_ctx:
            sections.append(skills_ctx)
        sections.append(_projects_index(projects, lang=lang))

    ctx = "\n\n".join(s for s in sections if s.strip())
    print(
        f"[GROQ] Context routed: {len(ctx)} chars "
        f"projects={len(matched_projects)} blog={bool(matched_posts)}",
        file=sys.stderr,
    )
    return ctx


def build_context_for_messages(messages: list[dict], lang: str = "tr") -> str:
    return build_context_for_query(_last_user_text(messages), lang=lang)


def build_context() -> str:
    """Legacy full context — prefer build_context_for_messages in chat."""
    return build_context_for_query("", "tr")
