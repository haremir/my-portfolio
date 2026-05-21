import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.theme import (
    BG,
    BG_CARD,
    BORDER,
    PRIMARY,
    TEXT,
    TEXT_MUTED,
    GLOW_PRIMARY,
    FONT_SANS,
    FONT_MONO,
)
from harun_site.state.index_state import IndexState


def section_divider() -> rx.Component:
    return rx.box(
        height="1px",
        background=f"linear-gradient(90deg, transparent, {BORDER}, transparent)",
        width="100%",
        margin="0",
    )


def hero_section() -> rx.Component:
    return rx.vstack(
        rx.image(
            src="/avatar.jpg",
            width="260px",
            height="260px",
            object_fit="cover",
            border_radius="50%",
            border=f"2px solid {PRIMARY}",
            box_shadow=GLOW_PRIMARY,
            margin_bottom="1.2em",
        ),
        rx.text(
            "── AI & BACKEND ENGINEER ──",
            color=PRIMARY,
            font_family=FONT_MONO,
            style={
                "font_size": "0.72em",
                "letter_spacing": "0.2em",
                "opacity": "0.8",
                "margin_bottom": "1.2em",
            },
        ),
        rx.vstack(
            rx.text(
                "HARUN EMİRHAN",
                font_family=FONT_SANS,
                color=TEXT,
                style={
                    "font_size": "2.6em",
                    "font_weight": "700",
                    "line_height": "1.05",
                    "margin_bottom": "0.2em",
                },
            ),
            rx.text(
                "BOSTANCI",
                font_family=FONT_SANS,
                color=TEXT,
                style={
                    "font_size": "2.6em",
                    "font_weight": "700",
                    "line_height": "1.05",
                    "margin_bottom": "0.6em",
                },
            ),
            width="100%",
            max_width="480px",
            align_items="center",
            text_align="center",
        ),
        rx.text(
            "RAG mimarileri, LLM'ler ve üretim odaklı AI sistemleri üzerinde çalışıyorum.",
            color=TEXT_MUTED,
            font_family=FONT_SANS,
            style={"font_size": "0.95em", "margin_bottom": "2em"},
        ),
        rx.hstack(
            rx.link(
                rx.button(
                    "Hakkımda",
                    color=PRIMARY,
                    background="transparent",
                    border=f"1px solid {PRIMARY}",
                    padding="0.65em 1.6em",
                    border_radius="6px",
                    font_family=FONT_MONO,
                    font_size="0.85em",
                    cursor="pointer",
                    _hover={"background": PRIMARY, "color": BG},
                    transition="all 200ms",
                ),
                href="/about",
            ),
            rx.link(
                rx.button(
                    "Chat",
                    background=PRIMARY,
                    color=BG,
                    padding="0.65em 1.6em",
                    border_radius="6px",
                    font_family=FONT_MONO,
                    font_size="0.85em",
                    font_weight="600",
                    cursor="pointer",
                    _hover={"box_shadow": GLOW_PRIMARY},
                    transition="all 200ms",
                ),
                href="/chat",
            ),
            style={"gap": "1em", "margin_bottom": "2em"},
        ),
        rx.box(
            rx.input(
                placeholder="bir şey sor... · dent-bot nedir?",
                width="100%",
                background="#0a1a1d",
                border=f"1px solid {BORDER}",
                color=TEXT,
                color_scheme="teal",
                font_family=FONT_MONO,
                font_size="0.85em",
                padding="0.85em 3em 0.85em 1.2em",
                border_radius="8px",
                height="48px",
                _placeholder={"color": "#7a9ba8"},
                _focus={
                    "border_color": PRIMARY,
                    "box_shadow": f"0 0 0 1px {PRIMARY}40",
                    "outline": "none",
                },
                style={
                    "color": TEXT,
                    "background": BG_CARD,
                    "caretColor": PRIMARY,
                    "::placeholder": {"color": TEXT_MUTED},
                    ":focus": {"borderColor": PRIMARY, "outline": "none"},
                },
                on_change=IndexState.set_query,
                on_key_down=IndexState.handle_keydown,
            ),
            rx.button(
                "→",
                position="absolute",
                right="0.8em",
                top="50%",
                transform="translateY(-50%)",
                background="transparent",
                border="none",
                color=PRIMARY,
                cursor="pointer",
                font_size="1.1em",
                font_family=FONT_MONO,
                padding="0",
                on_click=IndexState.submit_query,
            ),
            width="100%",
            max_width="480px",
            position="relative",
        ),
        rx.text(
            "↑ hakkımda soru sor",
            font_family=FONT_MONO,
            font_size="0.7em",
            color=TEXT_MUTED,
            margin_top="0.5em",
        ),
        align_items="center",
        text_align="center",
        flex="1",
        width="100%",
        padding="8em 2em 4em 2em",
        style={
            "justify_content": "center",
            "background": "radial-gradient(ellipse at 50% 30%, #00f5d412 0%, transparent 60%)",
        },
    )


