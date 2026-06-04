"""Internationalization (i18n) dictionary for the portfolio site.

All static UI text is stored here in TR / EN pairs.
Usage in components:
    from harun_site.utils.i18n import TXT
    from harun_site.state.language_state import LanguageState
    ...
    rx.cond(
        LanguageState.language == "en",
        rx.text(TXT["hello"]["en"]),
        rx.text(TXT["hello"]["tr"]),
    )
Or the shorthand via LanguageState instance.
"""

from __future__ import annotations


TXT: dict[str, dict[str, str]] = {
    # ── Navbar ────────────────────────────────────────────────
    "nav_home": {"tr": "Ana Sayfa", "en": "Home"},
    "nav_portfolio": {"tr": "Projeler", "en": "Projects"},
    "nav_blog": {"tr": "Blog", "en": "Blog"},
    "nav_about": {"tr": "Hakkında", "en": "About"},
    "nav_chat": {"tr": "Chat", "en": "Chat"},
    "nav_admin": {"tr": "Yönetim", "en": "Admin"},
    "nav_lang_tr": {"tr": "TR", "en": "TR"},
    "nav_lang_en": {"tr": "EN", "en": "EN"},

    # ── Index / Hero ──────────────────────────────────────────
    "hero_title": {
        "tr": "Merhaba, ben Harun Emirhan Bostancı",
        "en": "Hi, I'm Harun Emirhan Bostancı",
    },
    "hero_subtitle": {
        "tr": "Data Science & AI Engineer | LLM Orchestrator",
        "en": "Data Science & AI Engineer | LLM Orchestrator",
    },
    "hero_desc": {
        "tr": "Kurumsal yapay zeka çözümleri, full-stack mühendislik ve modüler sistem mimarileri üzerine çalışıyorum. Reflex, FastAPI ve modern AI stack ile üretim odaklı projeler geliştiriyorum.",
        "en": "I build enterprise AI solutions, full-stack engineering, and modular system architectures. I develop production-focused projects with Reflex, FastAPI, and the modern AI stack.",
    },
    "hero_chat_cta": {
        "tr": "AI Sohbet Asistanı",
        "en": "AI Chat Assistant",
    },
    "hero_portfolio_cta": {
        "tr": "Projeleri Keşfet",
        "en": "Explore Projects",
    },

    # ── Featured Projects ─────────────────────────────────────
    "featured_title": {
        "tr": "Öne Çıkan Projeler",
        "en": "Featured Projects",
    },
    "featured_view_all": {
        "tr": "Tüm Projeler",
        "en": "View All Projects",
    },
    "featured_case_study": {
        "tr": "Case Study →",
        "en": "Case Study →",
    },

    # ── Recent Posts ──────────────────────────────────────────
    "recent_posts": {
        "tr": "Son Yazılar",
        "en": "Recent Posts",
    },
    "recent_view_all": {
        "tr": "Tüm Yazılar",
        "en": "View All Posts",
    },
    "read_more": {
        "tr": "Devamını Oku →",
        "en": "Read More →",
    },

    # ── Skills ────────────────────────────────────────────────
    "skills_title": {
        "tr": "Yetenekler",
        "en": "Skills",
    },

    # ── Experience ────────────────────────────────────────────
    "experience_title": {
        "tr": "Deneyim",
        "en": "Experience",
    },

    # ── Portfolio Page ────────────────────────────────────────
    "portfolio_title": {
        "tr": "Projeler",
        "en": "Projects",
    },
    "portfolio_desc": {
        "tr": "Geliştirdiğim yapay zeka ve yazılım projeleri. Her proje için detaylı case study mevcut.",
        "en": "AI and software projects I've built. Each project has a detailed case study.",
    },
    "portfolio_filter": {
        "tr": "Filtrele",
        "en": "Filter",
    },
    "portfolio_search": {
        "tr": "Proje ara...",
        "en": "Search projects...",
    },
    "portfolio_clear": {
        "tr": "Temizle",
        "en": "Clear",
    },

    # ── Case Study ────────────────────────────────────────────
    "cs_problem": {"tr": "Problem", "en": "Problem"},
    "cs_architecture": {"tr": "Mimari", "en": "Architecture"},
    "cs_stack": {"tr": "Teknoloji Seçimi", "en": "Tech Stack"},
    "cs_challenges": {"tr": "Zorluklar", "en": "Challenges"},
    "cs_learnings": {"tr": "Öğrenilenler", "en": "Learnings"},
    "cs_back": {"tr": "← Projelere Dön", "en": "← Back to Projects"},
    "cs_tags": {"tr": "Etiketler", "en": "Tags"},

    # ── Blog Page ─────────────────────────────────────────────
    "blog_title": {
        "tr": "Blog",
        "en": "Blog",
    },
    "blog_desc": {
        "tr": "Yazılım mühendisliği, yapay zeka ve teknoloji üzerine yazılar.",
        "en": "Posts on software engineering, AI, and technology.",
    },
    "blog_search": {
        "tr": "Yazı ara...",
        "en": "Search posts...",
    },
    "blog_no_results": {
        "tr": "Sonuç bulunamadı.",
        "en": "No results found.",
    },
    "blog_tags": {
        "tr": "Etiketler",
        "en": "Tags",
    },
    "blog_back": {
        "tr": "← Blog'a Dön",
        "en": "← Back to Blog",
    },

    # ── About Page ────────────────────────────────────────────
    "about_title": {
        "tr": "Hakkımda",
        "en": "About Me",
    },
    "about_bio_title": {
        "tr": "Kimim?",
        "en": "Who Am I?",
    },
    "about_bio": {
        "tr": "Bilgisayar Mühendisliği mezunu, yapay zeka ve backend sistemleri üzerine uzmanlaşmış bir yazılım geliştiriciyim. RAG, LLM orchestrasyonu ve full-stack Python çözümleri ile üretim odaklı projeler geliştiriyorum.",
        "en": "A computer engineering graduate specialized in AI and backend systems. I develop production-focused projects with RAG, LLM orchestration, and full-stack Python solutions.",
    },
    "about_contact": {
        "tr": "İletişim",
        "en": "Contact",
    },
    "about_email": {
        "tr": "E-posta",
        "en": "Email",
    },
    "about_linkedin": {
        "tr": "LinkedIn",
        "en": "LinkedIn",
    },
    "about_github": {
        "tr": "GitHub",
        "en": "GitHub",
    },
    "about_download_cv": {
        "tr": "CV İndir",
        "en": "Download CV",
    },

    # ── Education ─────────────────────────────────────────────
    "education_title": {
        "tr": "Eğitim",
        "en": "Education",
    },

    # ── Chat ──────────────────────────────────────────────────
    "chat_title": {
        "tr": "AI Sohbet",
        "en": "AI Chat",
    },
    "chat_desc": {
        "tr": "Harun Emirhan, projeleri ve deneyimleri hakkında soru sor.",
        "en": "Ask questions about Harun Emirhan, his projects, and experience.",
    },
    "chat_placeholder": {
        "tr": "sor...",
        "en": "ask...",
    },
    "chat_how_it_works": {
        "tr": "Nasıl çalışır?",
        "en": "How it works?",
    },
    "chat_api_info": {
        "tr": "DeepSeek API · Dinamik context · Streaming",
        "en": "DeepSeek API · Dynamic context · Streaming",
    },
    "chat_redirect": {
        "tr": "Daha derin sohbet için →",
        "en": "For deeper chat →",
    },
    "chat_fullscreen": {
        "tr": "Tam ekran aç",
        "en": "Open fullscreen",
    },
    "chat_reset": {
        "tr": "Sohbet sıfırlandı.",
        "en": "Chat reset.",
    },
    "chat_new_conv": {
        "tr": "Yeni konuşma",
        "en": "New conversation",
    },
    "chat_suggest_title": {
        "tr": "Bir soru seç:",
        "en": "Choose a question:",
    },
    "chat_greeting": {
        "tr": "Merhaba! Harun Emirhan ve projeleri hakkında merak ettiklerini bana sorabilirsin. 💬",
        "en": "Hi! Feel free to ask me about Harun Emirhan and his projects. 💬",
    },

    # ── Error Pages ───────────────────────────────────────────
    "not_found_title": {
        "tr": "Sayfa Bulunamadı",
        "en": "Page Not Found",
    },
    "not_found_desc": {
        "tr": "Aradığın sayfa mevcut değil.",
        "en": "The page you're looking for doesn't exist.",
    },
    "not_found_home": {
        "tr": "Ana Sayfa'ya Dön",
        "en": "Back to Home",
    },

    # ── Footer ────────────────────────────────────────────────
    "footer_tagline": {
        "tr": "Python ile inşa edildi. Reflex ile çalışıyor.",
        "en": "Built with Python. Powered by Reflex.",
    },
    "footer_build": {
        "tr": "Harun Emirhan Bostancı",
        "en": "Harun Emirhan Bostancı",
    },
    "footer_rights": {
        "tr": "Tüm hakları saklıdır.",
        "en": "All rights reserved.",
    },
}


def _(key: str, lang: str = "tr") -> str:
    """Get a translated text by key and language.
    Falls back to TR if the key or language is missing.
    """
    entry = TXT.get(key)
    if not entry:
        return f"!{key}"
    return entry.get(lang, entry.get("tr", f"!{key}"))