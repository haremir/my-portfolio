"""
case_study.py
=============
Case-study page and the legacy-route redirect shim.

URL conventions
---------------
Canonical:  /portfolio/[slug]  ← primary route for all new links
Alias:      /projects/[slug]   ← registered separately; on_load fires
                                  CaseStudyState.redirect_legacy_route which
                                  does an instant client-side redirect to
                                  /portfolio/[slug].  No HTML content is shown.

Case study content safety contract
-------------------------------
Every value passed into the case study content renderer in this file must be one of:
  • CaseStudyState.cs_problem
  • CaseStudyState.cs_architecture
  • CaseStudyState.cs_stack_reason
  • CaseStudyState.cs_challenges
  • CaseStudyState.cs_learnings

All five are plain ``str`` state vars (type-annotated and zero-defaulted).
They are populated exclusively by CaseStudyState.load_project(), which
passes every value through _safe_str() before assignment.

The page renders backend-generated HTML strings instead of using
rx.markdown() directly, which avoids React-side children assertions.

NO .get() chains, NO dict fields, NO raw project keys are used anywhere
in this file.

UX states
---------
The page handles four distinct states cleanly:
  1. is_loading   — skeleton shown while load_project runs (immediate yield)
  2. not_found    — 404 card with back button and styled message
  3. loaded + has content — full case-study sections
  4. loaded + no content — "coming soon" placeholder card
"""
import reflex as rx
from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.components.floating_chat import floating_chat
from harun_site.state.case_study_state import CaseStudyState
from harun_site.theme import (
    BG,
    BG_CARD,
    TEXT,
    TEXT_MUTED,
    PRIMARY,
    BORDER,
    ACCENT,
    GLOW_PRIMARY,
    FONT_MONO,
    FONT_SANS,
)


# ---------------------------------------------------------------------------
# Back-link — shared across all states so navigation is always available
# ---------------------------------------------------------------------------

def _back_link() -> rx.Component:
    return rx.link(
        "← Portfolyo",
        href="/portfolio",
        font_family=FONT_MONO,
        font_size="0.8em",
        color=TEXT_MUTED,
        _hover={"color": PRIMARY},
        text_decoration="none",
        display="block",
    )


# ---------------------------------------------------------------------------
# State 1 – Loading skeleton
# ---------------------------------------------------------------------------

def _cs_skeleton_bar(width: str, height: str = "0.9em") -> rx.Component:
    """Single skeleton shimmer bar."""
    return rx.box(
        height=height,
        width=width,
        background=BORDER,
        border_radius="4px",
        opacity="0.55",
    )


def cs_loading_state() -> rx.Component:
    """
    Shown immediately while load_project is running.

    load_project() sets is_loading=True and yields before doing any I/O,
    so this skeleton appears within one round-trip of the navigation event.
    """
    return rx.vstack(
        _back_link(),
        # ── Title skeleton ─────────────────────────────────────────────
        _cs_skeleton_bar("min(16em, 60%)", "2.2em"),
        # ── Tags skeleton ──────────────────────────────────────────────
        rx.hstack(
            _cs_skeleton_bar("5em", "1.5em"),
            _cs_skeleton_bar("7em", "1.5em"),
            _cs_skeleton_bar("4em", "1.5em"),
            gap="0.5em",
            wrap="wrap",
            style={"margin_top": "0.5em"},
        ),
        # ── Section skeletons ──────────────────────────────────────────
        rx.vstack(
            _cs_skeleton_bar("8em", "0.7em"),
            rx.box(height="1px", background=BORDER, width="100%", opacity="0.4"),
            _cs_skeleton_bar("100%"),
            _cs_skeleton_bar("90%"),
            _cs_skeleton_bar("75%"),
            gap="0.6em",
            width="100%",
            style={"margin_top": "2.5em"},
        ),
        rx.vstack(
            _cs_skeleton_bar("6em", "0.7em"),
            rx.box(height="1px", background=BORDER, width="100%", opacity="0.4"),
            _cs_skeleton_bar("100%"),
            _cs_skeleton_bar("85%"),
            gap="0.6em",
            width="100%",
            style={"margin_top": "2em"},
        ),
        align_items="flex-start",
        width="100%",
        gap="1em",
    )


# ---------------------------------------------------------------------------
# State 2 – Project not found (404)
# ---------------------------------------------------------------------------