def about_preview() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    "HAKKIMDA",
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    letter_spacing="0.2em",
                    color=PRIMARY,
                    text_shadow=GLOW_PRIMARY,
                ),
                rx.link(
                    "Devamını gör →",
                    href="/about",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                justify="between",
                align="center",
                margin_bottom="1.5em",
                width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.image(
                        src="/avatar.jpg",
                        width="72px",
                        height="72px",
                        object_fit="cover",
                        border_radius="50%",
                        border=f"2px solid {BORDER}",
                    ),
                    rx.text(
                        "Harun Emirhan Bostancı",
                        font_family=FONT_SANS,
                        font_weight="700",
                        color=TEXT,
                        font_size="1.05em",
                    ),
                    rx.text(
                        "AI & Backend Engineer",
                        font_family=FONT_MONO,
                        color=PRIMARY,
                        font_size="0.78em",
                    ),
                    rx.text(
                        "Python, Yapay Zeka ve backend sistemleri; büyük ölçekli veri ardışık düzenleri ve üretime hazır ML sistemleri geliştiriyorum.",
                        font_family=FONT_SANS,
                        color=TEXT_MUTED,
                        font_size="0.87em",
                        line_height="1.6",
                    ),
                    align_items="start",
                    gap="0.6em",
                    flex="1",
                    min_width="200px",
                ),
                rx.vstack(
                    rx.foreach(
                        IndexState.experience_preview,
                        lambda exp: rx.hstack(
                            rx.box(
                                width="3px",
                                height="100%",
                                min_height="50px",
                                background=PRIMARY,
                                border_radius="2px",
                            ),
                            rx.vstack(
                                rx.text(
                                    exp["company"],
                                    font_family=FONT_SANS,
                                    font_weight="600",
                                    color=TEXT,
                                    font_size="0.95em",
                                ),
                                rx.text(
                                    exp["role"],
                                    font_family=FONT_MONO,
                                    color=PRIMARY,
                                    font_size="0.78em",
                                ),
                                rx.text(
                                    exp["description"][:120] + "...",
                                    font_family=FONT_SANS,
                                    color=TEXT_MUTED,
                                    font_size="0.82em",
                                    line_height="1.5",
                                ),
                                align_items="start",
                                gap="0.2em",
                            ),
                            gap="1em",
                            align="start",
                            padding="0.8em",
                            background=BG,
                            border=f"1px solid {BORDER}",
                            border_radius="8px",
                            width="100%",
                        )
                    ),
                    align_items="start",
                    gap="0.5em",
                    flex="1",
                    min_width="200px",
                ),
                gap="3em",
                align="start",
                flex_wrap="wrap",
                width="100%",
            ),
            max_width="860px",
            margin="0 auto",
            padding="0 2em",
            width="100%",
        ),
        background=BG_CARD,
        width="100%",
        padding="3em 0",
    )


def project_preview_card(project: dict) -> rx.Component:
    # Link directly to the case study when a slug is available.
    # Falls back to the portfolio list for projects without a slug.
    return rx.link(
        rx.hstack(
            rx.text(
                "→",
                font_family=FONT_MONO,
                color=PRIMARY,
                opacity="0.5",
                font_size="1em",
                min_width="1.5em",
            ),
            rx.vstack(
                rx.text(
                    project["name"],
                    font_family=FONT_SANS,
                    font_weight="600",
                    color=TEXT,
                    font_size="0.95em",
                ),
                rx.text(
                    project["desc"],
                    font_family=FONT_SANS,
                    color=TEXT_MUTED,
                    font_size="0.82em",
                ),
                rx.hstack(
                    rx.foreach(
                        project["tags"][:2],
                        lambda tag: rx.text(
                            tag,
                            font_family=FONT_MONO,
                            font_size="0.68em",
                            color=PRIMARY,
                            border=f"1px solid {BORDER}",
                            padding="0.1em 0.4em",
                            border_radius="3px",
                        ),
                    ),
                    gap="0.3em",
                    margin_top="0.2em",
                    width="100%",
                ),
                align_items="start",
                gap="0.2em",
                flex="1",
            ),
            gap="1em",
            padding="1em 1.2em",
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="8px",
            margin_bottom="0.6em",
            width="100%",
            align="center",
            _hover={"border_color": PRIMARY, "box_shadow": GLOW_PRIMARY},
            transition="all 200ms",
            cursor="pointer",
        ),
        href=rx.cond(
            project["slug"] != "",
            "/projects/" + project["slug"],
            "/portfolio",
        ),
        text_decoration="none",
    )


