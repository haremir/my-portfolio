"""
case_study_state.py
===================
State for the /portfolio/[slug] page.

Design rules (hard constraints)
--------------------------------
1.  NO @rx.var computed vars that touch self.project.
    In Reflex 0.9.x the var-expression compiler evaluates chained .get()
    calls on a generic `dict` state var on the *frontend*, not Python.
    The JS result of an unresolved dict access is the raw object, which
    becomes `[object Object]` when fed into a render tree → crash.

2.  NO `project: dict` state var.
    Every state var is serialised to the frontend on every state delta.
    A nested dict sitting in the state tree can confuse Reflex's
    React-side reconciliation even when it is not referenced by any
    component.  Keep state vars to primitives only.

3.  ALL fields are normalised to `str` / `list[str]` by _safe_str()
    *before* being stored.  The frontend never sees anything but a plain
    string.

Routing
-------
Canonical URL:  /portfolio/[slug]  ← primary, used in all links
Legacy alias:   /projects/[slug]   ← redirect → /portfolio/[slug]
"""
from __future__ import annotations

import json
import markdown as md
import sys

import reflex as rx


# ---------------------------------------------------------------------------
# _safe_str  —  the only place that touches raw JSON values
# ---------------------------------------------------------------------------

def _safe_str(value: object, field_name: str = "unknown") -> str:
    """
    Convert *any* value to a plain Python ``str`` that is safe to pass to
    the frontend.

    Rules
    -----
    * ``None``    → ``""``
    * ``str``     → returned as-is
    * ``dict``    → JSON stringified with ``ensure_ascii=False``
    * ``list``    → joined into a newline-separated string
    * ``int``/``float``/``bool`` → converted with ``str``
    * anything else → ``str(value)`` or ``""`` if falsy

    Non-str inputs are logged as warnings to stderr.
    """
    import sys

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        print(
            f"[CASE_STUDY] WARNING: field {field_name!r} is a dict — "
            f"expected str. keys={list(value.keys())}",
            file=sys.stderr,
        )
        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, list):
        print(
            f"[CASE_STUDY] WARNING: field {field_name!r} is a list — expected str.",
            file=sys.stderr,
        )
        return "\n".join(str(item) for item in value if item is not None)

    if isinstance(value, (int, float, bool)):
        return str(value)

    print(
        f"[CASE_STUDY] WARNING: field {field_name!r} has unexpected type "
        f"{type(value).__name__!r}.",
        file=sys.stderr,
    )
    return str(value) if value else ""


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class CaseStudyState(rx.State):
    """
    Flat, primitive-only state for the case-study page.

    All fields are plain ``str`` or ``list[str]`` so Reflex serialises them
    as JSON scalars / arrays — never as nested objects that could end up
    inside rx.markdown() as [object Object].

    The raw project dict is intentionally *not* stored as a state var.
    It is only used as a local variable inside load_project().
    """

    # ── primitive state vars (serialised safely to the frontend) ──────────
    not_found:       bool      = False
    is_loading:      bool      = False   # True while load_project is running
    has_case_study_content: bool = False
    project_name:    str       = ""
    project_tags:    list[str] = []
    cs_problem:      str       = ""
    cs_problem_html: str       = ""
    cs_architecture: str       = ""
    cs_architecture_html: str   = ""
    cs_stack_reason: str       = ""
    cs_stack_reason_html: str   = ""
    cs_challenges:   str       = ""
    cs_challenges_html: str    = ""
    cs_learnings:    str       = ""
    cs_learnings_html: str     = ""
    cs_arch_image:   str       = ""

    # ── event handlers ────────────────────────────────────────────────────

    def _markdown_to_html(self, value: str) -> str:
        return md.markdown(value or "", extensions=["fenced_code", "tables", "nl2br"])

    @rx.event
    def redirect_legacy_route(self):
        """
        Called by the /projects/[slug] alias page.
        Immediately 301-equivalent client-side redirect to /portfolio/[slug].
        """
        slug = self.router.url.path.rsplit("/", 1)[-1]
        from harun_site.utils.data_manager import get_project_by_slug

        project = get_project_by_slug(slug) if slug else None
        target = project.get("url") if project and project.get("url") else "/portfolio"
        print(f"[CASE_STUDY] legacy /projects/{slug} → {target}")
        return rx.redirect(target)

    @rx.event
    def load_project(self):  # noqa: C901
        # ─────────────────────────────────────────────────────────────── #
        # PHASE 1: Instantly clear stale data and show loading indicator.      #
        # yield sends this partial state to the frontend before the file I/O.  #
        # Without this, navigating A → B shows A's content until B is ready.  #
        # ─────────────────────────────────────────────────────────────── #
        self.is_loading      = True
        self.not_found       = False
        self.project_name    = ""
        self.project_tags    = []
        self.cs_problem      = ""
        self.cs_problem_html = ""
        self.cs_architecture = ""
        self.cs_architecture_html = ""
        self.cs_stack_reason = ""
        self.cs_stack_reason_html = ""
        self.cs_challenges   = ""
        self.cs_challenges_html = ""
        self.cs_learnings    = ""
        self.cs_learnings_html = ""
        self.cs_arch_image   = ""
        self.has_case_study_content = False
        yield  # ← sends is_loading=True + cleared state to frontend NOW

        slug = self.router.url.path.rsplit("/", 1)[-1]
        print(f"[CASE_STUDY] load_project slug={slug!r}", file=sys.stderr)

        from harun_site.utils.data_manager import get_project_by_slug
        p = get_project_by_slug(slug)

        # ── project not found ───────────────────────────────────────────────────
        if p is None:
            print(f"[CASE_STUDY] slug={slug!r} not found", file=sys.stderr)
            self.not_found   = True
            self.is_loading  = False
            return

        self.not_found = False

        # ── validate case_study block ────────────────────────────────────────────
        cs_raw = p.get("case_study")
        if not isinstance(cs_raw, dict):
            print(
                f"[CASE_STUDY] WARNING: case_study block for slug={slug!r} "
                f"is {type(cs_raw).__name__!r}, not dict — treating as empty.",
                file=sys.stderr,
            )
            cs_raw = {}

        # ── normalise and assign every field ─────────────────────────────
        self.project_name = _safe_str(p.get("title") or p.get("name"), "title")

        # tags must be list[str]; validate each item
        raw_tags = p.get("tags")
        if isinstance(raw_tags, list):
            self.project_tags = [
                _safe_str(t, "tags[]") for t in raw_tags if t is not None
            ]
        else:
            print(
                f"[CASE_STUDY_DEBUG] WARNING: 'tags' is not a list "
                f"type={type(raw_tags).__name__} — using []"
            )
            self.project_tags = []

        self.cs_problem = _safe_str(
            cs_raw.get("problem"), "problem"
        )
        self.cs_problem_html = self._markdown_to_html(self.cs_problem)
        self.cs_architecture = _safe_str(
            cs_raw.get("architecture"), "architecture"
        )
        self.cs_architecture_html = self._markdown_to_html(self.cs_architecture)

        # Support both legacy key 'stack_reason' and new key 'why_this_stack'
        stack_raw = cs_raw.get("why_this_stack") or cs_raw.get("stack_reason")
        self.cs_stack_reason = _safe_str(
            stack_raw, "why_this_stack / stack_reason"
        )
        self.cs_stack_reason_html = self._markdown_to_html(self.cs_stack_reason)

        self.cs_challenges = _safe_str(
            cs_raw.get("challenges"), "challenges"
        )
        self.cs_challenges_html = self._markdown_to_html(self.cs_challenges)

        # Support both legacy key 'learnings' and new key 'lessons_learned'
        learnings_raw = (
            cs_raw.get("lessons_learned") or cs_raw.get("learnings")
        )
        self.cs_learnings = _safe_str(
            learnings_raw, "lessons_learned / learnings"
        )
        self.cs_learnings_html = self._markdown_to_html(self.cs_learnings)

        self.cs_arch_image = _safe_str(
            cs_raw.get("architecture_image"), "architecture_image"
        )

        self.has_case_study_content = any([
            self.cs_problem,
            self.cs_architecture,
            self.cs_stack_reason,
            self.cs_challenges,
            self.cs_learnings,
        ])
        # ── loading complete ────────────────────────────────────────────────────
        self.is_loading = False
        print(
            f"[CASE_STUDY] loaded slug={slug!r} "
            f"name={self.project_name!r} "
            f"has_content={self.has_case_study_content}",
            file=sys.stderr,
        )
