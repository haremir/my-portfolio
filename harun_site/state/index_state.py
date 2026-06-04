import reflex as rx
from typing import TypedDict


class RecentPostDict(TypedDict):
    slug: str
    title: str
    title_en: str
    date: str
    description: str
    description_en: str


class FeaturedProjectDict(TypedDict):
    id: str
    title: str
    slug: str
    url: str
    aliases: list[str]
    name: str
    desc: str
    desc_tr: str
    desc_en: str
    tags: list[str]


class ExperiencePreviewDict(TypedDict):
    company: str
    role: str
    role_en: str
    description: str
    description_en: str


class SkillCategoryDict(TypedDict):
    category: str
    category_en: str
    skills: list[str]


class IndexState(rx.State):
    recent_posts: list[RecentPostDict] = []
    featured_projects: list[FeaturedProjectDict] = []
    experience_preview: list[ExperiencePreviewDict] = []
    skills_list: list[SkillCategoryDict] = []
    query: str = ""

    @rx.event
    def on_load(self):
        from harun_site.utils.markdown_parser import get_all_posts
        from harun_site.utils.data_manager import load_projects, load_experience, load_skills, get_localized

        posts = get_all_posts()
        self.recent_posts = [
            {
                "slug": p.slug,
                "title": p.title,
                "title_en": getattr(p, "title_en", ""),
                "date": p.date,
                "description": p.description,
                "description_en": getattr(p, "description_en", ""),
            }
            for p in posts[:2]
        ]
        
        projects = load_projects()
        self.featured_projects = [
            {
                "id": p.get("id", ""),
                "title": p.get("title", p.get("name", "")),
                "slug": p.get("slug", ""),
                "url": p.get("url", ""),
                "aliases": [str(a) for a in (p.get("aliases") or [])],
                "name": p.get("title", p.get("name", "")),
                "desc": p.get("desc", ""),
                "desc_tr": get_localized(p, "desc", "tr"),
                "desc_en": get_localized(p, "desc", "en"),
                "tags": [str(t) for t in (p.get("tags") or [])],
            }
            for p in projects[:3]
        ]
        
        experiences = load_experience()
        self.experience_preview = [
            {
                "company": e.get("company", ""),
                "role": e.get("role", ""),
                "role_en": e.get("role_en", e.get("role", "")),
                "description": e.get("description", ""),
                "description_en": e.get("description_en", e.get("description", "")),
            }
            for e in experiences[:1]
        ]
        
        self.skills_list = load_skills()

    @rx.event
    def set_query(self, value: str):
        self.query = value

    @rx.event
    def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
        if key == "Enter":
            return self.submit_query()

    @rx.event
    def submit_query(self):
        if self.query.strip():
            return rx.redirect(f"/chat?q={self.query}")
