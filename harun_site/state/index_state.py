import reflex as rx
from typing import TypedDict


class RecentPostDict(TypedDict):
    slug: str
    title: str
    date: str
    description: str


class FeaturedProjectDict(TypedDict):
    name: str
    desc: str
    tags: list[str]


class ExperiencePreviewDict(TypedDict):
    company: str
    role: str
    description: str


class IndexState(rx.State):
    recent_posts: list[RecentPostDict] = []
    featured_projects: list[FeaturedProjectDict] = []
    experience_preview: list[ExperiencePreviewDict] = []
    query: str = ""

    @rx.event
    def on_load(self):
        from harun_site.utils.markdown_parser import get_all_posts
        from harun_site.utils.data_manager import load_projects, load_experience

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
        self.featured_projects = projects[:3]
        self.experience_preview = load_experience()[:1]

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