def cs_not_found() -> rx.Component:
    """
    Shown when CaseStudyState.not_found is True.

    Provides clear messaging and a prominent back-navigation path so
    the user never reaches a dead end.
    """
    return rx.vstack(
        _back_link(),
        rx.box(
            rx.vstack(
                # ── Visual signal ──────────────────────────────────────
                rx.text(
                    "404",
                    font_family=FONT_MONO,
                    font_size="3.5em",
                    font_weight="700",
                    color=PRIMARY,
                    opacity="0.25",
                    line_height="1",
                    style={"letter_spacing": "-2px"},
                ),
                rx.text(
                    "Proje bulunamadı",
                    font_family=FONT_SANS,
                    font_size="1.3em",
                    font_weight="700",
                    color=TEXT,
                    style={"margin_top": "-0.3em"},
                ),
                rx.text(
                    "Bu adrese karşılık gelen bir proje yok. "
                    "Slug yanlış yazılmış olabilir ya da proje kaldırılmış olabilir.",
                    font_family=FONT_SANS,
                    color=TEXT_MUTED,
                    font_size="0.9em",
                    line_height="1.7",
                ),
                # ── CTA ────────────────────────────────────────────────
                rx.link(
                    rx.hstack(
                        rx.text("←", font_family=FONT_MONO, color=PRIMARY),
                        rx.text(
                            "Tüm projeleri gör",
                            font_family=FONT_MONO,
                            font_size="0.85em",
                            color=PRIMARY,
                        ),
                        gap="0.5em",
                        align="center",
                    ),
                    href="/portfolio",
                    text_decoration="none",
                    _hover={"opacity": "0.8"},
                ),
                align_items="flex-start",
                gap="1em",
            ),
            padding="2em 2.5em",
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            width="100%",
            style={"margin_top": "3em"},
        ),
        align_items="flex-start",
        width="100%",
        gap="2em",
    )


# ---------------------------------------------------------------------------
# State 4 – Project exists but case_study block is empty
# ---------------------------------------------------------------------------

