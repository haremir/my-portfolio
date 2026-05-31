import reflex as rx
from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.theme import (
    BG,
    BG_CARD,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    BORDER,
    ACCENT,
    GLOW_PRIMARY,
    FONT_SANS,
    FONT_MONO,
)
from typing import TypedDict

class ProjectDict(TypedDict, total=False):
    id: str
    title: str
    name: str
    slug: str
    url: str
    aliases: list[str]
    desc: str
    tags: list[str]

class CategorizedTagDict(TypedDict):
    category: str
    tags: list[str]

class PortfolioState(rx.State):
    projects: list[ProjectDict] = []
    selected_tags: list[str] = []
    # ── Flat primitive vars for the detail modal ─────────────────────────────
    # NEVER store the full project dict in state — it carries a nested
    # case_study object that Reflex serialises to the frontend as a JS object
    # and any .get() call on the Var evaluates on the JS side → [object Object].
    modal_name: str = ""
    modal_desc: str = ""
    modal_tags: list[str] = []
    modal_slug: str = ""
    modal_url: str = ""
    is_modal_open: bool = False
    show_filters: bool = False

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_projects
        raw = load_projects()
        # Strip each project to only the four fields ProjectDict declares so
        # the nested case_study dict is never included in the state delta.
        self.projects = [
            {
                "id": p.get("id", ""),
                "title": p.get("title", p.get("name", "")),
                "name": p.get("name", ""),
                "slug": p.get("slug", ""),
                "url": p.get("url", ""),
                "aliases": [str(a) for a in (p.get("aliases") or [])],
                "desc": p.get("desc", ""),
                "tags": [str(t) for t in (p.get("tags") or [])],
            }
            for p in raw
        ]

    @rx.event
    def open_project(self, project: ProjectDict):
        # Flatten into primitive state vars — never store the raw dict.
        self.modal_name = str(project.get("name", ""))
        self.modal_desc = str(project.get("desc", ""))
        self.modal_tags = [str(t) for t in (project.get("tags") or [])]
        self.modal_slug = str(project.get("slug", ""))
        self.modal_url = str(project.get("url", ""))
        self.is_modal_open = True

    @rx.event
    def close_modal(self):
        self.modal_name = ""
        self.modal_desc = ""
        self.modal_tags = []
        self.modal_slug = ""
        self.modal_url = ""
        self.is_modal_open = False

    @rx.event
    def toggle_show_filters(self):
        self.show_filters = not self.show_filters

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
    def filtered_projects(self) -> list[ProjectDict]:
        if not self.selected_tags:
            return self.projects
        return [
            p
            for p in self.projects
            if any(t in p.get("tags", []) for t in self.selected_tags)
        ]

    @rx.var
    def selected_tags_str(self) -> str:
        return ",".join(self.selected_tags)

    @rx.var
    def has_filter(self) -> bool:
        return len(self.selected_tags) > 0

    @rx.var
    def categorized_tags(self) -> list[CategorizedTagDict]:
        from harun_site.utils.data_manager import load_categorized_tags
        cats = load_categorized_tags()
        project_tags = {tag for p in self.projects for tag in p.get("tags", [])}
        
        result = []
        for cat in cats:
            name = cat.get("category", "")
            tags = [t for t in cat.get("tags", []) if t in project_tags]
            if tags:
                result.append({"category": name, "tags": tags})
                
        # Handle any uncategorized tags that might exist in projects
        categorized_set = {t for cat in cats for t in cat.get("tags", [])}
        other_tags = [t for t in project_tags if t not in categorized_set]
        if other_tags:
            result.append({"category": "Diğer", "tags": sorted(other_tags)})
            
        return result


def category_tag_row(cat: rx.Var[CategorizedTagDict]) -> rx.Component:
    return rx.vstack(
        rx.text(
            cat["category"],
            font_family=FONT_MONO,
            font_size="0.72em",
            letter_spacing="0.1em",
            color=PRIMARY,
            text_transform="uppercase",
            font_weight="bold",
        ),
        rx.flex(
            rx.foreach(
                cat["tags"],
                lambda tag: rx.button(
                    tag,
                    on_click=PortfolioState.toggle_tag(tag),
                    font_family=FONT_MONO,
                    font_size="0.72em",
                    padding="0.25em 0.75em",
                    border_radius="4px",
                    cursor="pointer",
                    transition="all 150ms",
                    background=rx.cond(
                        PortfolioState.selected_tags_str.contains(tag),
                        PRIMARY,
                        "transparent",
                    ),
                    color=rx.cond(
                        PortfolioState.selected_tags_str.contains(tag),
                        BG,
                        TEXT_MUTED,
                    ),
                    border=rx.cond(
                        PortfolioState.selected_tags_str.contains(tag),
                        f"1px solid {PRIMARY}",
                        f"1px solid {BORDER}",
                    ),
                    _hover={
                        "border_color": PRIMARY,
                        "color": TEXT,
                        "background": f"{PRIMARY}15",
                    },
                ),
            ),
            wrap="wrap",
            gap="0.5em",
            width="100%",
        ),
        align_items="start",
        gap="0.4em",
        width="100%",
        border_left=f"2px solid {BORDER}",
        padding_left="1em",
        margin_bottom="1.2em",
    )


