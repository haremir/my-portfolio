from __future__ import annotations

from datetime import datetime
from typing import TypedDict

import reflex as rx

from harun_site.utils.markdown_parser import get_all_posts


class PostDict(TypedDict):
    slug: str
    title: str
    title_en: str
    date: str
    month: str
    month_en: str
    day: str
    year: str
    description: str
    description_en: str
    tags: list[str]
    cover: str


class BlogState(rx.State):
    selected_tags: list[str] = []
    all_posts: list[PostDict] = []

    @rx.event
    def on_load(self):
        posts = get_all_posts()
        months_tr = {
            "01": "Oca", "02": "Şub", "03": "Mar", "04": "Nis",
            "05": "May", "06": "Haz", "07": "Tem", "08": "Ağu",
            "09": "Eyl", "10": "Eki", "11": "Kas", "12": "Ara"
        }
        
        months_en = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }

        self.all_posts = []
        for post in posts:
            try:
                dt = datetime.strptime(post.date, "%Y-%m-%d")
                month_tr = months_tr.get(dt.strftime("%m"), dt.strftime("%b"))
                month_en = months_en.get(dt.strftime("%m"), dt.strftime("%b"))
                day = dt.strftime("%d")
                year = dt.strftime("%Y")
            except Exception:
                month_tr, month_en, day, year = "", "", "", ""

            self.all_posts.append(
                PostDict(
                    slug=post.slug,
                    title=post.title,
                    title_en=getattr(post, "title_en", ""),
                    date=post.date,
                    month=month_tr.upper(),
                    month_en=month_en.upper(),
                    day=day,
                    year=year,
                    description=post.description,
                    description_en=getattr(post, "description_en", ""),
                    tags=post.tags,
                    cover=getattr(post, "cover", ""),
                )
            )

    @rx.event
    def toggle_tag(self, tag: str):
        if tag in self.selected_tags:
            self.selected_tags = [t for t in self.selected_tags if t != tag]
        else:
            self.selected_tags = self.selected_tags + [tag]

    @rx.event
    def clear_tags(self):
        self.selected_tags = []

    @rx.var
    def filtered_posts(self) -> list[PostDict]:
        if not self.selected_tags:
            return self.all_posts
        return [
            post
            for post in self.all_posts
            if any(t in post.get("tags", []) for t in self.selected_tags)
        ]

    @rx.var
    def selected_tags_str(self) -> str:
        return ",".join(self.selected_tags)

    @rx.var
    def has_filter(self) -> bool:
        return len(self.selected_tags) > 0

    @rx.var
    def all_tags(self) -> list[str]:
        tags: list[str] = []
        for post in self.all_posts:
            for tag in post.get("tags", []):
                if tag not in tags:
                    tags.append(tag)
        return tags