def cs_empty_content() -> rx.Component:
    """
    Shown when the project loaded successfully but has no case_study sections.

    Replaces the silent blank space that would otherwise appear below the
    project title and tags when all cs_* fields are empty strings.
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("📋", font_size="1.4em"),
                rx.text(
                    "Case Study Hazırlanıyor",
                    font_family=FONT_SANS,
                    font_weight="700",
                    color=TEXT,
                    font_size="1em",
                ),
                align="center",
                gap="0.7em",
            ),
            rx.text(
                "Bu projenin detaylı case study içeriği yakında eklenecek. "
                "Proje hakkında soru sormak için sohbet asistanını kullanabilirsin.",
                font_family=FONT_SANS,
                color=TEXT_MUTED,
                font_size="0.88em",
                line_height="1.7",
            ),
            rx.link(
                "Projeyi AI ile tartış →",
                href="/chat",
                font_family=FONT_MONO,
                font_size="0.8em",
                color=PRIMARY,
                text_decoration="none",
                _hover={"text_shadow": GLOW_PRIMARY},
            ),
            align_items="flex-start",
            gap="0.8em",
        ),
        padding="1.8em 2em",
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_left=f"3px solid {PRIMARY}",
        border_radius="10px",
        margin_top="2em",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Shared section renderer
# ---------------------------------------------------------------------------

def cs_section(title: str, content_html: rx.Var) -> rx.Component:
    """
    Render a titled markdown section.

    Parameters
    ----------
    title:   plain Python str — section heading (e.g. "Problem")
    content_html: a CaseStudyState.cs_*_html Var[str] — already safe HTML.
    """
    return rx.vstack(
        rx.text(
            title,
            font_family=FONT_MONO,
            font_size="0.72em",
            letter_spacing="0.15em",
            color=PRIMARY,
            text_transform="uppercase",
            margin_top="2em",
        ),
        rx.box(height="1px", background=BORDER, width="100%"),
        rx.cond(
            content_html != "",
            rx.box(
                rx.html(content_html),
                color=TEXT_MUTED,
                font_family=FONT_SANS,
                font_size="0.9em",
                line_height="1.8",
                margin_top="0.8em",
            ),
            rx.fragment(),
        ),
        align_items="flex-start",
        width="100%",
        gap="0.3em",
    )


# ---------------------------------------------------------------------------
# State 3 – Loaded project with case study content
# ---------------------------------------------------------------------------

def cs_content() -> rx.Component:
    """
    Full case-study view rendered when a project is successfully loaded
    and has at least one non-empty content section.
    """
    return rx.vstack(
        _back_link(),

        # ── Project header ─────────────────────────────────────────────
        rx.text(
            CaseStudyState.project_name,
            font_family=FONT_SANS,
            font_size="2.2em",
            font_weight="700",
            color=TEXT,
            style={"margin_top": "0.5em"},
        ),
        rx.hstack(
            rx.foreach(
                CaseStudyState.project_tags,
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
            style={"gap": "0.4em", "margin_top": "0.3em"},
        ),

        # ── Case study sections OR empty-content placeholder ───────────
        rx.cond(
            CaseStudyState.has_case_study_content,
            rx.vstack(
                rx.cond(
                    CaseStudyState.cs_problem_html != "",
                    cs_section("Problem", CaseStudyState.cs_problem_html),
                    rx.fragment(),
                ),
                rx.cond(
                    CaseStudyState.cs_architecture_html != "",
                    cs_section("Mimari", CaseStudyState.cs_architecture_html),
                    rx.fragment(),
                ),
                rx.cond(
                    CaseStudyState.cs_arch_image != "",
                    rx.box(
                        rx.image(
                            src=CaseStudyState.cs_arch_image,
                            width="100%",
                            border=f"1px solid {BORDER}",
                            border_radius="8px",
                            margin_top="1em",
                        )
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    CaseStudyState.cs_stack_reason_html != "",
                    cs_section("Neden Bu Stack?", CaseStudyState.cs_stack_reason_html),
                    rx.fragment(),
                ),
                rx.cond(
                    CaseStudyState.cs_challenges_html != "",
                    cs_section("Zorluklar", CaseStudyState.cs_challenges_html),
                    rx.fragment(),
                ),
                rx.cond(
                    CaseStudyState.cs_learnings_html != "",
                    cs_section("Öğrendiklerim", CaseStudyState.cs_learnings_html),
                    rx.fragment(),
                ),
                width="100%",
                align_items="flex-start",
                gap="0.5em",
            ),
            cs_empty_content(),
        ),

        # ── Bottom CTA — back to all projects ──────────────────────────
        rx.box(
            rx.link(
                "← Tüm projelere dön",
                href="/portfolio",
                font_family=FONT_MONO,
                font_size="0.8em",
                color=TEXT_MUTED,
                _hover={"color": PRIMARY},
                text_decoration="none",
            ),
            style={"margin_top": "4em", "padding_top": "2em",
                   "border_top": f"1px solid {BORDER}"},
            width="100%",
        ),

        align_items="flex-start",
        width="100%",
        gap="0.3em",
    )


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

def case_study() -> rx.Component:
    """
    /portfolio/[slug]  — canonical case-study page.

    Renders one of four mutually-exclusive states based on CaseStudyState:
      1. is_loading=True          → cs_loading_state() skeleton
      2. not_found=True           → cs_not_found() 404 card
      3. has_case_study_content   → cs_content() full sections
      4. loaded but no content    → cs_content() with cs_empty_content() inside
    """
    return rx.vstack(
        navbar(),
        rx.box(
            rx.cond(
                CaseStudyState.is_loading,
                cs_loading_state(),
                rx.cond(
                    CaseStudyState.not_found,
                    cs_not_found(),
                    cs_content(),
                ),
            ),
            style={
                "max_width": "800px",
                "margin": "0 auto",
                "padding": "3em 2em 6em 2em",
                "padding_top": "8em",
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


# ---------------------------------------------------------------------------
# Legacy-route redirect shim
# ---------------------------------------------------------------------------

def portfolio_slug_redirect() -> rx.Component:
    """
    Minimal page rendered for /projects/[slug].

    The real work is done by CaseStudyState.redirect_legacy_route which is
    fired as on_load and immediately calls rx.redirect("/portfolio/[slug]").
    This component is shown for the brief instant before the redirect fires;
    it intentionally has no navbar/footer to avoid a flash of unstyled content.
    """
    return rx.box(
        rx.text(
            "Yönlendiriliyor...",
            color=TEXT_MUTED,
            font_family=FONT_MONO,
            font_size="0.85em",
            letter_spacing="0.1em",
        ),
        display="flex",
        align_items="center",
        justify_content="center",
        height="100vh",
        background=BG,
    )
