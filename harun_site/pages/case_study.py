import reflex as rx
from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.state.case_study_state import CaseStudyState
from harun_site.theme import (
    BG,
    TEXT,
    TEXT_MUTED,
    PRIMARY,
    BORDER,
    FONT_MONO,
    FONT_SANS,
)

def cs_section(title: str, content: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_family=FONT_MONO, font_size="0.72em",
                letter_spacing="0.15em", color=PRIMARY,
                text_transform="uppercase", margin_top="2em"),
        rx.box(height="1px", background=BORDER, width="100%"),
        rx.text(content, font_family=FONT_SANS, color=TEXT_MUTED,
                font_size="0.9em", line_height="1.8", margin_top="0.8em"),
        align_items="flex-start", width="100%", gap="0.3em",
    )

def case_study() -> rx.Component:
    content = rx.vstack(
        rx.link("← Portfolyo", href="/portfolio", font_family=FONT_MONO, font_size="0.8em", color=TEXT_MUTED, _hover={"color": PRIMARY}, text_decoration="none", margin_bottom="2em", display="block"),
        rx.text(CaseStudyState.project_name, font_family=FONT_SANS, font_size="2.2em", font_weight="700", color=TEXT),
        rx.hstack(
            rx.foreach(
                CaseStudyState.project_tags,
                lambda tag: rx.text(tag, font_family=FONT_MONO, font_size="0.7em", color=PRIMARY, border=f"1px solid {BORDER}", padding="0.15em 0.5em", border_radius="3px")
            ),
            wrap="wrap",
            style={"gap": "0.4em", "margin_top": "0.5em"}
        ),
        rx.cond(
            CaseStudyState.project_name != "",
            rx.vstack(
                cs_section("Problem", CaseStudyState.cs_problem),
                cs_section("Mimari", CaseStudyState.cs_architecture),
                cs_section("Neden Bu Stack?", CaseStudyState.cs_stack_reason),
                cs_section("Zorluklar", CaseStudyState.cs_challenges),
                cs_section("Öğrendiklerim", CaseStudyState.cs_learnings),
                width="100%",
                align_items="flex-start",
                gap="1em"
            ),
            rx.fragment()
        ),
        align_items="flex-start",
        width="100%"
    )

    return rx.vstack(
        navbar(),
        rx.box(
            rx.cond(CaseStudyState.not_found, rx.text("Proje bulunamadı.", color=TEXT, font_family=FONT_SANS), content),
            style={
                "max_width": "800px",
                "margin": "0 auto",
                "padding": "3em 2em",
                "padding_top": "8em",
            },
            width="100%",
            flex="1",
        ),
        footer(),
        width="100%",
        min_height="100vh",
        bg=BG,
        spacing="0",
    )
