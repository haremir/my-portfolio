import json
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from harun_site.utils.project_registry import canonicalize_project_record, resolve_project


# ---------------------------------------------------------------------------
# Atomic JSON write helper
# ---------------------------------------------------------------------------

def _atomic_write_json(path: Path, data: object) -> None:
    """
    Write *data* as JSON to *path* atomically.

    Writes to a sibling temp file first, then renames it over the target.
    This guarantees the target is never left in a half-written state — a
    crash mid-write leaves a .tmp file that is cleaned up on the next call,
    while the original file remains intact.

    Raises
    ------
    OSError   – if the filesystem is full or permissions are wrong.
    TypeError – if *data* is not JSON-serialisable.
    """
    path = Path(path)  # ensure Path object
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write temp file in the OS temp dir — NOT next to the target path.
    # Reflex dev hot-reload watches project dirs; a .tmp under data/ triggers
    # a full backend restart and wipes in-memory chat state.
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=path.stem + "_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(tmp_path_str, str(path))
    except Exception:
        # Best-effort cleanup of the temp file on failure
        try:
            os.unlink(tmp_path_str)
        except OSError:
            pass
        raise

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
_BASE_DIR = BASE_DIR
DATA_DIR = BASE_DIR / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
CHAT_LOGS_DIR = DATA_DIR / "chat_logs"
POSTS_DIR = BASE_DIR / "posts"
SUMMARIES_DIR = DATA_DIR / "summaries"
TAGS_FILE = DATA_DIR / "tags.json"
CV_DIR = BASE_DIR / "assets" / "cv"
SKILLS_FILE = DATA_DIR / "skills.json"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHAT_LOGS_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)
SUMMARIES_DIR.mkdir(exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)

# ---- SKILLS ----

def load_skills() -> list[dict]:
    if not SKILLS_FILE.exists():
        return []
    try:
        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_skills(skills: list[dict]):
    _atomic_write_json(SKILLS_FILE, skills)

# ---- PROJECTS ----

def load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            raw_projects = json.load(f)
        if not isinstance(raw_projects, list):
            return []
        return [canonicalize_project_record(project) for project in raw_projects if isinstance(project, dict)]
    except Exception:
        return []

def save_projects(projects: list[dict]):
    canonical_projects = [canonicalize_project_record(project) for project in projects if isinstance(project, dict)]
    _atomic_write_json(PROJECTS_FILE, canonical_projects)

def add_project(name: str, desc: str, tags: list[str]):
    raise NotImplementedError("Use explicit canonical project data with id/title/slug/url/aliases.")

from typing import Union

def get_project_by_slug(slug: str) -> Union[dict, None]:
    slug = slug.strip().strip('/')
    if not slug:
        return None
    projects = load_projects()
    for p in projects:
        if isinstance(p, dict) and p.get("slug", "") == slug:
            return p
    return resolve_project(slug, projects)

def delete_project(index: int):
    projects = load_projects()
    if 0 <= index < len(projects):
        projects.pop(index)
        save_projects(projects)

# ---- BLOG POSTS ----

def delete_blog_post(slug: str):
    post_path = POSTS_DIR / f"{slug}.md"
    if post_path.exists():
        post_path.unlink()

def save_blog_post(slug: str, title: str, date: str, description: str, tags: list[str], content: str, cover: str = ""):
    post_path = POSTS_DIR / f"{slug}.md"

    # Format tags for frontmatter
    tags_formatted = "\n".join([f"  - {t}" for t in tags])

    frontmatter = f"""---
title: "{title}"
date: "{date}"
description: "{description}"
tags:
{tags_formatted}
cover: "{cover}"
---
"""

    # Blog posts are markdown so we can't use _atomic_write_json (non-JSON).
    # Use the same temp-file-then-rename pattern manually.
    import shutil as _shutil, tempfile as _tmp
    fd, tmp_str = _tmp.mkstemp(prefix=slug + "_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(frontmatter + "\n" + content)
        _shutil.move(tmp_str, str(post_path))
    except Exception:
        try: os.unlink(tmp_str)
        except OSError: pass
        raise

# ---- CHAT LOGS ----

def save_chat_log(messages: list[dict], filename: str | None = None) -> str:
    # Save a chat log with a timestamped filename, or overwrite an existing one.
    if not messages:
        return ""

    if not filename:
        filename = f"{uuid4().hex}.json"
    filepath = CHAT_LOGS_DIR / filename

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "messages": messages
    }

    _atomic_write_json(filepath, log_data)
    return filename

def load_chat_logs() -> list[dict]:
    logs = []
    if not CHAT_LOGS_DIR.exists():
        return logs

    for path in CHAT_LOGS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = data.get("messages", [])
                user_count = sum(1 for m in messages if m.get("role") == "user")
                asst_count = sum(1 for m in messages if m.get("role") == "assistant")
                logs.append({
                    "filename": path.name,
                    "timestamp": data.get("timestamp", ""),
                    "mtime": path.stat().st_mtime,
                    # Geriye uyumluluk — toplam mesaj
                    "message_count": len(messages),
                    # Ayrıntılı sayımlar
                    "user_message_count": user_count,
                    "assistant_message_count": asst_count,
                })
        except Exception:
            pass

    # Sort newest first using saved timestamp when available.
    return sorted(logs, key=lambda x: (x.get("timestamp") or "", x.get("mtime", 0)), reverse=True)