def project_card(project: ProjectDict) -> rx.Component:
    return rx.box(
        rx.text(
            "→",
            font_family=FONT_MONO,
            color=PRIMARY,
            font_size="1.4em",
            font_weight="700",
            opacity="0.35",
            min_width="2.5em",
        ),
        rx.vstack(
            rx.text(
                project["title"],
                font_family=FONT_SANS,
                font_weight="700",
                color=TEXT,
                font_size="1.05em",
            ),
            rx.text(
                project["desc"],
                font_family=FONT_SANS,
                color=TEXT_MUTED,
                font_size="0.87em",
                line_height="1.6",
            ),
            rx.hstack(
                rx.foreach(
                    project["tags"],
                    lambda tag: rx.text(
                        tag,
                        font_family=FONT_MONO,
                        font_size="0.7em",
                        color=PRIMARY,
                        border=f"1px solid {BORDER}",
                        padding="0.15em 0.5em",
                        border_radius="3px",
                    ),
                ),
                wrap="wrap",
                style={"gap": "0.4em"},
            ),
            rx.cond(
                project.contains("url") & (project["url"] != ""),
                rx.link(
                    "Case Study →",
                    href=project["url"],
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    color=PRIMARY,
                    text_decoration="none",
                    _hover={"text_shadow": GLOW_PRIMARY},
                    margin_top="0.8em",
                    display="block",
                    on_click=rx.stop_propagation,
                ),
                rx.fragment(),
            ),
            align_items="start",
            gap="0.4em",
            flex="1",
            ),
            on_click=PortfolioState.open_project(project),
        width="100%",
        align_items="start",
        gap="1.5em",
        padding="1.5em",
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        margin_bottom="1em",
        transition="all 200ms",
        _hover={"border_color": PRIMARY, "box_shadow": GLOW_PRIMARY},
        cursor="pointer",
    )


