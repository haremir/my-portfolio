from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter


@dataclass
class BlogPost:
	slug: str
	title: str
	date: str
	description: str
	tags: list[str]
	content: str
	cover: str = ""
	title_en: str = ""
	description_en: str = ""
	content_en: str = ""


def _posts_dir() -> Path:
	return Path(__file__).resolve().parents[2] / "posts"


def _parse_post(path: Path) -> BlogPost | None:
	try:
		post = frontmatter.load(path)
	except Exception:
		return None

	title = post.get("title")
	date = post.get("date")
	description = post.get("description")
	tags = post.get("tags")

	if not all([title, date, description, tags]):
		return None
	if not isinstance(tags, list):
		return None

	slug = path.stem
	cover = ""
	if hasattr(post, "metadata") and isinstance(post.metadata, dict):
		cover = str(post.metadata.get("cover", "") or "")

	# Bilingual fields — optional, fallback to empty string if not present
	title_en = str(post.get("title_en") or "")
	description_en = str(post.get("description_en") or "")
	content_en = str(post.get("content_en") or "")

	return BlogPost(
		slug=slug,
		title=str(title),
		date=str(date),
		description=str(description),
		tags=[str(tag) for tag in tags],
		content=post.content or "",
		cover=cover,
		title_en=title_en,
		description_en=description_en,
		content_en=content_en,
	)


def get_all_posts() -> list[BlogPost]:
	posts_dir = _posts_dir()
	if not posts_dir.exists():
		return []

	posts: list[BlogPost] = []
	for path in posts_dir.glob("*.md"):
		parsed = _parse_post(path)
		if parsed is not None:
			posts.append(parsed)

	return sorted(posts, key=lambda item: item.date, reverse=True)


def get_post_by_slug(slug: str) -> BlogPost | None:
	posts_dir = _posts_dir()
	path = posts_dir / f"{slug}.md"
	if not path.exists():
		return None

	return _parse_post(path)