def load_chat_log_messages(filename: str) -> list[dict]:
    filepath = CHAT_LOGS_DIR / filename
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            messages = data.get("messages", [])
            normalized_messages: list[dict] = []
            for message in messages:
                if not isinstance(message, dict):
                    continue
                role = message.get("role", "")
                content = message.get("content", "")
                if content is None:
                    content = ""
                elif isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False)
                elif isinstance(content, list):
                    content = "\n".join(str(item) for item in content if item is not None)
                elif not isinstance(content, str):
                    content = str(content)
                normalized_messages.append({"role": str(role), "content": content})
            return normalized_messages
    except Exception:
        return []

def delete_chat_log(filename: str):
    filepath = CHAT_LOGS_DIR / filename
    if filepath.exists():
        filepath.unlink()

def clear_all_chat_logs():
    # Delete all files in chat_logs and summaries directories
    for f in CHAT_LOGS_DIR.glob("*.json"):
        f.unlink()
    for f in SUMMARIES_DIR.glob("*.json"):
        f.unlink()
    clear_dashboard_overview_cache()

# ---- ADMIN DASHBOARD OVERVIEW CACHE ----

DASHBOARD_OVERVIEW_CACHE = SUMMARIES_DIR / "dashboard_overview_cache.json"


def load_dashboard_overview_cache(fingerprint: str) -> dict | None:
    if not DASHBOARD_OVERVIEW_CACHE.exists():
        return None
    try:
        data = json.loads(DASHBOARD_OVERVIEW_CACHE.read_text(encoding="utf-8"))
        if data.get("fingerprint") == fingerprint:
            return data.get("overview")
    except Exception:
        pass
    return None


def save_dashboard_overview_cache(fingerprint: str, overview: dict) -> None:
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(
        DASHBOARD_OVERVIEW_CACHE,
        {"fingerprint": fingerprint, "overview": overview},
    )


def clear_dashboard_overview_cache() -> None:
    if DASHBOARD_OVERVIEW_CACHE.exists():
        DASHBOARD_OVERVIEW_CACHE.unlink()


# ---- CHAT SUMMARIES ----

def save_chat_summary(data: dict):
    from datetime import datetime
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
    data["date"] = datetime.now().isoformat()
    (SUMMARIES_DIR / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ---- TAGS ----

def load_categorized_tags() -> list:
    """Return tags grouped by category: [{"category": str, "tags": [str]}]."""
    if not TAGS_FILE.exists():
        return []
    try:
        data = json.loads(TAGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
    # Support both old flat list and new categorized format
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data
    # Legacy flat list – wrap in a single "Genel" category
    if isinstance(data, list):
        return [{"category": "Genel", "tags": data}]
    return []


def load_tags() -> list:
    """Return all tags as a flat list (backward compatible)."""
    cats = load_categorized_tags()
    flat = []
    for cat in cats:
        for tag in cat.get("tags", []):
            if tag not in flat:
                flat.append(tag)
    return flat


def save_tags(tags):
    """Save tags – accepts either flat list or categorized list."""
    _atomic_write_json(TAGS_FILE, tags)


def add_tag(tag: str, category: str = ""):
    """Add a tag. If category given and categorized format, add under that category."""
    cats = load_categorized_tags()
    # Check if already exists
    for cat in cats:
        if tag in cat.get("tags", []):
            return
    if category:
        for cat in cats:
            if cat.get("category", "") == category:
                cat["tags"].append(tag)
                save_tags(cats)
                return
        # Category not found, create it
        cats.append({"category": category, "tags": [tag]})
        save_tags(cats)
    else:
        # Add to last category or create "Diğer"
        if cats:
            cats[-1].get("tags", []).append(tag)
        else:
            cats = [{"category": "Diğer", "tags": [tag]}]
        save_tags(cats)


def delete_tag(tag: str):
    cats = load_categorized_tags()
    changed = False
    for cat in cats:
        tags_list = cat.get("tags", [])
        if tag in tags_list:
            cat["tags"] = [t for t in tags_list if t != tag]
            changed = True
    if changed:
        save_tags(cats)



# ---- CHAT SUGGESTIONS ----

def load_suggestions() -> list[str]:
    path = _BASE_DIR / "data" / "suggestions.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_suggestions(suggestions: list[str]):
    _atomic_write_json(_BASE_DIR / "data" / "suggestions.json", suggestions)

# ---- CV ----

def save_cv(file_data: bytes, filename: str) -> str:
    CV_DIR.mkdir(parents=True, exist_ok=True)
    # Clear previous CVs
    for old in CV_DIR.glob("*.pdf"):
        old.unlink()
    path = CV_DIR / filename
    path.write_bytes(file_data)
    return f"/cv/{filename}"

def get_cv_path() -> str:
    if not CV_DIR.exists():
        return ""
    files = list(CV_DIR.glob("*.pdf"))
    return f"/cv/{files[0].name}" if files else ""


# ---- EDUCATION & EXPERIENCE ----

def load_education() -> list[dict]:
    path = BASE_DIR / "data" / "education.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_education(data: list[dict]):
    _atomic_write_json(BASE_DIR / "data" / "education.json", data)


def load_experience() -> list[dict]:
    path = BASE_DIR / "data" / "experience.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_experience(data: list[dict]):
    _atomic_write_json(BASE_DIR / "data" / "experience.json", data)
