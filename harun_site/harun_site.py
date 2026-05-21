import reflex as rx

from harun_site.pages.index import index
from harun_site.pages.blog import blog
from harun_site.pages.blog_post import blog_post_page as blog_post, BlogPostState
from harun_site.pages.about import about_page as about
from harun_site.pages.chat import chat_page as chat
from harun_site.pages.admin import admin_page as admin, AdminEduExpState
from harun_site.pages.portfolio import portfolio_page as portfolio, PortfolioState
from harun_site.pages.case_study import case_study, portfolio_slug_redirect
from harun_site.state.index_state import IndexState
from harun_site.state.blog_state import BlogState
from harun_site.state.about_state import AboutState
from harun_site.state.chat_state import ChatState
from harun_site.state.admin_state import AdminState
from harun_site.state.case_study_state import CaseStudyState
from harun_site.components.floating_chat import FloatingChatState
from harun_site import models
from harun_site.theme import APP_THEME
# models.ensure_tables() is called at the bottom of this file, after
# rx.App() is fully constructed, so rxconfig is guaranteed to be loaded.

app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
    ],
    head_components=[
        # Auto-scroll chat containers to bottom during streaming.
        # Watches #chat-messages-main and #chat-messages-floating via
        # MutationObserver.  Loaded on every page so the floating chat
        # popup (which appears on all pages) is always covered.
        rx.script(src="/chat_scroll.js"),
    ]
)

app.add_page(index, route="/", on_load=[IndexState.on_load, FloatingChatState.on_load])
app.add_page(about, route="/about", on_load=[AboutState.on_load, FloatingChatState.on_load])
app.add_page(portfolio, route="/portfolio", on_load=[PortfolioState.on_load, FloatingChatState.on_load])
# /projects/[slug]  — canonical route, used in all internal links
app.add_page(case_study, route="/projects/[slug]", on_load=[CaseStudyState.load_project, FloatingChatState.on_load])
# /portfolio/[slug] — legacy alias: immediately redirects to /projects/[slug]
app.add_page(portfolio_slug_redirect, route="/portfolio/[slug]", on_load=CaseStudyState.redirect_legacy_route)
app.add_page(blog, route="/blog", on_load=[BlogState.on_load, FloatingChatState.on_load])
app.add_page(blog_post, route="/blog/[slug]", on_load=[BlogPostState.load_post, FloatingChatState.on_load])
app.add_page(chat, route="/chat", on_load=[ChatState.on_load, ChatState.load_from_params])
app.add_page(admin, route="/admin", on_load=[AdminState.load_admin_data, AdminEduExpState.on_load])

# ── Startup checks ─────────────────────────────────────────────────────────
import sys as _sys
import os as _os

# 1. Database tables — must run AFTER rx.App() so rxconfig is loaded.
models.ensure_tables()

# 2. Groq API key — warn immediately if missing rather than failing silently
#    on the first user chat request.
from harun_site.utils.groq_client import validate_groq_key
validate_groq_key()

# 3. Admin password security check
_admin_pw = _os.environ.get("ADMIN_PASSWORD", "")
if not _admin_pw or _admin_pw == "admin123":
    print(
        "[SECURITY] WARNING: ADMIN_PASSWORD is "
        + ("not set — defaulting to 'admin123'" if not _admin_pw else "still set to the default 'admin123'"),
        file=_sys.stderr,
    )
    print(
        "[SECURITY] Set a strong ADMIN_PASSWORD env var before deploying to production!",
        file=_sys.stderr,
    )

del _sys, _os, _admin_pw
