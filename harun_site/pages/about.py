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
    FONT_MONO,
    FONT_SANS,
)


class AboutState(rx.State):
    selected_skills: list[str] = []
    projects: list[dict] = []
    
    def on_load(self):
        from harun_site.utils import data_manager
        self.projects = data_manager.load_projects()

    def toggle_skill(self, skill: str):
        if skill in self.selected_skills:
            self.selected_skills = [s for s in self.selected_skills if s != skill]
        else:
            self.selected_skills = self.selected_skills + [skill]

    def clear_skills(self):
        self.selected_skills = []

    @rx.var
    def selected_skills_str(self) -> str:
        return ",".join(self.selected_skills)

    @rx.var
    def has_filter(self) -> bool:
        return len(self.selected_skills) > 0


    @rx.var
    def filtered_projects(self) -> list[dict]:
        res = []
        for i, project in enumerate(self.projects):
            # Check filter
            if self.has_filter:
                match = any(skill in project.get("tags", []) for skill in self.selected_skills)
                if not match:
                    continue
            
            # Add index
            p = dict(project)
            p["display_index"] = f"0{len(res) + 1}"
            res.append(p)
        return res

class ProjectModalState(rx.State):
    is_open: bool = False
    selected_name: str = ""
    selected_desc: str = ""
    selected_tags: list[str] = []

    def open_modal(self, project: dict):
        self.selected_name = project.get("name", "")
        self.selected_desc = project.get("desc", "")
        self.selected_tags = project.get("tags", [])
        self.is_open = True

    def close_modal(self):
        self.is_open = False


def skill_tag(name: str) -> rx.Component:
    return rx.button(
        name,
        on_click=AboutState.toggle_skill(name),
        font_family=FONT_MONO,
        font_size="0.8em",
        padding="0.3em 0.8em",
        border_radius="4px",
        cursor="pointer",
        transition="all 150ms",
        background=rx.cond(
            AboutState.selected_skills_str.contains(name),
            "#00f5d415",
            BG_CARD,
        ),
        color=rx.cond(
            AboutState.selected_skills_str.contains(name),
            PRIMARY,
            TEXT_MUTED,
        ),
        border=rx.cond(
            AboutState.selected_skills_str.contains(name),
            f"1px solid {PRIMARY}",
            f"1px solid {BORDER}",
        ),
        text_shadow=rx.cond(
            AboutState.selected_skills_str.contains(name),
            GLOW_PRIMARY,
            "none",
        ),
    )


def project_card(project: dict) -> rx.Component:
    return rx.hstack(
        rx.text(
            project["display_index"],
            font_family=FONT_MONO,
            color=PRIMARY,
            style={
                "font_size": "1.5em",
                "font_weight": "600",
                "opacity": "0.4",
                "min_width": "2em",
            },
        ),
        rx.vstack(
            rx.text(
                project["name"],
                font_family=FONT_SANS,
                color=TEXT,
                style={"font_size": "1.05em", "font_weight": "600"},
            ),
            rx.text(
                project["desc"],
                font_family=FONT_SANS,
                color=TEXT_MUTED,
                style={"font_size": "0.85em", "line_height": "1.5"},
            ),
            rx.hstack(
                *[
                    rx.text(
                        tag,
                        font_family=FONT_MONO,
                        color=PRIMARY,
                        style={
                            "font_size": "0.7em",
                            "border": f"1px solid {BORDER}",
                            "padding": "0.15em 0.5em",
                            "border_radius": "3px",
                        },
                    )
                    for tag in project["tags"]
                ],
                wrap="wrap",
                style={"gap": "0.5em"},
            ),
            align="start",
            style={"gap": "0.3em"},
        ),
        align="start",
        style={"gap": "1.5em", "cursor": "pointer"},
        width="100%",
        background_color=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        padding="1.5em",
        margin_bottom="1em",
        _hover={"border_color": PRIMARY, "box_shadow": GLOW_PRIMARY},
        transition="all 200ms",
        on_click=lambda: ProjectModalState.open_modal(project),
    )


def _skill_matches(tags: list[str]) -> rx.Var:
    condition = AboutState.has_filter == False
    for tag in tags:
        condition = condition | AboutState.selected_skills_str.contains(tag)
    return condition


