import json
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
CHAT_LOGS_DIR = DATA_DIR / "chat_logs"
POSTS_DIR = BASE_DIR / "posts"
SUMMARIES_DIR = DATA_DIR / "summaries"
TAGS_FILE = DATA_DIR / "tags.json"
CV_DIR = BASE_DIR / "assets" / "cv"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHAT_LOGS_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)
SUMMARIES_DIR.mkdir(exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True)

# ---- PROJECTS ----

def load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_projects(projects: list[dict]):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

def add_project(name: str, desc: str, tags: list[str]):
    projects = load_projects()
    projects.append({"name": name, "desc": desc, "tags": tags})
    save_projects(projects)

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
    
    with open(post_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + "\n" + content)

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
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    return filename

def load_chat_logs() -> list[dict]:
    logs = []
    if not CHAT_LOGS_DIR.exists():
        return logs
        
    for path in CHAT_LOGS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logs.append({
                    "filename": path.name,
                    "timestamp": data.get("timestamp", ""),
                    "mtime": path.stat().st_mtime,
                    "message_count": len(data.get("messages", []))
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
            return data.get("messages", [])
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

def load_tags() -> list[str]:
    if not TAGS_FILE.exists():
        return []
    try:
        return json.loads(TAGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_tags(tags: list[str]):
    TAGS_FILE.write_text(json.dumps(tags, ensure_ascii=False, indent=2), encoding="utf-8")

def add_tag(tag: str):
    tags = load_tags()
    if tag not in tags:
        tags.append(tag)
        save_tags(tags)

def delete_tag(tag: str):
    tags = load_tags()
    if tag in tags:
        tags = [item for item in tags if item != tag]
        save_tags(tags)

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
    path = BASE_DIR / "data" / "education.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_experience() -> list[dict]:
    path = BASE_DIR / "data" / "experience.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_experience(data: list[dict]):
    path = BASE_DIR / "data" / "experience.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
