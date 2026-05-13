import json
import os
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_FILE = DATA_DIR / "projects.json"
CHAT_LOGS_DIR = DATA_DIR / "chat_logs"
POSTS_DIR = BASE_DIR / "posts"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHAT_LOGS_DIR.mkdir(exist_ok=True)
POSTS_DIR.mkdir(exist_ok=True)

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

def save_chat_log(messages: list[dict]):
    # Save a chat log with a timestamped filename
    if not messages:
        return
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}.json"
    filepath = CHAT_LOGS_DIR / filename
    
    log_data = {
        "timestamp": timestamp,
        "messages": messages
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

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
                    "message_count": len(data.get("messages", []))
                })
        except Exception:
            pass
            
    # Sort newest first
    return sorted(logs, key=lambda x: x["filename"], reverse=True)

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