def project_modal() -> rx.Component:
    modal_content = rx.box(
        rx.hstack(
            rx.text(
                ProjectModalState.selected_name,
                color=PRIMARY,
                font_family=FONT_SANS,
                font_size="1.3em",
                font_weight="700",
            ),
            rx.button(
                "×",
                on_click=ProjectModalState.close_modal,
                background_color="transparent",
                color=TEXT_MUTED,
                padding="0",
                height="24px",
                width="24px",
                _hover={"color": TEXT},
                style={"cursor": "pointer"},
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.text(
            ProjectModalState.selected_desc,
            color=TEXT,
            font_family=FONT_SANS,
            style={"line_height": "1.7", "margin_top": "1em"},
        ),
        rx.hstack(
            rx.foreach(
                ProjectModalState.selected_tags,
                lambda tag: rx.text(
                    tag,
                    font_family=FONT_MONO,
                    color=PRIMARY,
                    style={
                        "font_size": "0.7em",
                        "border": f"1px solid {BORDER}",
                        "padding": "0.15em 0.5em",
                        "border_radius": "3px",
                    },
                ),
            ),
            wrap="wrap",
            style={"gap": "0.5em", "margin_top": "1em"},
        ),
        rx.text(
            "× dışarı tıkla kapatır",
            color=TEXT_MUTED,
            font_size="0.72em",
            font_family=FONT_MONO,
            margin_top="1.5em",
        ),
        background=BG_CARD,
        border=f"1px solid {PRIMARY}",
        box_shadow=GLOW_PRIMARY,
        border_radius="12px",
        padding="2em",
        max_width="480px",
        width="90%",
        on_click=rx.stop_propagation,
    )

    return rx.cond(
        ProjectModalState.is_open,
        rx.box(
            modal_content,
            position="fixed",
            top="0",
            left="0",
            width="100vw",
            height="100vh",
            background="#000000aa",
            z_index="300",
            display="flex",
            align_items="center",
            justify_content="center",
            on_click=ProjectModalState.close_modal,
        ),
        rx.fragment(),
    )


def section_title(title: str) -> rx.Component:
    return rx.heading(
        title,
        size="4",
        color=PRIMARY,
        style={
            "border-bottom": f"1px solid {BORDER}",
            "padding-bottom": "0.5em",
            "font_family": FONT_MONO,
            "font_size": "0.75em",
            "letter_spacing": "0.2em",
            "text_transform": "uppercase",
            "text_shadow": GLOW_PRIMARY,
            "margin_bottom": "1em",
            "margin_top": "3em",
        },
        text_align="left",
    )


def about_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.image(
                        src="/avatar.jpg",
                        width="120px",
                        height="120px",
                        object_fit="cover",
                        border_radius="50%",
                        border=f"2px solid {BORDER}",
                    ),
                    rx.vstack(
                        rx.text(
                            "Harun Dülger",
                            color=TEXT,
                            font_family=FONT_SANS,
                            style={"font_size": "2em", "font_weight": "700"},
                        ),
                        rx.text(
                            "AI & Backend Engineer · Computer Engineering Graduate",
                            color=PRIMARY,
                            font_family=FONT_MONO,
                            style={"font_size": "0.85em"},
                        ),
                        rx.text(
                            "Yoğun makine öğrenmesi ve backend geliştirme deneyimi. "
                            "Bilgisayar Mühendisliği mezunu. ProudSec'te AI intern olarak çalışıyor. "
                            "Kendi yazılımımızı geliştirmeyi ve yeni teknolojiler keşfetmeyi seviyorum.",
                            color=TEXT_MUTED,
                            font_family=FONT_SANS,
                            style={"font_size": "0.9em", "line_height": "1.6", "margin_top": "0.5em"},
                        ),
                        align="start",
                    ),
                    align="center",
                    style={"gap": "3em", "margin_bottom": "3em"},
                ),
                section_title("Beceriler"),
                rx.hstack(
                    *[
                        skill_tag(skill)
                        for skill in [
                            "Python",
                            "Reflex",
                            "FastAPI",
                            "LangChain",
                            "RAG",
                            "PostgreSQL",
                            "Docker",
                            "Git",
                            "Groq",
                            "YOLOv8",
                            "Whisper",
                            "CLIP",
                        ]
                    ],
                    rx.cond(
                        AboutState.has_filter,
                        rx.button(
                            "✕ temizle",
                            on_click=AboutState.clear_skills,
                            font_family=FONT_MONO,
                            font_size="0.8em",
                            padding="0.3em 0.8em",
                            border_radius="4px",
                            background="transparent",
                            color=ACCENT,
                            border=f"1px solid {ACCENT}66",
                            cursor="pointer",
                            transition="all 150ms",
                            _hover={"border_color": ACCENT, "color": ACCENT},
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    wrap="wrap",
                ),
                section_title("Projeler"),
                rx.vstack(
                    rx.foreach(
                        AboutState.filtered_projects,
                        lambda project: project_card(project)
                    ),
                    spacing="1",
                ),
                section_title("İletişim"),
                rx.hstack(
                    rx.link(
                        "GitHub",
                        href="https://github.com",
                        color=PRIMARY,
                        transition="color 200ms ease",
                        _hover={"color": ACCENT},
                    ),
                    rx.link(
                        "LinkedIn",
                        href="https://linkedin.com",
                        color=PRIMARY,
                        transition="color 200ms ease",
                        _hover={"color": ACCENT},
                    ),
                    spacing="4",
                    align="center",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            style={
                "max_width": "800px",
                "margin": "0 auto",
                "padding": "8em 2em 3em 2em",
                "background_color": BG,
            },
            width="100%",
        ),
        footer(),
        project_modal(),
        floating_chat(),
        width="100%",
        min_height="100vh",
        bg=BG,
    )