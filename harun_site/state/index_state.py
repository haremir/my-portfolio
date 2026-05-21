import reflex as rx
from typing import TypedDict


class RecentPostDict(TypedDict):
    slug: str
    title: str
    date: str
    description: str


class FeaturedProjectDict(TypedDict):
    slug: str
    name: str
    desc: str
    tags: list[str]


class ExperiencePreviewDict(TypedDict):
    company: str
    role: str
    description: str


class SkillCategoryDict(TypedDict):
    category: str
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
        from harun_site.utils.data_manager import load_projects, load_experience, load_skills

        posts = get_all_posts()
        self.recent_posts = [
            {
                "slug": p.slug,
                "title": p.title,
                "date": p.date,
                "description": p.description,
            }
            for p in posts[:2]
        ]
        
        projects = load_projects()
        self.featured_projects = [
            {
                "name": p.get("name", ""),
                "slug": p.get("slug", ""),
                "desc": p.get("desc", ""),
                "tags": [str(t) for t in (p.get("tags") or [])],
            }
            for p in projects[:3]
        ]
        
        experiences = load_experience()
        self.experience_preview = [
            {
                "company": e.get("company", ""),
                "role": e.get("role", ""),
                "description": e.get("description", ""),
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