def portfolio_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.vstack(
                    rx.text(
                        "PORTFOLYO",
                        font_family=FONT_MONO,
                        font_size="0.75em",
                        letter_spacing="0.2em",
                        color=PRIMARY,
                        text_shadow=GLOW_PRIMARY,
                    ),
                    rx.text(
                        "Projeler, yarışmalar ve başarılar",
                        font_family=FONT_SANS,
                        color=TEXT_MUTED,
                        font_size="0.85em",
                    ),
                    align_items="start",
                    gap="0.2em",
                    width="100%",
                    margin_bottom="1.5em",
                ),
                rx.vstack(
                    # Toggle header & clear button
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.cond(
                                    PortfolioState.show_filters,
                                    rx.text("▲ Filtreleri Gizle", font_family=FONT_MONO, font_size="0.75em"),
                                    rx.text("▼ Filtreleri Göster (Etikete Göre Ara)", font_family=FONT_MONO, font_size="0.75em"),
                                ),
                                gap="0.3em",
                                align="center",
                            ),
                            on_click=PortfolioState.toggle_show_filters,
                            background="transparent",
                            border=f"1px solid {BORDER}",
                            color=PRIMARY,
                            padding="0.4em 0.9em",
                            border_radius="6px",
                            cursor="pointer",
                            transition="all 150ms",
                            _hover={"background": f"{PRIMARY}15", "border_color": PRIMARY},
                        ),
                        rx.cond(
                            PortfolioState.has_filter,
                            rx.button(
                                "✕ temizle",
                                on_click=PortfolioState.clear_tags,
                                font_family=FONT_MONO,
                                font_size="0.72em",
                                padding="0.4em 0.9em",
                                border_radius="6px",
                                background="transparent",
                                color=ACCENT,
                                border=f"1px solid {ACCENT}66",
                                cursor="pointer",
                                transition="all 150ms",
                                _hover={"border_color": ACCENT, "color": ACCENT, "background": f"{ACCENT}15"},
                            ),
                            rx.fragment(),
                        ),
                        justify="between",
                        align="center",
                        width="100%",
                        margin_bottom="1em",
                    ),
                    # Selected tags summary pills (always visible if filtering is active)
                    rx.cond(
                        PortfolioState.has_filter,
                        rx.flex(
                            rx.text("Aktif Filtreler:", font_family=FONT_MONO, font_size="0.7em", color=TEXT_MUTED, margin_right="0.5em", margin_top="0.35em"),
                            rx.foreach(
                                PortfolioState.selected_tags,
                                lambda tag: rx.button(
                                    tag + " ✕",
                                    on_click=PortfolioState.toggle_tag(tag),
                                    font_family=FONT_MONO,
                                    font_size="0.7em",
                                    padding="0.15em 0.5em",
                                    border_radius="3px",
                                    background=PRIMARY,
                                    color=BG,
                                    border=f"1px solid {PRIMARY}",
                                    cursor="pointer",
                                    margin_bottom="0.4em",
                                    margin_right="0.4em",
                                ),
                            ),
                            wrap="wrap",
                            width="100%",
                            margin_bottom="1em",
                        ),
                        rx.fragment(),
                    ),
                    # Collapsible tags panel by category
                    rx.cond(
                        PortfolioState.show_filters,
                        rx.vstack(
                            rx.foreach(
                                PortfolioState.categorized_tags,
                                category_tag_row,
                            ),
                            width="100%",
                            padding="1.2em",
                            background=f"{BG_CARD}66",
                            border=f"1px solid {BORDER}",
                            border_radius="8px",
                            margin_top="0.5em",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    margin_bottom="2.5em",
                ),
                rx.vstack(
                    rx.foreach(PortfolioState.filtered_projects, project_card),
                    # Project detail modal
                    rx.cond(
                        PortfolioState.is_modal_open,
                        rx.box(
                            position="fixed",
                            top="0",
                            left="0",
                            width="100vw",
                            height="100vh",
                            background="rgba(3, 10, 12, 0.58)",
                            backdrop_filter="blur(12px)",
                            z_index="1100",
                            on_click=PortfolioState.close_modal,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        PortfolioState.is_modal_open,
                        rx.box(
                            rx.box(
                                # ── Modal header ────────────────────────────────────────────
                                rx.hstack(
                                    # Use flat primitive state vars — never .get() on a dict Var
                                    rx.text(PortfolioState.modal_name, font_family=FONT_SANS, font_weight="700", font_size="1.2em", color=TEXT),
                                    rx.button(
                                        "×",
                                        on_click=PortfolioState.close_modal,
                                        margin_left="auto",
                                        background="transparent",
                                        color=TEXT_MUTED,
                                        font_size="1.3em",
                                        padding="0 0.3em",
                                        cursor="pointer",
                                        _hover={"color": PRIMARY},
                                        border="none",
                                    ),
                                    width="100%",
                                    align="center",
                                ),
                                # ── Description ───────────────────────────────────────────
                                rx.text(PortfolioState.modal_desc, font_family=FONT_SANS, color=TEXT_MUTED, margin_top="0.8em", font_size="0.9em", line_height="1.6"),
                                # ── Tags ─────────────────────────────────────────────────
                                rx.hstack(
                                    rx.foreach(
                                        PortfolioState.modal_tags,
                                        lambda tag: rx.text(tag, font_family=FONT_MONO, font_size="0.72em", color=PRIMARY, border=f"1px solid {BORDER}", padding="0.2em 0.6em", border_radius="4px"),
                                    ),
                                    gap="0.4em",
                                    margin_top="0.8em",
                                    wrap="wrap",
                                ),
                                # ── CTA: navigate to case study ────────────────────────
                                rx.cond(
                                    PortfolioState.modal_url != "",
                                    rx.box(
                                        rx.link(
                                            rx.hstack(
                                                rx.text(
                                                    "Case Study'yi Görüntüle",
                                                    font_family=FONT_MONO,
                                                    font_size="0.82em",
                                                    font_weight="600",
                                                    color=BG,
                                                ),
                                                rx.text("→", font_family=FONT_MONO, color=BG, font_size="0.9em"),
                                                gap="0.5em",
                                                align="center",
                                            ),
                                                href=PortfolioState.modal_url,
                                            text_decoration="none",
                                            on_click=PortfolioState.close_modal,
                                        ),
                                        background=PRIMARY,
                                        padding="0.6em 1.2em",
                                        border_radius="8px",
                                        display="inline-block",
                                        margin_top="1.2em",
                                        transition="all 150ms",
                                        _hover={"box_shadow": GLOW_PRIMARY, "opacity": "0.9"},
                                        cursor="pointer",
                                    ),
                                    rx.fragment(),
                                ),
                                padding=rx.breakpoints(initial="1.2em", sm="2em"),
                                background=BG_CARD,
                                border=f"1px solid {BORDER}",
                                border_radius="12px",
                                width="100%",
                                box_shadow="0 24px 80px rgba(0,0,0,0.55)",
                                max_height="85vh",
                                overflow_y="auto",
                            ),
                            position="fixed",
                            top="50%",
                            left="50%",
                            transform="translate(-50%, -50%)",
                            z_index="1201",
                            padding="0",
                            width=rx.breakpoints(initial="92%", sm="90%", md="100%"),
                            max_width="700px",
                            bg="transparent",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                ),
                width="100%",
                align_items="start",
            ),
            max_width="860px",
            margin="0 auto",
            padding=rx.breakpoints(initial="6em 1.2em 3em 1.2em", md="8em 2em 3em 2em"),
            width="100%",
            flex="1",
        ),
        footer(),
        floating_chat(),
        width="100%",
        min_height="100vh",
        bg=BG,
        spacing="0",
    )
