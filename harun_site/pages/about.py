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
from harun_site.state.about_state import AboutState
from harun_site.state.language_state import LanguageState
from harun_site.utils.i18n import TXT


def skill_tag(name: str) -> rx.Component:
    return rx.box(
        name,
        font_family=FONT_MONO,
        font_size="0.8em",
        padding="0.3em 0.8em",
        border_radius="4px",
        background=BG_CARD,
        color=PRIMARY,
        border=f"1px solid {BORDER}",
        text_shadow="none",
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


def experience_card(exp: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        exp["company"],
                        font_family=FONT_SANS,
                        font_weight="700",
                        color=TEXT,
                        font_size="1.05em",
                    ),
                    rx.text(
                        rx.cond(
                            LanguageState.language == "en",
                            exp["role_en"],
                            exp["role"],
                        ),
                        font_family=FONT_MONO,
                        color=PRIMARY,
                        font_size="0.82em",
                    ),
                    align_items="start",
                    gap="0.1em",
                ),
                rx.text(
                    rx.cond(
                        LanguageState.language == "en",
                        exp["start_date_en"] + " – " + exp["end_date_en"],
                        exp["start_date"] + " – " + exp["end_date"],
                    ),
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    color=TEXT_MUTED,
                    white_space="nowrap",
                ),
                justify="between",
                align="start",
                width="100%",
            ),
            rx.text(
                rx.cond(
                    LanguageState.language == "en",
                    exp["description_en"],
                    exp["description"],
                ),
                font_family=FONT_SANS,
                color=TEXT_MUTED,
                font_size="0.87em",
                line_height="1.7",
                margin_top="0.8em",
            ),
            rx.hstack(
                rx.foreach(
                    exp["tags"],
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
                gap="0.4em",
                flex_wrap="wrap",
                margin_top="0.8em",
                width="100%",
            ),
            align_items="start",
            width="100%",
        ),
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        padding="1.5em",
        width="100%",
        margin_bottom="1em",
        _hover={"border_color": PRIMARY},
        transition="all 200ms",
    )


def education_card(edu: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        edu["school"],
                        font_family=FONT_SANS,
                        font_weight="700",
                        color=TEXT,
                        font_size="1.05em",
                    ),
                    rx.text(
                        rx.cond(
                            LanguageState.language == "en",
                            edu["department_en"],
                            edu["department"],
                        ),
                        font_family=FONT_MONO,
                        color=PRIMARY,
                        font_size="0.82em",
                    ),
                    align_items="start",
                    gap="0.1em",
                ),
                rx.text(
                    edu["start_year"] + " – " + edu["end_year"],
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    color=TEXT_MUTED,
                    white_space="nowrap",
                ),
                justify="between",
                align="start",
                width="100%",
            ),
            rx.badge(
                rx.cond(
                    LanguageState.language == "en",
                    edu["degree_en"],
                    edu["degree"],
                ),
                font_family=FONT_MONO,
                font_size="0.72em",
                background=f"{PRIMARY}15",
                color=PRIMARY,
                border=f"1px solid {PRIMARY}44",
                padding="0.2em 0.6em",
                border_radius="4px",
                margin_top="0.8em",
            ),
            rx.text(
                rx.cond(
                    LanguageState.language == "en",
                    edu["description_en"],
                    edu["description"],
                ),
                font_family=FONT_SANS,
                color=TEXT_MUTED,
                font_size="0.87em",
                line_height="1.7",
                margin_top="0.8em",
            ),
            align_items="start",
            width="100%",
        ),
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        padding="1.5em",
        width="100%",
        margin_bottom="1em",
        _hover={"border_color": PRIMARY},
        transition="all 200ms",
    )
def skill_category_view(cat: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.text(
            rx.cond(LanguageState.language == "en", cat["category_en"], cat["category"]),
            font_family=FONT_MONO,
            font_size="0.8em",
            font_weight="bold",
            color=PRIMARY,
            text_transform="uppercase",
            margin_bottom="0.5em",
        ),
        rx.hstack(
            rx.foreach(
                cat["skills"],
                skill_tag,
            ),
            spacing="2",
            wrap="wrap",
            width="100%",
        ),
        align_items="start",
        width="100%",
        margin_bottom="1.5em",
    )


