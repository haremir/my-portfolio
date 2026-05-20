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
    name: str
    slug: str
    desc: str
    tags: list[str]

class PortfolioState(rx.State):
    projects: list[ProjectDict] = []
    # ── Flat primitive vars for the detail modal ─────────────────────────────
    # NEVER store the full project dict in state — it carries a nested
    # case_study object that Reflex serialises to the frontend as a JS object
    # and any .get() call on the Var evaluates on the JS side → [object Object].
    # Extract only the four fields the modal actually renders.
    modal_name: str = ""
    modal_desc: str = ""
    modal_tags: list[str] = []
    modal_slug: str = ""
    is_modal_open: bool = False

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_projects
        raw = load_projects()
        # Strip each project to only the four fields ProjectDict declares so
        # the nested case_study dict is never included in the state delta.
        self.projects = [
            {
                "name": p.get("name", ""),
                "slug": p.get("slug", ""),
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
        self.is_modal_open = True

    @rx.event
    def close_modal(self):
        self.modal_name = ""
        self.modal_desc = ""
        self.modal_tags = []
        self.modal_slug = ""
        self.is_modal_open = False


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
            rx.cond(
                project.contains("slug") & (project["slug"] != ""),
                rx.link(
                    "Case Study →",
                    href="/projects/" + project["slug"],
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
                                PortfolioState.modal_slug != "",
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
                                        href="/projects/" + PortfolioState.modal_slug,
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
                            padding="1.5em",
                            background=BG_CARD,
                            border=f"1px solid {BORDER}",
                            border_radius="12px",
                            width="100%",
                            max_width="700px",
                            box_shadow="0 24px 80px rgba(0,0,0,0.55)",
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
        width="100%",
        min_height="100vh",
        bg=BG,
        spacing="0",
    )
