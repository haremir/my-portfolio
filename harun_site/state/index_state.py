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
        # Strip each project to only the fields FeaturedProjectDict declares.
        # load_projects() returns full dicts that include a nested case_study
        # object — that nested dict must never reach the frontend state delta.
        self.featured_projects = [
            {
                "name": p.get("name", ""),
                "slug": p.get("slug", ""),
                "desc": p.get("desc", ""),
                "tags": [str(t) for t in (p.get("tags") or [])],
            }
            for p in projects[:3]
        ]
        # Strip experience_preview to only the three fields ExperiencePreviewDict
        # declares.  load_experience() returns dicts with tags list and other
        # extra keys — those must not be serialised into the state delta.
        experiences = load_experience()
        self.experience_preview = [
            {
                "company": e.get("company", ""),
                "role": e.get("role", ""),
                "description": e.get("description", ""),
            }
            for e in experiences[:1]
        ]

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