def about_page() -> rx.Component:
    return rx.vstack(
        navbar(),
        rx.box(
            rx.vstack(
                rx.flex(
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
                            "HARUN EMİRHAN BOSTANCI",
                            color=TEXT,
                            font_family=FONT_SANS,
                            font_size=rx.breakpoints(initial="1.6em", md="2em"),
                            font_weight="700",
                        ),
                        rx.text(
                            "── DATA SCIENCE & AI ENGINEER | LLM ORCHESTRATOR ──",
                            color=PRIMARY,
                            font_family=FONT_MONO,
                            font_size="0.85em",
                        ),
                        rx.text(
                            rx.cond(
                                LanguageState.language == "en",
                                "As a computer engineering graduate from Erzurum Technical University, I focus on artificial intelligence, machine learning, and data engineering. I specialize in large language models (LLMs), data processing systems, and production-oriented AI applications, building scalable Python-based AI solutions, data pipelines, and end-to-end systems.",
                                "Erzurum Teknik Üniversitesi mezunu bir bilgisayar mühendisi olarak yapay zeka, makine öğrenmesi ve veri mühendisliği alanlarında çalışıyorum. Büyük dil modelleri (LLM), veri işleme sistemleri ve üretim odaklı AI uygulamaları üzerine yoğunlaşıyorum. Python tabanlı ölçeklenebilir yapay zeka çözümleri, veri pipeline’ları ve uçtan uca AI sistemleri geliştiriyorum.",
                            ),
                            color=TEXT_MUTED,
                            font_family=FONT_SANS,
                            style={"font_size": "0.9em", "line_height": "1.6", "margin_top": "0.5em"},
                        ),
                        align="start",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    align="center",
                    gap="2em",
                    margin_bottom="3em",
                    width="100%",
                ),

                section_title(rx.cond(LanguageState.language == "en", "Skills", "Beceriler")),
                rx.vstack(
                    rx.foreach(AboutState.skills, skill_category_view),
                    width="100%",
                    spacing="3",
                                        align_items="start",
                ),
                section_title(rx.cond(LanguageState.language == "en", "EXPERIENCE", "DENEYİM")),
                rx.vstack(
                    rx.foreach(AboutState.experience, experience_card),
                    width="100%",
                ),
                section_title(rx.cond(LanguageState.language == "en", "EDUCATION", "EĞİTİM")),
                rx.vstack(
                    rx.foreach(AboutState.education, education_card),
                    width="100%",
                ),
                section_title(rx.cond(LanguageState.language == "en", "Projects", "Projeler")),
                rx.vstack(
                    rx.text("PORTFOLYO", font_family=FONT_MONO, font_size="0.75em",
                            letter_spacing="0.2em", color=PRIMARY, text_shadow=GLOW_PRIMARY),
                    rx.text(rx.cond(LanguageState.language == "en", "Check out the portfolio for projects, competitions, and achievements.", "Projeler, yarışmalar ve başarılar için portfolyo sayfasına göz at."),
                            font_family=FONT_SANS, color=TEXT_MUTED, font_size="0.87em"),
                    rx.link(rx.cond(LanguageState.language == "en", "Go to Portfolio →", "Portfolyo'ya git →"), href="/portfolio",
                            font_family=FONT_MONO, font_size="0.85em", color=PRIMARY,
                            _hover={"text_shadow": GLOW_PRIMARY}, text_decoration="none"),
                    align_items="start", gap="0.5em",
                    padding="1.2em 1.5em",
                    background=BG_CARD,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    width="100%",
                    margin_top="1em",
                ),
                section_title(rx.cond(LanguageState.language == "en", "Contact", "İletişim")),
                rx.hstack(
                    rx.link(
                        "GitHub",
                        href="https://github.com/haremir",
                        color=PRIMARY,
                        transition="color 200ms ease",
                        _hover={"color": ACCENT},
                    ),
                    rx.link(
                        "LinkedIn",
                        href="https://linkedin.com/in/haremir826",
                        color=PRIMARY,
                        transition="color 200ms ease",
                        _hover={"color": ACCENT},
                    ),
                    rx.link(
                        "Blog",
                        href="/blog",
                        color=PRIMARY,
                        transition="color 200ms ease",
                        _hover={"color": ACCENT},
                    ),
                    rx.cond(
                        AboutState.cv_path != "",
                        rx.button(
                            rx.cond(LanguageState.language == "en", "Download CV ↓", "CV İndir ↓"),
                            on_click=rx.download(AboutState.cv_path),
                            font_family=FONT_MONO,
                            font_size="0.85em",
                            color=BG,
                            background=PRIMARY,
                            padding="0.5em 1.2em",
                            border_radius="6px",
                            font_weight="600",
                            _hover={"box_shadow": GLOW_PRIMARY},
                        ),
                        rx.fragment(),
                    ),
                    spacing="4",
                    align="center",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            max_width="800px",
            margin="0 auto",
            padding=rx.breakpoints(initial="6em 1.2em 3em 1.2em", md="8em 2em 3em 2em"),
            background_color=BG,
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
