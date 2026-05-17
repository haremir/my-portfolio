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

class ProjectDict(TypedDict):
    name: str
    desc: str
    tags: list[str]

class PortfolioState(rx.State):
    projects: list[ProjectDict] = []
    selected_project: dict = {}
    is_modal_open: bool = False

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_projects
        self.projects = load_projects()

    @rx.event
    def open_project(self, project: ProjectDict):
        self.selected_project = project
        self.is_modal_open = True

    @rx.event
    def close_modal(self):
        self.selected_project = {}
        self.is_modal_open = False

    @rx.var
    def selected_project_tags(self) -> list[str]:
        proj = self.selected_project or {}
        tags = proj.get("tags") if isinstance(proj, dict) else []
        return tags or []


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
                project["name"],
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


@rx.page(route="/portfolio")
def portfolio_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.hstack(
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
                    ),
                    width="100%",
                    justify="between",
                    align="center",
                    margin_bottom="2em",
                ),
                rx.vstack(
                    rx.foreach(PortfolioState.projects, project_card),
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
                                rx.hstack(
                                    rx.text(PortfolioState.selected_project.get("name", ""), font_family=FONT_SANS, font_weight="700", font_size="1.2em", color=TEXT),
                                    rx.button("Kapat", on_click=PortfolioState.close_modal, margin_left="auto"),
                                ),
                                rx.text(PortfolioState.selected_project.get("desc", ""), font_family=FONT_SANS, color=TEXT_MUTED, margin_top="0.8em"),
                                rx.hstack(
                                    rx.foreach(
                                        PortfolioState.selected_project_tags,
                                        lambda tag: rx.text(tag, font_family=FONT_MONO, font_size="0.72em", color=PRIMARY, border=f"1px solid {BORDER}", padding="0.2em 0.6em", border_radius="4px"),
                                    ),
                                    gap="0.4em",
                                    margin_top="0.8em",
                                ),
                                padding="1.2em",
                                background=BG_CARD,
                                border=f"1px solid {BORDER}",
                                border_radius="10px",
                                width="100%",
                                max_width="700px",
                                box_shadow="0 24px 80px rgba(0,0,0,0.45)",
                            ),
                            position="fixed",
                            top="50%",
                            left="50%",
                            transform="translate(-50%, -50%)",
                            z_index="1201",
                            padding="2em",
                            bg="transparent",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                ),
                width="100%",
                align_items="start",
            ),
            style={
                "max_width": "860px",
                "margin": "0 auto",
                "padding": "8em 2em 3em 2em",
            },
            width="100%",
            flex="1",
        ),
        footer(),
        floating_chat(),
        on_mount=PortfolioState.on_load,
        width="100%",
        min_height="100vh",
        bg=BG,
        spacing="0",
    )
