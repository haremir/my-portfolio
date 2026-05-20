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
    becomes `[object Object]` as rx.markdown()'s children → crash.

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
Canonical URL:  /projects/[slug]   ← primary, used in all links
Legacy alias:   /portfolio/[slug]  ← redirect → /projects/[slug]
"""
from __future__ import annotations

import reflex as rx


# ---------------------------------------------------------------------------
# _safe_str  —  the only place that touches raw JSON values
# ---------------------------------------------------------------------------

def _safe_str(value: object, field_name: str = "unknown") -> str:
    """
    Convert *any* value to a plain Python ``str`` that is safe to pass to
    ``rx.markdown()``.

    Rules
    -----
    * ``None``    → ``""``
    * ``str``     → returned as-is
    * ``dict``    → tries common content keys; falls back to joining values
    * ``list``    → joins all items as strings
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
        for key in ("content", "text", "value", "body", "description", "summary"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
        parts = [str(v) for v in value.values() if v is not None]
        return " ".join(parts)

    if isinstance(value, list):
        print(
            f"[CASE_STUDY] WARNING: field {field_name!r} is a list — expected str.",
            file=sys.stderr,
        )
        return " ".join(str(item) for item in value if item is not None)

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
    project_name:    str       = ""
    project_tags:    list[str] = []
    cs_problem:      str       = ""
    cs_architecture: str       = ""
    cs_stack_reason: str       = ""
    cs_challenges:   str       = ""
    cs_learnings:    str       = ""
    cs_arch_image:   str       = ""

    # ── computed vars ─────────────────────────────────────────────────────

    @rx.var
    def has_case_study_content(self) -> bool:
        """
        True when at least one case-study section has real content.

        Safe to use as @rx.var: reads only flat str state vars — never
        a dict, never a computed chain on self.project.
        """
        return any([
            self.cs_problem,
            self.cs_architecture,
            self.cs_stack_reason,
            self.cs_challenges,
            self.cs_learnings,
        ])

    # ── event handlers ────────────────────────────────────────────────────

    @rx.event
    def redirect_legacy_route(self):
        """
        Called by the /portfolio/[slug] alias page.
        Immediately 301-equivalent client-side redirect to /projects/[slug].
        """
        slug = self.router.page.params.get("slug", "")
        target = f"/projects/{slug}" if slug else "/portfolio"
        print(f"[CASE_STUDY] legacy /portfolio/{slug} → {target}")
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
        self.cs_architecture = ""
        self.cs_stack_reason = ""
        self.cs_challenges   = ""
        self.cs_learnings    = ""
        self.cs_arch_image   = ""
        yield  # ← sends is_loading=True + cleared state to frontend NOW

        slug = self.router.page.params.get("slug", "")
        import sys
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
        self.project_name = _safe_str(p.get("name"), "name")

        # tags must be list[str]; validate each item
        raw_tags = p.get("tags")
        if isinstance(raw_tags, list):
            self.project_tags = [
                str(t) for t in raw_tags if t is not None
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
        self.cs_architecture = _safe_str(
            cs_raw.get("architecture"), "architecture"
        )

        # Support both legacy key 'stack_reason' and new key 'why_this_stack'
        stack_raw = cs_raw.get("why_this_stack") or cs_raw.get("stack_reason")
        self.cs_stack_reason = _safe_str(
            stack_raw, "why_this_stack / stack_reason"
        )

        self.cs_challenges = _safe_str(
            cs_raw.get("challenges"), "challenges"
        )

        # Support both legacy key 'learnings' and new key 'lessons_learned'
        learnings_raw = (
            cs_raw.get("lessons_learned") or cs_raw.get("learnings")
        )
        self.cs_learnings = _safe_str(
            learnings_raw, "lessons_learned / learnings"
        )

        self.cs_arch_image = _safe_str(
            cs_raw.get("architecture_image"), "architecture_image"
        )

        # ── loading complete ────────────────────────────────────────────────────
        self.is_loading = False
        print(
            f"[CASE_STUDY] loaded slug={slug!r} "
            f"name={self.project_name!r} "
            f"has_content={self.has_case_study_content}",
            file=sys.stderr,
        )
