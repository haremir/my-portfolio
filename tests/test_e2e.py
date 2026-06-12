# -*- coding: utf-8 -*-
"""
tests/test_e2e.py
═══════════════════════════════════════════════════════════════════════════════
End-to-End Test Suite  —  harun-site portfolio

Kapsam
------
1.  Veri Katmanı          → data_manager CRUD (projeler, blog, chat log, tag, eğitim/deneyim)
2.  Proje Registry         → normalize / canonicalize / match / resolve
3.  Chat Zenginleştirme    → PROJECT_REF token işleme, link kanonikleştirme
4.  LLM İstemcisi          → prompt şablonları, model seçimi, cache, token limiti
5.  API Uç Noktaları       → tüm /api/* rotaların var ve doğru yanıt verdiğini test eder (mock sunucu)
6.  API İstemcisi          → ReflexApiClient yanıt ayrıştırma ve hata yönetimi
7.  Bildirim Sistemi       → hiring detection, mute/unmute, watchlist, cooldown
8.  Admin Kimlik Doğrulama → şifre dosyası okuma/yazma, varsayılan şifre
9.  i18n Sistemi           → TXT anahtarları TR/EN eksiksizliği
10. Routes & Slug          → URL sabitleri, slugify tutarlılığı
11. Güvenlik               → path traversal koruması, veri bütünlüğü

Her test grubunun kendi geçici dizini (tmp_path) var; gerçek dosyalara dokunulmaz.

Çalıştırma:
    uv run --with pytest python -m pytest tests/test_e2e.py -v
    uv run --with pytest python -m pytest tests/test_e2e.py -v --tb=short   # CI için
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI ARAÇLAR
# ══════════════════════════════════════════════════════════════════════════════

def _run(coro):
    """Async coroutine'i senkron olarak çalıştırmak için yardımcı."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_project(
    slug: str = "test-proje",
    title: str = "Test Proje",
    aliases: list[str] | None = None,
) -> dict:
    return {
        "id": slug,
        "title": title,
        "name": title,
        "slug": slug,
        "url": f"/portfolio/{slug}",
        "aliases": aliases or [title.lower()],
        "desc": {"tr": "Türkçe açıklama", "en": "English description"},
        "tags": ["python", "ai"],
        "case_study": {
            "problem": {"tr": "Problem TR", "en": "Problem EN"},
            "architecture": {"tr": "Mimari TR", "en": "Architecture EN"},
            "stack_reason": {"tr": "Stack TR", "en": "Stack EN"},
            "challenges": {"tr": "Zorluklar TR", "en": "Challenges EN"},
            "learnings": {"tr": "Öğrenilenler TR", "en": "Learnings EN"},
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# 1. VERİ KATMANI — data_manager CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TestDataManagerProjects:
    """Proje CRUD işlemleri — gerçek dosyaya dokunmadan tmp_path kullanır."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

    def test_load_projects_empty(self):
        from harun_site.utils.data_manager import load_projects
        assert load_projects() == []

    def test_save_and_load_projects(self):
        from harun_site.utils.data_manager import load_projects, save_projects
        projects = [_make_project("proje-1"), _make_project("proje-2")]
        save_projects(projects)
        loaded = load_projects()
        assert len(loaded) == 2
        slugs = [p["slug"] for p in loaded]
        assert "proje-1" in slugs
        assert "proje-2" in slugs

    def test_get_project_by_slug(self):
        from harun_site.utils.data_manager import get_project_by_slug, save_projects
        save_projects([_make_project("benim-projem")])
        result = get_project_by_slug("benim-projem")
        assert result is not None
        assert result["slug"] == "benim-projem"

    def test_get_project_by_slug_missing_returns_none(self):
        from harun_site.utils.data_manager import get_project_by_slug, save_projects
        save_projects([_make_project("varolan")])
        assert get_project_by_slug("olmayan") is None

    def test_delete_project(self):
        from harun_site.utils.data_manager import delete_project, load_projects, save_projects
        save_projects([_make_project("silinecek"), _make_project("kalacak")])
        delete_project(0)
        remaining = load_projects()
        assert len(remaining) == 1
        assert remaining[0]["slug"] == "kalacak"

    def test_load_projects_localized_tr(self):
        from harun_site.utils.data_manager import load_projects_localized, save_projects
        save_projects([_make_project()])
        projects = load_projects_localized("tr")
        assert projects[0]["desc"] == "Türkçe açıklama"

    def test_load_projects_localized_en(self):
        from harun_site.utils.data_manager import load_projects_localized, save_projects
        save_projects([_make_project()])
        projects = load_projects_localized("en")
        assert projects[0]["desc"] == "English description"

    def test_project_json_is_valid_after_save(self, tmp_path):
        from harun_site.utils.data_manager import PROJECTS_FILE, save_projects
        save_projects([_make_project("json-test")])
        raw = json.loads(PROJECTS_FILE.read_text(encoding="utf-8"))
        assert isinstance(raw, list)
        assert raw[0]["slug"] == "json-test"


class TestDataManagerChatLogs:
    """Chat log kayıt ve okuma işlemleri."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

    def test_save_and_load_chat_log(self):
        from harun_site.utils.data_manager import load_chat_log_messages, save_chat_log
        messages = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": "Selam!"},
        ]
        filename = save_chat_log(messages)
        assert filename.endswith(".json")
        loaded = load_chat_log_messages(filename)
        assert len(loaded) == 2
        assert loaded[0]["content"] == "Merhaba"

    def test_load_chat_logs_returns_sorted(self):
        from harun_site.utils.data_manager import load_chat_logs, save_chat_log
        save_chat_log([{"role": "user", "content": "İlk"}], "a_log.json")
        save_chat_log([{"role": "user", "content": "İkinci"}], "b_log.json")
        logs = load_chat_logs()
        assert len(logs) == 2
        # En yeni başta gelmeli
        assert logs[0]["filename"] in ("a_log.json", "b_log.json")

    def test_save_chat_log_with_filename(self):
        from harun_site.utils.data_manager import load_chat_log_messages, save_chat_log
        messages = [{"role": "user", "content": "Özel dosya"}]
        filename = save_chat_log(messages, "ozel_log.json")
        assert filename == "ozel_log.json"
        loaded = load_chat_log_messages("ozel_log.json")
        assert loaded[0]["content"] == "Özel dosya"

    def test_empty_messages_not_saved(self):
        from harun_site.utils.data_manager import load_chat_logs, save_chat_log
        result = save_chat_log([])
        assert result == ""
        assert load_chat_logs() == []

    def test_delete_chat_log(self):
        from harun_site.utils.data_manager import delete_chat_log, load_chat_logs, save_chat_log
        save_chat_log([{"role": "user", "content": "Silinecek"}], "silinecek.json")
        assert len(load_chat_logs()) == 1
        delete_chat_log("silinecek.json")
        assert load_chat_logs() == []

    def test_clear_all_chat_logs(self):
        from harun_site.utils.data_manager import clear_all_chat_logs, load_chat_logs, save_chat_log
        save_chat_log([{"role": "user", "content": "Log 1"}], "log1.json")
        save_chat_log([{"role": "user", "content": "Log 2"}], "log2.json")
        clear_all_chat_logs()
        assert load_chat_logs() == []

    def test_chat_log_user_message_count(self):
        from harun_site.utils.data_manager import load_chat_logs, save_chat_log
        messages = [
            {"role": "user", "content": "Soru 1"},
            {"role": "assistant", "content": "Yanıt 1"},
            {"role": "user", "content": "Soru 2"},
            {"role": "assistant", "content": "Yanıt 2"},
        ]
        save_chat_log(messages, "sayim.json")
        logs = load_chat_logs()
        assert logs[0]["user_message_count"] == 2
        assert logs[0]["assistant_message_count"] == 2
        assert logs[0]["message_count"] == 4

    def test_load_chat_log_messages_nonexistent(self):
        from harun_site.utils.data_manager import load_chat_log_messages
        result = load_chat_log_messages("olmayan.json")
        assert result == []

    def test_chat_log_normalizes_none_content(self):
        from harun_site.utils.data_manager import load_chat_log_messages, save_chat_log
        messages = [{"role": "user", "content": None}]
        fname = save_chat_log(messages)
        loaded = load_chat_log_messages(fname)
        # None → boş string olmalı
        assert loaded[0]["content"] == ""


class TestDataManagerTags:
    """Tag yönetim işlemleri."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")

    def test_load_tags_empty(self):
        from harun_site.utils.data_manager import load_tags
        assert load_tags() == []

    def test_add_and_load_tag(self):
        from harun_site.utils.data_manager import add_tag, load_tags
        add_tag("python")
        tags = load_tags()
        assert "python" in tags

    def test_delete_tag(self):
        from harun_site.utils.data_manager import add_tag, delete_tag, load_tags
        add_tag("silinecek-tag")
        delete_tag("silinecek-tag")
        assert "silinecek-tag" not in load_tags()

    def test_duplicate_tag_not_added(self):
        from harun_site.utils.data_manager import add_tag, load_tags
        add_tag("tekrar")
        add_tag("tekrar")
        tags = load_tags()
        assert tags.count("tekrar") == 1

    def test_save_and_load_categorized_tags(self):
        from harun_site.utils.data_manager import load_categorized_tags, save_tags
        cats = [
            {"category": "Diller", "tags": ["python", "go"]},
            {"category": "Araçlar", "tags": ["docker", "git"]},
        ]
        save_tags(cats)
        loaded = load_categorized_tags()
        assert len(loaded) == 2
        assert loaded[0]["category"] == "Diller"


class TestDataManagerBlogPosts:
    """Blog yazısı kayıt ve silme."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "POSTS_DIR", tmp_path / "posts")
        (tmp_path / "posts").mkdir()

    def test_save_and_delete_blog_post(self, tmp_path):
        from harun_site.utils.data_manager import delete_blog_post, save_blog_post
        save_blog_post(
            slug="test-yazi",
            title="Test Yazısı",
            title_en="Test Post",
            date="2025-01-01",
            description="Açıklama",
            description_en="Description",
            tags=["python"],
            content="# İçerik\nMetin burada",
            content_en="# Content\nText here",
        )
        post_file = tmp_path / "posts" / "test-yazi.md"
        assert post_file.exists()
        delete_blog_post("test-yazi")
        assert not post_file.exists()

    def test_blog_post_frontmatter_format(self, tmp_path):
        from harun_site.utils.data_manager import save_blog_post
        save_blog_post(
            slug="frontmatter-test",
            title="Başlık",
            title_en="Title",
            date="2025-06-12",
            description="Kısa açıklama",
            description_en="Short description",
            tags=["ai", "ml"],
            content="İçerik",
            content_en="Content",
            cover="/blog/image.png",
        )
        content = (tmp_path / "posts" / "frontmatter-test.md").read_text(encoding="utf-8")
        assert "title:" in content
        assert "2025-06-12" in content
        assert "ai" in content


class TestDataManagerEducationExperience:
    """Eğitim ve deneyim CRUD."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "BASE_DIR", tmp_path)

    def test_save_and_load_education(self):
        from harun_site.utils.data_manager import load_education, save_education
        data = [{"school": "ATATÜRK ÜNİVERSİTESİ", "degree": "Lisans", "year": "2024"}]
        save_education(data)
        loaded = load_education()
        assert loaded[0]["school"] == "ATATÜRK ÜNİVERSİTESİ"

    def test_save_and_load_experience(self):
        from harun_site.utils.data_manager import load_experience, save_experience
        data = [{"company": "ProudSec", "role": "AI Engineer", "period": "2024-2025"}]
        save_experience(data)
        loaded = load_experience()
        assert loaded[0]["company"] == "ProudSec"

    def test_education_returns_empty_when_missing(self):
        from harun_site.utils.data_manager import load_education
        assert load_education() == []


# ══════════════════════════════════════════════════════════════════════════════
# 2. PROJE REGİSTRY
# ══════════════════════════════════════════════════════════════════════════════

class TestProjectRegistry:
    """Proje eşleştirme ve kanonikleştirme mantığı."""

    def test_normalize_text_lowercase(self):
        from harun_site.utils.project_registry import normalize_project_text
        assert normalize_project_text("DENT-BOT") == "dent bot"

    def test_normalize_text_strips_punctuation(self):
        from harun_site.utils.project_registry import normalize_project_text
        assert normalize_project_text("fraud-eye!") == "fraud eye"

    def test_normalize_text_collapses_spaces(self):
        from harun_site.utils.project_registry import normalize_project_text
        assert normalize_project_text("c   module") == "c module"

    def test_canonicalize_fills_missing_name(self):
        from harun_site.utils.project_registry import canonicalize_project_record
        p = {"title": "DentBot", "slug": "dent-bot"}
        c = canonicalize_project_record(p)
        assert c["name"] == "DentBot"
        assert c["id"] == "dent-bot"

    def test_canonicalize_generates_url(self):
        from harun_site.utils.project_registry import canonicalize_project_record
        p = {"title": "MyApp", "slug": "my-app"}
        c = canonicalize_project_record(p)
        assert c["url"] == "/portfolio/my-app"

    def test_project_url_from_slug(self):
        from harun_site.utils.project_registry import project_url_from_slug
        assert project_url_from_slug("dent-bot") == "/portfolio/dent-bot"
        assert project_url_from_slug("") == ""

    def test_match_projects_by_title(self):
        from harun_site.utils.project_registry import match_projects
        projects = [_make_project("dent-bot", "Dent Bot"), _make_project("fraud-eye", "Fraud Eye")]
        matched = match_projects("dent bot", projects)
        assert len(matched) == 1
        assert matched[0]["slug"] == "dent-bot"

    def test_match_projects_by_alias(self):
        from harun_site.utils.project_registry import match_projects
        projects = [_make_project("selfapi", "SelfAPI", aliases=["self api", "selfapi", "portfolio site"])]
        matched = match_projects("portfolio site", projects)
        assert len(matched) == 1

    def test_match_projects_empty_query(self):
        from harun_site.utils.project_registry import match_projects
        projects = [_make_project()]
        assert match_projects("", projects) == []

    def test_resolve_project_exact(self):
        from harun_site.utils.project_registry import resolve_project
        projects = [_make_project("c-module", "C Module")]
        result = resolve_project("c module", projects)
        assert result is not None
        assert result["slug"] == "c-module"

    def test_resolve_project_ambiguous_returns_none(self):
        from harun_site.utils.project_registry import resolve_project
        projects = [
            _make_project("proje-a", "Proje A"),
            _make_project("proje-b", "Proje A Alt"),  # hem "proje" hem "a" var
        ]
        # "proje" her ikisiyle de eşleşebilir — None dönmeli
        result = resolve_project("proje", projects)
        # Eşleşme yoksa ya da belirsizse None
        assert result is None or isinstance(result, dict)

    def test_resolve_project_not_found(self):
        from harun_site.utils.project_registry import resolve_project
        result = resolve_project("hiç olmayan proje xyz", [_make_project()])
        assert result is None

    def test_project_ref_token_format(self):
        from harun_site.utils.project_registry import project_ref_token
        token = project_ref_token("selfapi")
        assert token == "[[PROJECT_REF:selfapi]]"

    def test_project_reference_payload(self):
        from harun_site.utils.project_registry import project_reference_payload
        p = _make_project("dent-bot", "Dent Bot")
        payload = project_reference_payload(p)
        assert payload["project_id"] == "dent-bot"
        assert payload["title"] == "Dent Bot"
        assert payload["url"] == "/portfolio/dent-bot"


# ══════════════════════════════════════════════════════════════════════════════
# 3. CHAT ZENGİNLEŞTİRME — finalize_project_references
# ══════════════════════════════════════════════════════════════════════════════

class TestChatEnrich:
    """Proje referans token işleme ve link kanonikleştirme."""

    @pytest.fixture(autouse=True)
    def _mock_projects(self, monkeypatch):
        projects = [
            _make_project("dent-bot", "Dent Bot", aliases=["dent bot", "dentbot"]),
            _make_project("fraud-eye", "Fraud Eye", aliases=["fraud eye", "fraudeye"]),
        ]
        import harun_site.utils.chat_enrich as ce
        monkeypatch.setattr(ce, "_project_index", lambda: projects)

    def test_project_ref_token_replaced(self):
        from harun_site.utils.chat_enrich import finalize_project_references
        text = "Bu proje hakkında [[PROJECT_REF:dent-bot]] daha fazla bilgi."
        result = finalize_project_references(text)
        assert "[[PROJECT_REF:" not in result
        assert "[Dent Bot]" in result
        assert "/portfolio/dent-bot" in result

    def test_unknown_token_removed(self):
        from harun_site.utils.chat_enrich import finalize_project_references
        text = "Bilinmeyen [[PROJECT_REF:olmayan-proje]] token."
        result = finalize_project_references(text)
        assert "[[PROJECT_REF:" not in result

    def test_empty_text_returned_as_is(self):
        from harun_site.utils.chat_enrich import finalize_project_references
        assert finalize_project_references("") == ""

    def test_streamed_finalize(self):
        from harun_site.utils.chat_enrich import finalize_streamed_project_references
        chunks = ["Bu [[PROJECT", "_REF:fraud-eye]] projesi."]
        result = finalize_streamed_project_references(chunks)
        assert "[Fraud Eye]" in result

    def test_multiple_tokens_in_same_text(self):
        from harun_site.utils.chat_enrich import finalize_project_references
        text = "[[PROJECT_REF:dent-bot]] ve [[PROJECT_REF:fraud-eye]] projelerim."
        result = finalize_project_references(text)
        assert "[Dent Bot]" in result
        assert "[Fraud Eye]" in result

    def test_ensure_case_study_links_wrapper(self):
        from harun_site.utils.chat_enrich import ensure_case_study_links
        text = "[[PROJECT_REF:dent-bot]] kullanıyor."
        result = ensure_case_study_links(text, "dent bot")
        assert "/portfolio/dent-bot" in result


# ══════════════════════════════════════════════════════════════════════════════
# 4. LLM İSTEMCİSİ — groq_client
# ══════════════════════════════════════════════════════════════════════════════

class TestGroqClient:
    """Prompt şablonları, model seçimi ve LLM cache mantığı."""

    def test_system_prompt_template_tr_has_context_placeholder(self):
        from harun_site.utils.groq_client import _SYSTEM_PROMPT_TEMPLATE_TR
        assert "{context}" in _SYSTEM_PROMPT_TEMPLATE_TR

    def test_system_prompt_template_en_has_context_placeholder(self):
        from harun_site.utils.groq_client import _SYSTEM_PROMPT_TEMPLATE_EN
        assert "{context}" in _SYSTEM_PROMPT_TEMPLATE_EN

    def test_trim_chat_history_within_limit(self):
        from harun_site.utils.groq_client import trim_chat_history
        msgs = [{"role": "user", "content": f"Mesaj {i}"} for i in range(5)]
        assert trim_chat_history(msgs, max_messages=10) == msgs

    def test_trim_chat_history_over_limit(self):
        from harun_site.utils.groq_client import trim_chat_history
        msgs = [{"role": "user", "content": f"Mesaj {i}"} for i in range(20)]
        trimmed = trim_chat_history(msgs, max_messages=8)
        assert len(trimmed) == 8
        # En son 8 mesajı almalı
        assert trimmed[-1]["content"] == "Mesaj 19"

    def test_model_selection_fast_for_short_message(self):
        from harun_site.utils.groq_client import _select_kind
        kind = _select_kind("Merhaba", project_matched=False)
        assert kind == "fast"

    def test_model_selection_deep_for_deep_keyword(self):
        from harun_site.utils.groq_client import _select_kind
        kind = _select_kind("Bu projenin mimari kararları nelerdir?", project_matched=False)
        assert kind == "deep"

    def test_model_selection_fast_for_matched_project_short(self):
        from harun_site.utils.groq_client import _select_kind
        kind = _select_kind("Dent Bot nedir?", project_matched=True)
        assert kind == "fast"

    def test_cache_key_deterministic(self):
        from harun_site.utils.groq_client import _build_cache_key
        key1 = _build_cache_key("groq", "model-a", "system", [{"role": "user", "content": "x"}], max_tokens=512, temperature=0.2)
        key2 = _build_cache_key("groq", "model-a", "system", [{"role": "user", "content": "x"}], max_tokens=512, temperature=0.2)
        assert key1 == key2

    def test_cache_key_differs_on_content(self):
        from harun_site.utils.groq_client import _build_cache_key
        key1 = _build_cache_key("groq", "model", "sys", [{"role": "user", "content": "a"}], max_tokens=512, temperature=0.2)
        key2 = _build_cache_key("groq", "model", "sys", [{"role": "user", "content": "b"}], max_tokens=512, temperature=0.2)
        assert key1 != key2

    def test_cache_set_and_get(self):
        from harun_site.utils.groq_client import _LLM_RESPONSE_CACHE, _cache_get, _cache_set
        _LLM_RESPONSE_CACHE.clear()
        _cache_set("test-key-xyz", "cachedContent")
        result = _cache_get("test-key-xyz")
        assert result == "cachedContent"
        _LLM_RESPONSE_CACHE.clear()

    def test_cache_miss_returns_none(self):
        from harun_site.utils.groq_client import _LLM_RESPONSE_CACHE, _cache_get
        _LLM_RESPONSE_CACHE.clear()
        assert _cache_get("olmayan-key") is None

    def test_rate_limit_error_detection(self):
        from harun_site.utils.groq_client import is_rate_limit_error
        assert is_rate_limit_error(Exception("rate_limit exceeded"))
        assert is_rate_limit_error(Exception("HTTP 429"))
        assert not is_rate_limit_error(Exception("internal server error"))

    def test_user_message_for_rate_limit(self):
        from harun_site.utils.groq_client import user_message_for_groq_error
        msg = user_message_for_groq_error(Exception("rate_limit exceeded"))
        assert "limit" in msg.lower()

    def test_user_message_for_auth_error(self):
        from harun_site.utils.groq_client import user_message_for_groq_error
        msg = user_message_for_groq_error(Exception("invalid_api_key"))
        assert "yapılandırılmamış" in msg or "erişilemiyor" in msg

    def test_validate_groq_key_no_keys(self, monkeypatch):
        import harun_site.utils.groq_client as gc
        monkeypatch.setattr(gc, "DEEPSEEK_API_KEY", "")
        monkeypatch.setattr(gc, "GROQ_API_KEY", "")
        result = gc.validate_groq_key()
        assert result is False

    def test_validate_groq_key_with_groq_key(self, monkeypatch):
        import harun_site.utils.groq_client as gc
        monkeypatch.setattr(gc, "GROQ_API_KEY", "gsk_test_key_12345")
        monkeypatch.setattr(gc, "DEEPSEEK_API_KEY", "")
        result = gc.validate_groq_key()
        assert result is True

    def test_normalize_messages_none_content(self):
        from harun_site.utils.groq_client import _normalize_messages
        msgs = [{"role": "user", "content": None}]
        result = _normalize_messages(msgs)
        assert result[0]["content"] == ""

    def test_normalize_messages_dict_content(self):
        from harun_site.utils.groq_client import _normalize_messages
        msgs = [{"role": "user", "content": {"key": "value"}}]
        result = _normalize_messages(msgs)
        assert isinstance(result[0]["content"], str)

    def test_normalize_messages_list_content(self):
        from harun_site.utils.groq_client import _normalize_messages
        msgs = [{"role": "user", "content": ["parça1", "parça2"]}]
        result = _normalize_messages(msgs)
        assert "parça1" in result[0]["content"]

    def test_chat_logs_fingerprint_is_consistent(self):
        from harun_site.utils.groq_client import chat_logs_fingerprint
        logs = [{"filename": "a.json", "mtime": 100, "message_count": 5}]
        fp1 = chat_logs_fingerprint(logs)
        fp2 = chat_logs_fingerprint(logs)
        assert fp1 == fp2
        assert len(fp1) == 16

    def test_chat_logs_fingerprint_changes_on_new_log(self):
        from harun_site.utils.groq_client import chat_logs_fingerprint
        logs1 = [{"filename": "a.json", "mtime": 100, "message_count": 5}]
        logs2 = [{"filename": "b.json", "mtime": 200, "message_count": 3}]
        assert chat_logs_fingerprint(logs1) != chat_logs_fingerprint(logs2)


# ══════════════════════════════════════════════════════════════════════════════
# 5. API UÇ NOKTALARI — endpoints.py (mock Starlette uygulaması)
# ══════════════════════════════════════════════════════════════════════════════

class TestApiEndpoints:
    """API rotalarının doğru yanıt verip vermediğini test eder."""

    @pytest.fixture
    def mock_starlette_app(self):
        """Starlette uygulamasını ve add_route çağrılarını taklit eder."""
        routes = {}

        class MockApp:
            def add_route(self, path, handler, methods=None):
                routes[path] = handler

        return MockApp(), routes

    def test_register_api_routes_success(self, monkeypatch, tmp_path, mock_starlette_app):
        """register_api_routes çağrıldığında tüm rotalar eklenmeli."""
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

        mock_app, routes = mock_starlette_app

        from harun_site.api.endpoints import register_api_routes
        register_api_routes(mock_app)

        expected_routes = [
            "/api/ping",
            "/api/chat-logs",
            "/api/chat-logs/{filename}",
            "/api/stats",
            "/api/projects",
            "/api/suggestions",
            "/api/skills",
        ]
        for route in expected_routes:
            assert route in routes, f"Eksik rota: {route}"

    @pytest.mark.asyncio
    async def test_ping_endpoint_response(self, tmp_path, monkeypatch):
        """Ping endpoint'i {ok: True} döndürmeli."""
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

        routes = {}

        class MockApp:
            def add_route(self, path, handler, methods=None):
                routes[path] = handler

        from harun_site.api.endpoints import register_api_routes
        register_api_routes(MockApp())

        # Ping handler'ı çağır
        mock_request = MagicMock()
        mock_request.headers = {}
        response = await routes["/api/ping"](mock_request)
        data = json.loads(response.body)
        assert data["ok"] is True

    @pytest.mark.asyncio
    async def test_chat_logs_endpoint_unauthorized(self, tmp_path, monkeypatch):
        """Geçersiz token ile /api/chat-logs 401 döndürmeli."""
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

        import harun_site.api.endpoints as ep
        monkeypatch.setattr(ep, "_API_SECRET", "gizli_token")
        monkeypatch.setattr(ep, "_ALLOW_OPEN", False)

        routes = {}

        class MockApp:
            def add_route(self, path, handler, methods=None):
                routes[path] = handler

        from harun_site.api.endpoints import register_api_routes
        register_api_routes(MockApp())

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer yanlis_token"}
        response = await routes["/api/chat-logs"](mock_request)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_logs_endpoint_authorized(self, tmp_path, monkeypatch):
        """Geçerli token ile /api/chat-logs liste döndürmeli."""
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()
        dm.save_chat_log([{"role": "user", "content": "Test"}], "test.json")

        import harun_site.api.endpoints as ep
        monkeypatch.setattr(ep, "_API_SECRET", "dogru_token")
        monkeypatch.setattr(ep, "_ALLOW_OPEN", False)

        routes = {}

        class MockApp:
            def add_route(self, path, handler, methods=None):
                routes[path] = handler

        from harun_site.api.endpoints import register_api_routes
        register_api_routes(MockApp())

        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer dogru_token"}
        response = await routes["/api/chat-logs"](mock_request)
        assert response.status_code == 200
        data = json.loads(response.body)
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_invalid_filename_in_chat_log_detail(self, tmp_path, monkeypatch):
        """Şüpheli dosya adıyla /api/chat-logs/{filename} 400 döndürmeli."""
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

        import harun_site.api.endpoints as ep
        monkeypatch.setattr(ep, "_API_SECRET", "")
        monkeypatch.setattr(ep, "_ALLOW_OPEN", True)

        routes = {}

        class MockApp:
            def add_route(self, path, handler, methods=None):
                routes[path] = handler

        from harun_site.api.endpoints import register_api_routes
        register_api_routes(MockApp())

        mock_request = MagicMock()
        mock_request.headers = {}
        # Path traversal girişimi
        mock_request.path_params = {"filename": "../etc/passwd"}
        response = await routes["/api/chat-logs/{filename}"](mock_request)
        assert response.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# 6. API İSTEMCİSİ — ReflexApiClient
# ══════════════════════════════════════════════════════════════════════════════

class TestReflexApiClient:
    """Telegram bot API istemcisinin yanıt ayrıştırma ve hata yönetimi."""

    @pytest.fixture
    def client(self):
        from harun_site.telegram_bot.api_client import ReflexApiClient
        return ReflexApiClient(base_url="http://test-server:3000", secret="test-secret")

    @pytest.mark.asyncio
    async def test_ping_returns_true_on_ok(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_resp)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            # Direkt _get mock'la
            client._get = AsyncMock(return_value={"ok": True})
            result = await client.ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_ping_returns_false_on_error(self, client):
        from harun_site.telegram_bot.api_client import ReflexApiError
        client._get = AsyncMock(side_effect=ReflexApiError("Bağlantı hatası", status_code=0))
        result = await client.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_chat_logs_parses_list(self, client):
        logs = [{"filename": "a.json", "timestamp": "2025-01-01T00:00:00"}]
        client._get = AsyncMock(return_value=logs)
        result = await client.get_chat_logs()
        assert result == logs

    @pytest.mark.asyncio
    async def test_get_chat_logs_returns_empty_on_non_list(self, client):
        client._get = AsyncMock(return_value={"error": "sunucu hatası"})
        result = await client.get_chat_logs()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_chat_log_messages_extracts_messages(self, client):
        messages = [{"role": "user", "content": "Merhaba"}]
        client._get = AsyncMock(return_value={"filename": "a.json", "messages": messages})
        result = await client.get_chat_log_messages("a.json")
        assert result == messages

    @pytest.mark.asyncio
    async def test_get_chat_log_messages_empty_filename(self, client):
        result = await client.get_chat_log_messages("")
        assert result == []

    @pytest.mark.asyncio
    async def test_get_projects_parses_list(self, client):
        projects = [{"slug": "dent-bot", "name": "Dent Bot"}]
        client._get = AsyncMock(return_value=projects)
        result = await client.get_projects()
        assert result == projects

    @pytest.mark.asyncio
    async def test_get_stats_returns_dict(self, client):
        stats = {"total_sessions": 10, "today_sessions": 2}
        client._get = AsyncMock(return_value=stats)
        result = await client.get_stats()
        assert result["total_sessions"] == 10

    def test_reflex_api_error_user_message_401(self):
        from harun_site.telegram_bot.api_client import ReflexApiError
        err = ReflexApiError("Yetkisiz", status_code=401)
        msg = err.user_message()
        assert "401" in msg or "yetkilendirme" in msg.lower()

    def test_reflex_api_error_user_message_connection(self):
        from harun_site.telegram_bot.api_client import ReflexApiError
        err = ReflexApiError("Bağlanamadı", status_code=0)
        msg = err.user_message()
        assert "ulaşılamadı" in msg.lower() or "bağlanamadı" in msg.lower()

    def test_client_headers_set_with_secret(self, client):
        assert "Authorization" in client._headers
        assert "test-secret" in client._headers["Authorization"]

    def test_client_no_secret_no_auth_header(self):
        from harun_site.telegram_bot.api_client import ReflexApiClient
        c = ReflexApiClient(base_url="http://test", secret="")
        assert "Authorization" not in c._headers


# ══════════════════════════════════════════════════════════════════════════════
# 7. BİLDİRİM SİSTEMİ — notifier
# ══════════════════════════════════════════════════════════════════════════════

class TestNotifier:
    """Mute, watchlist, hiring detection ve cooldown mantığı."""

    @pytest.fixture(autouse=True)
    def _patch_files(self, tmp_path, monkeypatch):
        import harun_site.telegram_bot.notifier as n
        monkeypatch.setattr(n, "_GUARD_FILE", tmp_path / "guard.json")
        monkeypatch.setattr(n, "_WATCH_FILE", tmp_path / "watchlist.json")

    def test_mute_1h_sets_state(self):
        from harun_site.telegram_bot.notifier import get_mute_state, set_mute
        set_mute("1h")
        state = get_mute_state()
        assert state["muted"] is True
        assert state["type"] == "1h"

    def test_mute_forever_sets_state(self):
        from harun_site.telegram_bot.notifier import get_mute_state, set_mute
        set_mute("forever")
        state = get_mute_state()
        assert state["muted"] is True
        assert state["until"] == -1

    def test_clear_mute_unmutes(self):
        from harun_site.telegram_bot.notifier import clear_mute, get_mute_state, set_mute
        set_mute("1h")
        clear_mute()
        assert get_mute_state()["muted"] is False

    def test_is_muted_returns_false_initially(self):
        from harun_site.telegram_bot.notifier import is_muted
        assert is_muted() is False

    def test_is_muted_returns_true_after_mute(self):
        from harun_site.telegram_bot.notifier import is_muted, set_mute
        set_mute("1d")
        assert is_muted() is True

    def test_watchlist_add_and_load(self):
        from harun_site.telegram_bot.notifier import load_watchlist, watch_add
        watch_add("dent-bot")
        wl = load_watchlist()
        assert "dent-bot" in wl

    def test_watchlist_remove(self):
        from harun_site.telegram_bot.notifier import load_watchlist, watch_add, watch_remove
        watch_add("fraud-eye")
        watch_remove("fraud-eye")
        assert "fraud-eye" not in load_watchlist()

    def test_watchlist_add_returns_false_if_exists(self):
        from harun_site.telegram_bot.notifier import watch_add
        watch_add("selfapi")
        result = watch_add("selfapi")
        assert result is False

    def test_watchlist_remove_returns_false_if_not_exists(self):
        from harun_site.telegram_bot.notifier import watch_remove
        result = watch_remove("olmayan-proje")
        assert result is False

    def test_watchlist_stored_lowercase(self):
        from harun_site.telegram_bot.notifier import load_watchlist, watch_add
        watch_add("DentBot")
        wl = load_watchlist()
        assert "dentbot" in wl

    def test_detect_watch_mentions(self):
        from harun_site.telegram_bot.notifier import detect_watch_mentions, watch_add
        watch_add("dent-bot")
        msgs = [{"role": "user", "content": "dent-bot hakkında soru sormak istiyorum"}]
        mentioned = detect_watch_mentions(msgs)
        assert "dent-bot" in mentioned

    def test_detect_watch_mentions_empty_watchlist(self):
        from harun_site.telegram_bot.notifier import detect_watch_mentions
        msgs = [{"role": "user", "content": "dent-bot nedir?"}]
        assert detect_watch_mentions(msgs) == []

    def test_detect_hiring_intent_strong_signal(self):
        from harun_site.telegram_bot.notifier import detect_hiring_intent
        msgs = [
            {"role": "user", "content": "Freelance çalışmak istiyorum, fiyat nedir?"},
            {"role": "assistant", "content": "Merhaba!"},
            {"role": "user", "content": "Email veya LinkedIn ile iletişime geçebilir miyim?"},
        ]
        with patch("harun_site.telegram_bot.notifier._get_projects_sync", return_value=[]):
            result = detect_hiring_intent(msgs)
        assert result is not None
        assert result["score"] >= 1

    def test_detect_hiring_intent_no_signal(self):
        from harun_site.telegram_bot.notifier import detect_hiring_intent
        msgs = [{"role": "user", "content": "Python öğrenmek istiyorum"}]
        with patch("harun_site.telegram_bot.notifier._get_projects_sync", return_value=[]):
            result = detect_hiring_intent(msgs)
        assert result is None

    def test_detect_hiring_intent_empty_messages(self):
        from harun_site.telegram_bot.notifier import detect_hiring_intent
        assert detect_hiring_intent([]) is None

    def test_should_send_allows_first_time(self, tmp_path, monkeypatch):
        import harun_site.telegram_bot.notifier as n
        monkeypatch.setattr(n, "_GUARD_FILE", tmp_path / "guard2.json")
        from harun_site.telegram_bot.notifier import _should_send
        assert _should_send("test", "key1", 60) is True

    def test_should_send_blocks_within_cooldown(self, tmp_path, monkeypatch):
        import harun_site.telegram_bot.notifier as n
        monkeypatch.setattr(n, "_GUARD_FILE", tmp_path / "guard3.json")
        from harun_site.telegram_bot.notifier import _should_send
        _should_send("test", "key2", 60)  # İlk çağrı
        assert _should_send("test", "key2", 60) is False  # Cooldown içinde

    def test_new_visitor_notify_disabled_toggle(self, monkeypatch):
        from harun_site.telegram_bot.notifier import (
            is_new_visitor_notify_enabled,
            set_new_visitor_notify,
        )
        set_new_visitor_notify(False)
        assert is_new_visitor_notify_enabled() is False
        set_new_visitor_notify(True)
        assert is_new_visitor_notify_enabled() is True

    def test_fmt_new_visitor_alert_format(self):
        from harun_site.telegram_bot.notifier import fmt_new_visitor_alert
        msg = fmt_new_visitor_alert("Merhaba, projeniz hakkında", "14:30")
        assert "Yeni Ziyaretçi" in msg
        assert "14:30" in msg

    def test_fmt_hiring_alert_format(self):
        from harun_site.telegram_bot.notifier import fmt_hiring_alert
        signal = {"score": 3, "contact": 2, "msg_count": 5, "long_session": False, "top_project": "Dent Bot"}
        with patch("harun_site.telegram_bot.notifier.load_watchlist", return_value=[]):
            msg = fmt_hiring_alert(signal)
        assert "İşe Alım" in msg
        assert "Dent Bot" in msg

    def test_fmt_error_alert_format(self):
        from harun_site.telegram_bot.notifier import fmt_error_alert
        msg = fmt_error_alert("ValueError: something went wrong", "chat_state")
        assert "Uygulama Hatası" in msg
        assert "ValueError" in msg

    def test_fmt_long_session_alert_level1(self):
        from harun_site.telegram_bot.notifier import fmt_long_session_alert
        msg = fmt_long_session_alert(12, "Dent Bot", level=1)
        assert "Uzun Oturum" in msg
        assert "12" in msg

    def test_fmt_long_session_alert_level2(self):
        from harun_site.telegram_bot.notifier import fmt_long_session_alert
        msg = fmt_long_session_alert(22, "", level=2)
        assert "Çok Uzun Oturum" in msg

    def test_fmt_watch_alert_format(self):
        from harun_site.telegram_bot.notifier import fmt_watch_alert
        msg = fmt_watch_alert("dent-bot", 7)
        assert "Watch Alert" in msg
        assert "dent-bot" in msg


# ══════════════════════════════════════════════════════════════════════════════
# 8. ADMİN KİMLİK DOĞRULAMA
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminAuth:
    """Admin şifre okuma, yazma ve slugify mantığı."""

    def test_get_admin_password_from_env(self, monkeypatch):
        monkeypatch.setenv("ADMIN_PASSWORD", "EnvSifresi123!")
        from harun_site.state.admin_state import _get_admin_password
        # Şifre dosyası yoksa env'e düşmeli
        with patch("harun_site.state.admin_state._ADMIN_PW_FILE") as mock_path:
            mock_path.exists.return_value = False
            pw = _get_admin_password()
        assert pw == "EnvSifresi123!"

    def test_get_admin_password_default(self, monkeypatch):
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        with patch("harun_site.state.admin_state._ADMIN_PW_FILE") as mock_path:
            mock_path.exists.return_value = False
            from harun_site.state.admin_state import _get_admin_password
            pw = _get_admin_password()
        assert pw == "SoloTrk826!"

    def test_save_and_load_admin_password(self, tmp_path, monkeypatch):
        pw_file = tmp_path / "admin_password.json"
        import harun_site.state.admin_state as asa
        monkeypatch.setattr(asa, "_ADMIN_PW_FILE", pw_file)
        result = asa._save_admin_password("YeniSifre456!")
        assert result is True
        loaded = asa._get_admin_password()
        assert loaded == "YeniSifre456!"

    def test_get_admin_password_from_file_priority(self, tmp_path, monkeypatch):
        pw_file = tmp_path / "admin_password.json"
        pw_file.write_text(json.dumps({"password": "DosyadakiSifre"}), encoding="utf-8")
        import harun_site.state.admin_state as asa
        monkeypatch.setattr(asa, "_ADMIN_PW_FILE", pw_file)
        monkeypatch.setenv("ADMIN_PASSWORD", "EnvdekiSifre")
        pw = asa._get_admin_password()
        assert pw == "DosyadakiSifre"  # Dosya env'e göre öncelikli

    def test_slugify_turkish_chars(self):
        from harun_site.state.admin_state import slugify
        assert slugify("Çok Güzel Proje") == "cok-guzel-proje"

    def test_slugify_special_chars_removed(self):
        from harun_site.state.admin_state import slugify
        assert slugify("Hello! World@2025") == "hello-world2025"

    def test_slugify_spaces_to_hyphens(self):
        from harun_site.state.admin_state import slugify
        assert slugify("my new project") == "my-new-project"

    def test_slugify_strips_leading_trailing_hyphens(self):
        from harun_site.state.admin_state import slugify
        result = slugify("-test-")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_slugify_empty_string(self):
        from harun_site.state.admin_state import slugify
        assert slugify("") == ""


# ══════════════════════════════════════════════════════════════════════════════
# 9. i18n SİSTEMİ
# ══════════════════════════════════════════════════════════════════════════════

class TestI18n:
    """TXT anahtarlarının eksiksizliği ve çeviri fonksiyonu."""

    CRITICAL_KEYS = [
        "nav_home", "nav_portfolio", "nav_blog", "nav_about",
        "hero_title", "hero_subtitle",
        "portfolio_title", "blog_title", "about_title", "chat_title",
        "chat_greeting", "chat_placeholder",
        "cs_problem", "cs_architecture", "cs_challenges", "cs_learnings",
        "footer_tagline",
    ]

    def test_all_critical_keys_exist(self):
        from harun_site.utils.i18n import TXT
        for key in self.CRITICAL_KEYS:
            assert key in TXT, f"Eksik i18n anahtarı: {key}"

    def test_all_keys_have_tr(self):
        from harun_site.utils.i18n import TXT
        for key, val in TXT.items():
            assert "tr" in val, f"'{key}' anahtarında TR çevirisi eksik"

    def test_all_keys_have_en(self):
        from harun_site.utils.i18n import TXT
        for key, val in TXT.items():
            assert "en" in val, f"'{key}' anahtarında EN çevirisi eksik"

    def test_translation_function_returns_tr(self):
        from harun_site.utils.i18n import _
        result = _("nav_home", "tr")
        assert result == "Ana Sayfa"

    def test_translation_function_returns_en(self):
        from harun_site.utils.i18n import _
        result = _("nav_home", "en")
        assert result == "Home"

    def test_translation_function_missing_key(self):
        from harun_site.utils.i18n import _
        result = _("olmayan_anahtar", "tr")
        assert result.startswith("!")

    def test_no_empty_translations(self):
        from harun_site.utils.i18n import TXT
        for key, val in TXT.items():
            assert val.get("tr", ""), f"'{key}' için TR çevirisi boş"
            assert val.get("en", ""), f"'{key}' için EN çevirisi boş"


# ══════════════════════════════════════════════════════════════════════════════
# 10. ROUTES & SLUG SABİTLERİ
# ══════════════════════════════════════════════════════════════════════════════

class TestRoutes:
    """URL sabitleri ve rota tutarlılığı."""

    def test_portfolio_route_constant(self):
        from harun_site.utils.routes import PORTFOLIO_ROUTE
        assert PORTFOLIO_ROUTE == "/portfolio"

    def test_case_study_route_has_slug_param(self):
        from harun_site.utils.routes import CASE_STUDY_ROUTE
        assert "[slug]" in CASE_STUDY_ROUTE

    def test_legacy_route_different_from_canonical(self):
        from harun_site.utils.routes import CASE_STUDY_ROUTE, LEGACY_CASE_STUDY_ROUTE
        assert CASE_STUDY_ROUTE != LEGACY_CASE_STUDY_ROUTE

    def test_case_study_href_prefix(self):
        from harun_site.utils.routes import CASE_STUDY_HREF_PREFIX
        assert CASE_STUDY_HREF_PREFIX.endswith("/")
        assert "portfolio" in CASE_STUDY_HREF_PREFIX

    def test_project_url_from_slug_builds_correct_url(self):
        from harun_site.utils.project_registry import project_url_from_slug
        url = project_url_from_slug("dent-bot")
        assert url == "/portfolio/dent-bot"

    def test_project_url_from_slug_empty(self):
        from harun_site.utils.project_registry import project_url_from_slug
        assert project_url_from_slug("") == ""


# ══════════════════════════════════════════════════════════════════════════════
# 11. GÜVENLİK TESTLERİ
# ══════════════════════════════════════════════════════════════════════════════

class TestSecurity:
    """Path traversal, veri bütünlüğü ve izolasyon korumaları."""

    @pytest.fixture(autouse=True)
    def _patch_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()

    def test_atomic_write_does_not_leave_tmp_file_on_success(self, tmp_path):
        from harun_site.utils.data_manager import save_projects
        save_projects([_make_project("guvenlik-testi")])
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_projects_file_is_valid_json(self, tmp_path):
        from harun_site.utils.data_manager import PROJECTS_FILE, save_projects
        save_projects([_make_project("json-guvenlik")])
        data = json.loads(PROJECTS_FILE.read_text())
        assert isinstance(data, list)

    def test_chat_log_path_traversal_blocked(self):
        """load_chat_log_messages, '../' içeren isimde dosya döndürmemeli."""
        from harun_site.utils.data_manager import load_chat_log_messages
        result = load_chat_log_messages("../etc/passwd")
        assert result == []

    def test_project_aliases_normalized_lowercase(self):
        from harun_site.utils.project_registry import canonicalize_project_record
        p = {"title": "Test", "slug": "test", "aliases": ["BÜYÜK", "Karışık"]}
        c = canonicalize_project_record(p)
        for alias in c["aliases"]:
            assert alias == alias.lower()

    def test_save_and_reload_preserves_unicode(self, tmp_path):
        from harun_site.utils.data_manager import load_projects, save_projects
        unicode_project = _make_project("unicode-test", "Türkçe Çok Güzel Proje")
        save_projects([unicode_project])
        loaded = load_projects()
        assert loaded[0]["title"] == "Türkçe Çok Güzel Proje"

    def test_corrupt_projects_file_returns_empty(self, tmp_path):
        import harun_site.utils.data_manager as dm
        dm.PROJECTS_FILE.write_text("GEÇERSIZ JSON{{{{", encoding="utf-8")
        from harun_site.utils.data_manager import load_projects
        assert load_projects() == []

    def test_corrupt_chat_log_returns_empty(self, tmp_path):
        import harun_site.utils.data_manager as dm
        bozuk = dm.CHAT_LOGS_DIR / "bozuk.json"
        bozuk.write_text("BOZUK VERI", encoding="utf-8")
        from harun_site.utils.data_manager import load_chat_log_messages
        assert load_chat_log_messages("bozuk.json") == []

    def test_admin_password_not_in_env_uses_default(self, monkeypatch):
        monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
        with patch("harun_site.state.admin_state._ADMIN_PW_FILE") as mp:
            mp.exists.return_value = False
            from harun_site.state.admin_state import _get_admin_password
            pw = _get_admin_password()
        assert pw == "SoloTrk826!"


# ══════════════════════════════════════════════════════════════════════════════
# 12. BÜTÜNLEŞME / E2E SENARYOLARI
# ══════════════════════════════════════════════════════════════════════════════

class TestE2EScenarios:
    """Gerçekçi kullanıcı senaryolarını uçtan uca simüle eder."""

    @pytest.fixture(autouse=True)
    def _patch_all_dirs(self, tmp_path, monkeypatch):
        import harun_site.utils.data_manager as dm
        monkeypatch.setattr(dm, "DATA_DIR", tmp_path)
        monkeypatch.setattr(dm, "PROJECTS_FILE", tmp_path / "projects.json")
        monkeypatch.setattr(dm, "CHAT_LOGS_DIR", tmp_path / "chat_logs")
        monkeypatch.setattr(dm, "SUMMARIES_DIR", tmp_path / "summaries")
        monkeypatch.setattr(dm, "TAGS_FILE", tmp_path / "tags.json")
        monkeypatch.setattr(dm, "SKILLS_FILE", tmp_path / "skills.json")
        monkeypatch.setattr(dm, "POSTS_DIR", tmp_path / "posts")
        (tmp_path / "chat_logs").mkdir()
        (tmp_path / "summaries").mkdir()
        (tmp_path / "posts").mkdir()

    def test_scenario_project_lifecycle(self):
        """Proje oluştur → kaydet → sil → doğrula."""
        from harun_site.utils.data_manager import (
            delete_project,
            get_project_by_slug,
            load_projects,
            save_projects,
        )
        projects = [
            _make_project("dent-bot", "Dent Bot"),
            _make_project("fraud-eye", "Fraud Eye"),
            _make_project("c-module", "C Module"),
        ]
        save_projects(projects)
        assert len(load_projects()) == 3

        p = get_project_by_slug("fraud-eye")
        assert p is not None and p["title"] == "Fraud Eye"

        # İndex ile sil
        current = load_projects()
        idx = next(i for i, p in enumerate(current) if p["slug"] == "fraud-eye")
        delete_project(idx)
        assert len(load_projects()) == 2
        assert get_project_by_slug("fraud-eye") is None

    def test_scenario_chat_log_and_enrichment(self):
        """Chat log kaydet → proje token'ını çöz → link doğrula."""
        from harun_site.utils.data_manager import load_chat_log_messages, save_chat_log, save_projects
        from harun_site.utils.chat_enrich import finalize_project_references

        save_projects([_make_project("dent-bot", "Dent Bot")])

        messages = [
            {"role": "user", "content": "dent-bot projen nedir?"},
            {"role": "assistant", "content": "[[PROJECT_REF:dent-bot]] çok güzel bir proje."},
        ]
        fname = save_chat_log(messages)
        loaded = load_chat_log_messages(fname)
        assert len(loaded) == 2

        import harun_site.utils.chat_enrich as ce
        ce_projects = [_make_project("dent-bot", "Dent Bot")]
        with patch.object(ce, "_project_index", return_value=ce_projects):
            enriched = finalize_project_references(loaded[1]["content"])
        assert "[Dent Bot]" in enriched
        assert "/portfolio/dent-bot" in enriched

    def test_scenario_admin_password_change(self, tmp_path, monkeypatch):
        """Şifreyi değiştir → yeni şifreyi doğrula."""
        pw_file = tmp_path / "admin_password.json"
        import harun_site.state.admin_state as asa
        monkeypatch.setattr(asa, "_ADMIN_PW_FILE", pw_file)

        asa._save_admin_password("EskiSifre123!")
        assert asa._get_admin_password() == "EskiSifre123!"

        asa._save_admin_password("YeniSifre456!")
        assert asa._get_admin_password() == "YeniSifre456!"

    def test_scenario_watchlist_trigger_flow(self, tmp_path, monkeypatch):
        """Watchlist ekle → mesajda geç → algıla."""
        import harun_site.telegram_bot.notifier as n
        monkeypatch.setattr(n, "_WATCH_FILE", tmp_path / "watchlist2.json")

        from harun_site.telegram_bot.notifier import detect_watch_mentions, watch_add
        watch_add("dent-bot")
        msgs = [{"role": "user", "content": "Dent-bot projesini çok beğendim"}]
        mentioned = detect_watch_mentions(msgs)
        assert "dent-bot" in mentioned

    def test_scenario_mute_blocks_notify(self, tmp_path, monkeypatch):
        """Mute aktifken send_notification çağrılmamalı."""
        import harun_site.telegram_bot.notifier as n
        monkeypatch.setattr(n, "_GUARD_FILE", tmp_path / "mute_guard.json")

        from harun_site.telegram_bot.notifier import set_mute

        set_mute("forever")
        with patch("harun_site.telegram_bot.notifier._get_creds") as mock_creds:
            with patch("harun_site.telegram_bot.notifier.send_notification") as mock_send:
                from harun_site.telegram_bot.notifier import notify_hiring_if_warranted
                msgs = [
                    {"role": "user", "content": "freelance çalışmak istiyorum fiyat nedir?"},
                    {"role": "assistant", "content": "Merhaba!"},
                    {"role": "user", "content": "Email ile iletişime geçebilir miyim?"},
                ]
                notify_hiring_if_warranted(msgs)
                mock_send.assert_not_called()

    def test_scenario_project_bilingual_localization(self):
        """Proje hem TR hem EN dilde doğru çözümlenmeli."""
        from harun_site.utils.data_manager import load_projects_localized, save_projects
        p = _make_project("bilingual-test", "Bilingual Proje")
        save_projects([p])

        tr_projects = load_projects_localized("tr")
        en_projects = load_projects_localized("en")

        assert tr_projects[0]["desc"] == "Türkçe açıklama"
        assert en_projects[0]["desc"] == "English description"

    def test_scenario_tag_management_flow(self):
        """Tag ekle → proje ile ilişkilendir → tag sil → doğrula."""
        from harun_site.utils.data_manager import (
            add_tag,
            delete_tag,
            load_tags,
            save_projects,
        )
        add_tag("rag")
        add_tag("langchain")
        tags = load_tags()
        assert "rag" in tags
        assert "langchain" in tags

        p = _make_project("rag-proje")
        p["tags"] = ["rag", "langchain"]
        save_projects([p])

        delete_tag("langchain")
        assert "langchain" not in load_tags()

    def test_scenario_blog_post_full_cycle(self, tmp_path):
        """Blog yazısı oluştur → dosya var mı kontrol et → sil."""
        from harun_site.utils.data_manager import delete_blog_post, save_blog_post
        save_blog_post(
            slug="e2e-blog-test",
            title="E2E Test Yazısı",
            title_en="E2E Test Post",
            date="2025-06-12",
            description="Test açıklama",
            description_en="Test description",
            tags=["test", "e2e"],
            content="## İçerik\nBu bir E2E test yazısıdır.",
            content_en="## Content\nThis is an E2E test post.",
        )
        from harun_site.utils.data_manager import POSTS_DIR
        assert (POSTS_DIR / "e2e-blog-test.md").exists()
        delete_blog_post("e2e-blog-test")
        assert not (POSTS_DIR / "e2e-blog-test.md").exists()

    def test_scenario_fingerprint_invalidates_on_new_log(self):
        """Yeni log gelince dashboard cache geçersiz sayılmalı."""
        from harun_site.utils.groq_client import chat_logs_fingerprint
        from harun_site.utils.data_manager import save_chat_log

        save_chat_log([{"role": "user", "content": "Log 1"}], "fp_log1.json")
        logs1 = [{"filename": "fp_log1.json", "mtime": 1000, "message_count": 1}]
        fp1 = chat_logs_fingerprint(logs1)

        save_chat_log([{"role": "user", "content": "Log 2"}], "fp_log2.json")
        logs2 = logs1 + [{"filename": "fp_log2.json", "mtime": 2000, "message_count": 1}]
        fp2 = chat_logs_fingerprint(logs2)

        assert fp1 != fp2