def skills_preview() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    "BECERİLER",
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    letter_spacing="0.2em",
                    color=PRIMARY,
                    text_shadow=GLOW_PRIMARY,
                ),
                justify="between",
                align="center",
                margin_bottom="1.5em",
                width="100%",
            ),
            rx.flex(
                rx.foreach(
                    IndexState.skills_list,
                    lambda cat: rx.vstack(
                        rx.text(
                            cat["category"],
                            font_family=FONT_MONO,
                            color=PRIMARY,
                            font_size="0.85em",
                            margin_bottom="0.5em",
                        ),
                        rx.flex(
                            rx.foreach(
                                cat["skills"],
                                lambda skill: rx.text(
                                    skill,
                                    font_family=FONT_SANS,
                                    font_size="0.85em",
                                    color=TEXT,
                                    background=BG_CARD,
                                    border=f"1px solid {BORDER}",
                                    padding="0.3em 0.8em",
                                    border_radius="15px",
                                )
                            ),
                            wrap="wrap",
                            gap="0.5em",
                        ),
                        align_items="start",
                        width="100%",
                        margin_bottom="1em"
                    )
                ),
                direction="column",
                gap="1.5em",
                width="100%",
            ),
            max_width="860px",
            margin="0 auto",
            padding="0 2em",
            width="100%",
        ),
        background=BG,
        width="100%",
        padding="3em 0",
    )


def portfolio_preview() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    "PORTFOLYO",
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    letter_spacing="0.2em",
                    color=PRIMARY,
                    text_shadow=GLOW_PRIMARY,
                ),
                rx.link(
                    "Tümünü gör →",
                    href="/portfolio",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                justify="between",
                align="center",
                margin_bottom="1.5em",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(IndexState.featured_projects, project_preview_card),
                width="100%",
            ),
            max_width="860px",
            margin="0 auto",
            padding="0 2em",
            width="100%",
        ),
        background=BG,
        width="100%",
        padding="3em 0",
    )


def blog_preview_card(post: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.text(
                post["date"],
                font_family=FONT_MONO,
                font_size="0.72em",
                color=TEXT_MUTED,
                min_width="80px",
            ),
            rx.box(width="1px", height="30px", background=BORDER),
            rx.vstack(
                rx.text(
                    post["title"],
                    font_family=FONT_SANS,
                    font_weight="600",
                    color=TEXT,
                    font_size="0.95em",
                ),
                rx.text(
                    post["description"],
                    font_family=FONT_SANS,
                    color=TEXT_MUTED,
                    font_size="0.82em",
                ),
                align_items="start",
                gap="0.15em",
                flex="1",
            ),
            rx.text("→", color=TEXT_MUTED, font_family=FONT_MONO),
            gap="1.5em",
            padding="1em 1.2em",
            background=BG,
            border=f"1px solid {BORDER}",
            border_radius="8px",
            margin_bottom="0.6em",
            width="100%",
            align="center",
            _hover={"border_color": PRIMARY},
            transition="all 200ms",
            cursor="pointer",
        ),
        href="/blog/" + post["slug"],
        text_decoration="none",
        width="100%",
    )


def blog_preview() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    "SON YAZILAR",
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    letter_spacing="0.2em",
                    color=PRIMARY,
                    text_shadow=GLOW_PRIMARY,
                ),
                rx.link(
                    "Tüm yazılar →",
                    href="/blog",
                    font_family=FONT_MONO,
                    font_size="0.78em",
                    color=TEXT_MUTED,
                    _hover={"color": PRIMARY},
                    text_decoration="none",
                ),
                justify="between",
                align="center",
                margin_bottom="1.5em",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(IndexState.recent_posts, blog_preview_card),
                width="100%",
            ),
            max_width="860px",
            margin="0 auto",
            padding="0 2em",
            width="100%",
        ),
        background=BG_CARD,
        width="100%",
        padding="3em 0",
    )


def index() -> rx.Component:
    return rx.vstack(
        navbar(),
        hero_section(),
        section_divider(),
        about_preview(),
        section_divider(),
        skills_preview(),
        section_divider(),
        portfolio_preview(),
        section_divider(),
        blog_preview(),
        footer(),
        floating_chat(),
        width="100%",
        min_height="100vh",
        background=BG,
        spacing="0",
    )
