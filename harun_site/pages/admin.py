import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.state.admin_state import AdminAuthState, AdminBlogState, AdminProjectState, AdminChatLogState, AdminChatAssistantState, AdminSuggestionsState, AdminCVState, AdminState, AdminCareerState, AdminEduExpState, AdminSkillsState
from harun_site.theme import BG, BG_CARD, PRIMARY, TEXT, TEXT_MUTED, BORDER, ACCENT, FONT_SANS, FONT_MONO, GLOW_PRIMARY

def login_form() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.heading("Admin Login", size="6", color=PRIMARY, font_family=FONT_MONO),
            rx.cond(
                AdminAuthState.login_error != "",
                rx.text(AdminAuthState.login_error, color=ACCENT, font_size="0.9em"),
                rx.fragment()
            ),
            rx.input(
                placeholder="Şifre...",
                type="password",
                value=AdminAuthState.password,
                on_change=AdminAuthState.set_password,
                width="100%",
                background=BG_CARD,
                border=f"1px solid {BORDER}",
                color=TEXT,
            ),
            rx.button(
                "Giriş Yap",
                on_click=AdminAuthState.login,
                width="100%",
                background=PRIMARY,
                color=BG,
                font_weight="bold",
                _hover={"opacity": 0.8}
            ),
            padding="2em",
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="12px",
            width="100%",
            max_width="400px",
            spacing="4"
        ),
        height="100vh",
        width="100%"
    )

def tag_checkbox_grid(state_class) -> rx.Component:
    return rx.vstack(
        rx.text("Etiketler", font_size="0.9em", color=TEXT_MUTED),
        rx.flex(
            rx.foreach(
                state_class.available_tags,
                lambda tag: rx.box(
                    rx.hstack(
                        rx.cond(
                            state_class.selected_tags.contains(tag),
                            rx.text("✓", color=PRIMARY, font_family=FONT_MONO, font_size="0.8em"),
                            rx.text("○", color=TEXT_MUTED, font_family=FONT_MONO, font_size="0.8em"),
                        ),
                        rx.text(tag, font_family=FONT_MONO, font_size="0.8em", color=TEXT),
                        rx.button(
                            "Sil",
                            on_click=state_class.delete_tag(tag),
                            background="transparent",
                            color=ACCENT,
                            border=f"1px solid {ACCENT}44",
                            size="1",
                            font_family=FONT_MONO,
                            font_size="0.7em",
                            padding="0.2em 0.45em",
                            _hover={"background": f"{ACCENT}12", "border_color": ACCENT},
                        ),
                        gap="0.4em", align="center",
                    ),
                    padding="0.3em 0.8em",
                    border=rx.cond(state_class.selected_tags.contains(tag), f"1px solid {PRIMARY}", f"1px solid {BORDER}"),
                    border_radius="4px",
                    background=rx.cond(state_class.selected_tags.contains(tag), f"{PRIMARY}15", BG_CARD),
                    cursor="pointer",
                    on_click=lambda: state_class.toggle_tag(tag),
                    transition="all 150ms",
                )
            ),
            wrap="wrap",
            spacing="2",
            width="100%"
        ),
        rx.hstack(
            rx.input(
                placeholder="Yeni etiket...",
                value=state_class.new_tag_name,
                on_change=state_class.set_new_tag_name,
                background=BG,
                size="1"
            ),
            rx.button("Ekle", on_click=state_class.add_new_tag, size="1", background=PRIMARY, color=BG),
            spacing="2",
            margin_top="0.5em"
        ),
        width="100%",
        align_items="start",
        spacing="2"
    )

def blog_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Yeni Blog Yazısı", size="4", color=TEXT),
        rx.hstack(
            rx.input(placeholder="Başlık (örn: Merhaba Dünya)", value=AdminBlogState.blog_title, on_change=AdminBlogState.set_blog_title, width="100%", background=BG),
            rx.input(placeholder="Slug (örn: merhaba-dunya)", value=AdminBlogState.blog_slug, on_change=AdminBlogState.set_blog_slug, width="100%", background=BG),
            width="100%",
            spacing="4"
        ),
        rx.hstack(
            rx.input(placeholder="Tarih (YYYY-MM-DD)", value=AdminBlogState.blog_date, on_change=AdminBlogState.set_blog_date, width="100%", background=BG),
            width="100%",
        ),
        tag_checkbox_grid(AdminBlogState),
        rx.text_area(placeholder="Kısa Açıklama", value=AdminBlogState.blog_description, on_change=AdminBlogState.set_blog_description, width="100%", background=BG),

        rx.vstack(
            rx.text("Kapak Görseli Yükle", font_size="0.9em", color=TEXT_MUTED),
            rx.upload(
                rx.vstack(
                    rx.button("Görsel Seç", background=BG, border=f"1px solid {BORDER}", color=TEXT),
                    rx.text("Sürükle bırak veya tıkla", font_size="0.8em", color=TEXT_MUTED)
                ),
                id="blog_cover_upload",
                border=f"1px dashed {BORDER}",
                padding="2em",
                border_radius="8px",
                width="100%",
            ),
            rx.hstack(
                rx.button("Yükle", on_click=AdminBlogState.handle_upload(rx.upload_files(upload_id="blog_cover_upload")), background=PRIMARY, color=BG),
                rx.cond(
                    AdminBlogState.is_uploading,
                    rx.text("Yükleniyor...", color=PRIMARY),
                    rx.cond(
                        AdminBlogState.blog_cover_path != "",
                        rx.text(f"Yüklendi: {AdminBlogState.blog_cover_path}", color=PRIMARY),
                        rx.fragment()
                    )
                )
            ),
            width="100%",
            align_items="start"
        ),

        rx.text_area(placeholder="Markdown İçerik...", value=AdminBlogState.blog_content, on_change=AdminBlogState.set_blog_content, width="100%", height="300px", background=BG),
        rx.button("Yazıyı Kaydet", on_click=AdminBlogState.save_post, background=PRIMARY, color=BG, width="100%"),

        rx.divider(margin_y="2em", border_color=BORDER),

        rx.heading("Mevcut Yazılar", size="4", color=TEXT),
        rx.vstack(
                rx.foreach(
                AdminBlogState.all_admin_posts,
                lambda post: rx.hstack(
                    rx.text(post["title"], color=TEXT, flex="1"),
                    rx.text(post["date"], color=TEXT_MUTED, font_size="0.8em"),
                    rx.button("Düzenle", on_click=AdminBlogState.start_edit_post(post["slug"]), background=PRIMARY, color=BG, size="1"),
                    rx.button("Sil", on_click=AdminBlogState.delete_post(post["slug"]), background=ACCENT, color=BG, size="1"),
                    width="100%",
                    padding="1em",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    background=BG,
                    align_items="center"
                )
            ),
            width="100%",
            spacing="2"
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px"
    )

def project_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Yeni Proje Ekle", size="4", color=TEXT),
        rx.input(placeholder="Proje Başlığı", value=AdminProjectState.project_name, on_change=AdminProjectState.set_project_name, width="100%", background=BG),
        rx.input(placeholder="Slug (örn: cebirx)", value=AdminProjectState.project_slug, on_change=AdminProjectState.set_project_slug, width="100%", background=BG),
        rx.input(placeholder="Aliaslar (virgülle, opsiyonel)", value=AdminProjectState.project_aliases_str, on_change=AdminProjectState.set_project_aliases_str, width="100%", background=BG),
        tag_checkbox_grid(AdminProjectState),
        rx.text_area(placeholder="Açıklama", value=AdminProjectState.project_desc, on_change=AdminProjectState.set_project_desc, width="100%", background=BG),
        rx.text_area(placeholder="Problem (markdown destekli)", value=AdminProjectState.cs_problem, on_change=AdminProjectState.set_cs_problem, width="100%", height="120px", background=BG),
        rx.text_area(placeholder="Mimari (markdown destekli)", value=AdminProjectState.cs_architecture, on_change=AdminProjectState.set_cs_architecture, width="100%", height="120px", background=BG),
        rx.input(placeholder="Architecture Image (path veya url)", value=AdminProjectState.architecture_image, on_change=AdminProjectState.set_architecture_image, width="100%", background=BG),
        rx.text_area(placeholder="Why This Stack? (markdown destekli)", value=AdminProjectState.cs_stack_reason, on_change=AdminProjectState.set_cs_stack_reason, width="100%", height="100px", background=BG),
        rx.text_area(placeholder="Challenges (markdown destekli)", value=AdminProjectState.cs_challenges, on_change=AdminProjectState.set_cs_challenges, width="100%", height="100px", background=BG),
        rx.text_area(placeholder="Lessons Learned (markdown destekli)", value=AdminProjectState.cs_learnings, on_change=AdminProjectState.set_cs_learnings, width="100%", height="100px", background=BG),
        rx.button("Projeyi Kaydet", on_click=AdminProjectState.save_project, background=PRIMARY, color=BG, width="100%"),

        rx.divider(margin_y="2em", border_color=BORDER),

        rx.heading("Mevcut Projeler", size="4", color=TEXT),
        rx.vstack(
                rx.foreach(
                AdminProjectState.all_admin_projects,
                lambda proj, index: rx.hstack(
                    rx.text(proj["title"], color=TEXT, flex="1"),
                    rx.button("Düzenle", on_click=AdminProjectState.start_edit_project(index), background=PRIMARY, color=BG, size="1"),
                    rx.button("Sil", on_click=AdminProjectState.delete_project(index), background=ACCENT, color=BG, size="1"),
                    width="100%",
                    padding="1em",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    background=BG,
                    align_items="center"
                )
            ),
            width="100%",
            spacing="2"
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px"
    )

def chat_log_tab() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.heading("Sohbet Özetleri", size="4", color=TEXT),
                rx.spacer(),
                rx.button(
                    "Tüm Geçmişi Temizle",
                    on_click=AdminChatLogState.clear_all_logs,
                    background="transparent",
                    border=f"1px solid {ACCENT}",
                    color=ACCENT,
                    size="1",
                    _hover={"background": f"{ACCENT}15"},
                    font_family=FONT_MONO,
                    font_size="0.75em",
                ),
                width="100%",
                align_items="center",
                margin_bottom="1em"
            ),
            rx.foreach(
                AdminChatLogState.chat_logs,
                lambda log: rx.vstack(
                    rx.hstack(
                        rx.vstack(
                            rx.text(log["date"], color=TEXT, font_size="0.8em", font_family=FONT_MONO),
                            rx.text(
                                log["filename"],
                                color=TEXT_MUTED,
                                font_size="0.68em",
                                font_family=FONT_MONO,
                            ),
                            align_items="start",
                            spacing="0",
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.text(f"{log['message_count']} mesaj", color=TEXT_MUTED, font_size="0.75em"),
                            rx.button(
                                "Aç",
                                on_click=lambda: AdminChatLogState.view_log(log["filename"]),
                                background=PRIMARY,
                                color=BG,
                                size="1",
                            ),
                            rx.link(
                                rx.button("Tam ekran", background="transparent", color=PRIMARY, border=f"1px solid {PRIMARY}", size="1"),
                                href=f"/chat?c={log['filename']}"
                            ),
                            rx.button(
                                rx.icon("trash-2", size=14),
                                on_click=lambda: AdminChatLogState.delete_log(log["filename"]),
                                background="transparent",
                                color=ACCENT,
                                _hover={"color": "red"},
                                padding="0"
                            ),
                            spacing="2",
                            align="center",
                        ),
                        width="100%",
                        align_items="center"
                    ),
                    rx.flex(
                        rx.foreach(
                            log["top_topics"],
                            lambda topic: rx.text(
                                topic,
                                font_family=FONT_MONO,
                                font_size="0.7em",
                                color=PRIMARY,
                                border=f"1px solid {BORDER}",
                                padding="0.1em 0.4em",
                                border_radius="3px"
                            )
                        ),
                        wrap="wrap",
                        spacing="2",
                        width="100%"
                    ),
                    rx.text(
                        log["summary"],
                        color=TEXT_MUTED,
                        font_size="0.85em",
                        line_height="1.6",
                        text_align="left",
                        width="100%"
                    ),
                    width="100%",
                    padding="1.2em",
                    border=f"1px solid {BORDER}",
                    border_radius="12px",
                    background=BG,
                    spacing="3",
                    align_items="start"
                )
            ),
            width="100%",
            height="700px",
            overflow_y="auto",
            spacing="4"
        ),
        rx.vstack(
            rx.hstack(
                rx.heading("Seçili Sohbet", size="4", color=TEXT),
                rx.spacer(),
                rx.cond(
                    AdminChatLogState.selected_log_name != "",
                    rx.link(
                        rx.button("Tam ekranda aç", background=PRIMARY, color=BG, size="1"),
                        href=f"/chat?c={AdminChatLogState.selected_log_name}",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align_items="center",
            ),
            rx.cond(
                AdminChatLogState.selected_log_name != "",
                rx.vstack(
                    rx.text(AdminChatLogState.selected_log_name, color=TEXT_MUTED, font_family=FONT_MONO, font_size="0.75em"),
                    rx.foreach(
                        AdminChatLogState.selected_log,
                        lambda message: rx.box(
                            rx.text(
                                message["role"],
                                color=PRIMARY,
                                font_family=FONT_MONO,
                                font_size="0.7em",
                                margin_bottom="0.3em",
                            ),
                            rx.text(
                                message["content"],
                                color=TEXT,
                                font_size="0.85em",
                                line_height="1.6",
                            ),
                            width="100%",
                            padding="0.9em",
                            border=f"1px solid {BORDER}",
                            border_radius="10px",
                            background=BG,
                        ),
                    ),
                    width="100%",
                    spacing="3",
                    align_items="start",
                ),
                rx.text("Soldan bir kayıt açın.", color=TEXT_MUTED),
            ),
            width="100%",
            height="700px",
            overflow_y="auto",
            spacing="4",
            padding="1.2em",
            border=f"1px solid {BORDER}",
            border_radius="12px",
            background=BG_CARD,
        ),

        width="100%",
        spacing="4",
        align_items="start"
    )


def chat_suggestions_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Sohbet Önerileri", size="4", color=TEXT),
        rx.cond(
            AdminSuggestionsState.suggestions.length() >= 8,
            rx.text(
                "Maksimum 8 oneriniz olabilir. Yeni eklemek icin once bir oneriyi silin.",
                color=ACCENT,
                font_size="0.85em",
                font_family=FONT_MONO,
            ),
            rx.fragment(),
        ),
        rx.vstack(
            rx.foreach(
                AdminSuggestionsState.suggestions,
                lambda suggestion, index: rx.hstack(
                    rx.text(
                        suggestion,
                        color=TEXT,
                        font_size="0.9em",
                        flex="1",
                    ),
                    rx.button(
                        "Sil",
                        on_click=AdminSuggestionsState.delete_suggestion(index),
                        background="transparent",
                        border=f"1px solid {ACCENT}",
                        color=ACCENT,
                        size="1",
                    ),
                    width="100%",
                    padding="0.8em 1em",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    background=BG,
                    align_items="center",
                ),
            ),
            width="100%",
            spacing="2",
            align_items="start",
        ),
        rx.hstack(
            rx.input(
                placeholder="Yeni sohbet onerisi...",
                value=AdminSuggestionsState.new_suggestion,
                on_change=AdminSuggestionsState.set_new_suggestion,
                background=BG,
                width="100%",
            ),
            rx.button(
                "Ekle",
                on_click=AdminSuggestionsState.add_suggestion,
                background=PRIMARY,
                color=BG,
                is_disabled=AdminSuggestionsState.suggestions.length() >= 8,
            ),
            width="100%",
            spacing="3",
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px",
    )


def admin_chat_bubble(message: dict) -> rx.Component:
    # Guard: only render rx.markdown when content is a non-empty string.
    # AdminChatAssistantState.messages is list[ChatMessageDict] (TypedDict)
    # which gives Reflex type info, but an empty-string interim value
    # during streaming could still cause react-markdown to receive an object.
    return rx.cond(
        message["role"] == "user",
        rx.box(
            message["content"],
            align_self="flex-end",
            background_color=PRIMARY,
            color=BG,
            padding="0.55em 0.9em",
            border_radius="18px 18px 4px 18px",
            font_family=FONT_SANS,
            font_size="0.85em",
            max_width="85%",
        ),
        rx.box(
            rx.cond(
                message["content"] != "",
                rx.markdown(message["content"]),
                rx.text(
                    "●●●",
                    color=TEXT_MUTED,
                    font_family=FONT_MONO,
                    font_size="0.75em",
                    letter_spacing="0.15em",
                ),
            ),
            align_self="flex-start",
            background_color=BG,
            color=TEXT,
            padding="0.55em 0.9em",
            border_radius="18px 18px 18px 4px",
            font_family=FONT_SANS,
            font_size="0.85em",
            border=f"1px solid {BORDER}",
            max_width="85%",
        ),
    )


def _shortcut_btn(label: str, icon_name: str, on_click) -> rx.Component:
    """Compact shortcut pill button for the analytics assistant."""
    return rx.button(
        rx.hstack(
            rx.icon(icon_name, size=13, color=PRIMARY),
            rx.text(label, font_family=FONT_MONO, font_size="0.72em", color=PRIMARY),
            gap="0.3em",
            align="center",
        ),
        on_click=on_click,
        background="transparent",
        border=f"1px solid {PRIMARY}44",
        border_radius="20px",
        padding="0.3em 0.75em",
        cursor="pointer",
        _hover={"background": f"{PRIMARY}12", "border_color": PRIMARY},
        transition="all 150ms",
        disabled=AdminChatAssistantState.is_loading,
    )


def admin_chat_tab() -> rx.Component:
    return rx.vstack(
        # ── header ─────────────────────────────────────────────────
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("brain", color=PRIMARY, size=18),
                    rx.heading(
                        "Portfolio Intelligence",
                        size="4",
                        color=TEXT,
                        font_family=FONT_MONO,
                    ),
                    gap="0.5em",
                    align="center",
                ),
                rx.text(
                    AdminChatAssistantState.status_text,
                    color=TEXT_MUTED,
                    font_size="0.80em",
                    font_family=FONT_MONO,
                ),
                align_items="start",
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                "Sıfırla",
                on_click=AdminChatAssistantState.reset_chat,
                background="transparent",
                border=f"1px solid {ACCENT}55",
                color=ACCENT,
                font_family=FONT_MONO,
                font_size="0.78em",
                size="1",
                _hover={"border_color": ACCENT, "background": f"{ACCENT}12"},
            ),
            width="100%",
            align_items="start",
        ),
        # ── shortcut quick-queries ─────────────────────────────────
        rx.flex(
            _shortcut_btn(
                "Intent Dağılımı",
                "pie-chart",
                AdminChatAssistantState.shortcut_intent_distribution,
            ),
            _shortcut_btn(
                "En Çok İlgi Gören Proje",
                "star",
                AdminChatAssistantState.shortcut_top_project,
            ),
            _shortcut_btn(
                "Ziyaretçi Patternleri",
                "trending-up",
                AdminChatAssistantState.shortcut_visitor_patterns,
            ),
            gap="0.5em",
            wrap="wrap",
            width="100%",
        ),
        # ── messages area ─────────────────────────────────────────────
        rx.cond(
            AdminChatAssistantState.messages.length() == 0,
            # empty state placeholder
            rx.box(
                rx.vstack(
                    rx.icon("message-square-dashed", color=TEXT_MUTED, size=28),
                    rx.text(
                        "Ziyaretçi davranışı, proje ilgisi veya intent dağılımı hakkında soru sor.",
                        color=TEXT_MUTED,
                        font_family=FONT_MONO,
                        font_size="0.80em",
                        text_align="center",
                        max_width="340px",
                    ),
                    rx.text(
                        "Ya da yukardaki kısayollardan birini kullan.",
                        color=TEXT_MUTED,
                        font_family=FONT_MONO,
                        font_size="0.72em",
                        text_align="center",
                        opacity="0.6",
                    ),
                    gap="0.8em",
                    align="center",
                ),
                display="flex",
                align_items="center",
                justify_content="center",
                height="460px",
                width="100%",
                background=BG_CARD,
                border=f"1px solid {BORDER}",
                border_radius="12px",
            ),
            rx.box(
                rx.vstack(
                    rx.foreach(AdminChatAssistantState.messages, admin_chat_bubble),
                    rx.cond(
                        AdminChatAssistantState.is_loading,
                        rx.hstack(
                            rx.text(
                                "●●●",
                                color=TEXT_MUTED,
                                font_size="0.75em",
                                letter_spacing="0.15em",
                            ),
                            rx.text(
                                "analiz ediliyor",
                                color=TEXT_MUTED,
                                font_family=FONT_MONO,
                                font_size="0.72em",
                            ),
                            gap="0.4em",
                            align="center",
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                    align_items="stretch",
                ),
                # id watched by chat_scroll.js for streaming auto-scroll
                id="chat-messages-admin",
                height="460px",
                overflow_y="auto",
                width="100%",
                padding="1.2em",
                background=BG_CARD,
                border=f"1px solid {BORDER}",
                border_radius="12px",
            ),
        ),
        # ── input bar ────────────────────────────────────────────────
        rx.hstack(
            rx.input(
                placeholder="Ziyaretçi davranışı, proje ilgisi, intent analizi...",
                value=AdminChatAssistantState.input_value,
                on_change=AdminChatAssistantState.set_input_value,
                on_key_down=AdminChatAssistantState.handle_keydown,
                background=BG,
                border=f"1px solid {BORDER}",
                color=TEXT,
                font_family=FONT_MONO,
                font_size="0.85em",
                focus_border_color=PRIMARY,
                width="100%",
                _placeholder={"color": TEXT_MUTED},
            ),
            rx.button(
                "Analiz Et",
                on_click=AdminChatAssistantState.send_message,
                background=PRIMARY,
                color=BG,
                font_family=FONT_MONO,
                font_weight="600",
                font_size="0.85em",
                _hover={"opacity": "0.85"},
                disabled=AdminChatAssistantState.is_loading,
            ),
            width="100%",
            spacing="3",
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px",
    )

def cv_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("CV Yönetimi", size="4", color=TEXT),
        rx.cond(
            AdminCVState.cv_url != "",
            rx.vstack(
                rx.hstack(
                    rx.icon("file-text", color=PRIMARY),
                    rx.text(AdminCVState.cv_filename, color=TEXT),
                    rx.spacer(),
                    rx.link(
                        rx.button("İndir", background=PRIMARY, color=BG, size="1"),
                        href=AdminCVState.cv_url,
                        download=True
                    ),
                    rx.button("Sil", on_click=AdminCVState.delete_cv, background=ACCENT, color=BG, size="1"),
                    width="100%",
                    padding="1em",
                    background=BG,
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    align_items="center"
                ),
                width="100%"
            ),
            rx.text("Henüz CV yüklenmemiş.", color=TEXT_MUTED)
        ),

        rx.divider(margin_y="2em", border_color=BORDER),

        rx.vstack(
            rx.text("Yeni CV Yükle (PDF)", font_size="0.9em", color=TEXT_MUTED),
            rx.upload(
                rx.vstack(
                    rx.button("PDF Seç", background=BG, border=f"1px solid {BORDER}", color=TEXT),
                    rx.text("PDF dosyasını sürükleyin veya tıklayın", font_size="0.8em", color=TEXT_MUTED)
                ),
                id="cv_upload",
                border=f"1px dashed {BORDER}",
                padding="2em",
                border_radius="8px",
                width="100%",
                accept={
                    "application/pdf": [".pdf"]
                }
            ),
            rx.button(
                "Yükle",
                on_click=AdminCVState.handle_cv_upload(rx.upload_files(upload_id="cv_upload")),
                background=PRIMARY,
                color=BG,
                width="100%"
            ),
            width="100%",
            spacing="4"
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px"
    )


def admin_skill_category_card(cat: rx.Var, idx: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(
                cat["category"],
                font_family=FONT_MONO,
                font_size="1em",
                font_weight="bold",
                color=PRIMARY,
            ),
            rx.hstack(
                rx.foreach(
                    cat["skills"],
                    lambda tag: rx.text(
                        tag,
                        font_family=FONT_MONO,
                        font_size="0.75em",
                        color=TEXT,
                        border=f"1px solid {BORDER}",
                        background=BG,
                        padding="0.15em 0.55em",
                        border_radius="3px",
                    ),
                ),
                spacing="2",
                wrap="wrap",
                margin_top="0.4em",
            ),
            align_items="start",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                "Düzenle",
                on_click=lambda: AdminSkillsState.start_edit(idx),
                background=PRIMARY,
                color=BG,
                size="1",
                _hover={"opacity": 0.8},
            ),
            rx.button(
                "Sil",
                on_click=lambda: AdminSkillsState.delete_category(idx),
                background=ACCENT,
                color=BG,
                size="1",
                _hover={"opacity": 0.8},
            ),
            spacing="2",
        ),
        width="100%",
        padding="1.2em",
        background=BG,
        border=f"1px solid {BORDER}",
        border_radius="8px",
        margin_bottom="0.8em",
        align_items="center",
    )


def skills_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Beceriler Yönetimi", size="4", color=TEXT),
        rx.text(
            "Yetenek ve becerileri kategorize gruplar halinde burada düzenleyebilirsiniz.",
            font_size="0.85em",
            color=TEXT_MUTED,
            margin_bottom="1.5em",
        ),
        
        rx.vstack(
            rx.text(
                rx.cond(
                    AdminSkillsState.editing_index >= 0,
                    "Kategoriyi Düzenle",
                    "Yeni Kategori Ekle"
                ),
                font_weight="bold",
                color=TEXT,
                font_family=FONT_MONO,
                font_size="0.95em",
            ),
            rx.vstack(
                rx.text("Kategori Adı", font_size="0.8em", color=TEXT_MUTED),
                rx.input(
                    placeholder="Örn: AI & ML",
                    value=AdminSkillsState.category,
                    on_change=AdminSkillsState.set_category,
                    background=BG,
                    border=f"1px solid {BORDER}",
                    color=TEXT,
                    width="100%",
                ),
                align_items="start",
                width="100%",
            ),
            rx.vstack(
                rx.text("Beceriler (virgülle ayrılmış)", font_size="0.8em", color=TEXT_MUTED),
                rx.input(
                    placeholder="Örn: LLM, RAG, PyTorch",
                    value=AdminSkillsState.skills_str,
                    on_change=AdminSkillsState.set_skills_str,
                    background=BG,
                    border=f"1px solid {BORDER}",
                    color=TEXT,
                    width="100%",
                ),
                align_items="start",
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(
                        AdminSkillsState.editing_index >= 0,
                        "Güncelle",
                        "Ekle"
                    ),
                    on_click=AdminSkillsState.save_category,
                    background=PRIMARY,
                    color=BG,
                    size="2",
                    font_weight="600",
                ),
                rx.cond(
                    AdminSkillsState.editing_index >= 0,
                    rx.button(
                        "İptal",
                        on_click=AdminSkillsState.cancel_edit,
                        background="transparent",
                        border=f"1px solid {BORDER}",
                        color=TEXT_MUTED,
                        size="2",
                    ),
                    rx.fragment()
                ),
                spacing="3",
                margin_top="0.5em",
            ),
            spacing="3",
            width="100%",
            padding="1.5em",
            background=BG_CARD,
            border=f"1px solid {BORDER}",
            border_radius="10px",
            align_items="start",
            margin_bottom="2em",
        ),

        rx.vstack(
            rx.text("Kategoriler", font_weight="bold", color=TEXT, font_family=FONT_MONO, font_size="0.95em", margin_bottom="0.8em"),
            rx.cond(
                AdminSkillsState.skills_list.length() > 0,
                rx.vstack(
                    rx.foreach(
                        AdminSkillsState.skills_list,
                        lambda cat, idx: admin_skill_category_card(cat, idx)
                    ),
                    width="100%",
                ),
                rx.text("Kayıtlı kategori bulunamadı.", color=TEXT_MUTED, font_size="0.9em"),
            ),
            width="100%",
            align_items="start",
        ),
        width="100%",
        spacing="4",
        padding="2em",
        background=BG_CARD,
        border_radius="12px",
    )


def dashboard_card(title: str, count: rx.Var, icon: str, tab_value: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(icon, color=PRIMARY, size=24),
            rx.text(title, color=TEXT, font_family=FONT_MONO, font_size="1em"),
            width="100%",
            spacing="3",
            align="center",
        ),
        rx.text(
            count,
            color=PRIMARY,
            font_size="3em",
            font_weight="bold",
            style={"text_shadow": GLOW_PRIMARY},
        ),
        rx.button(
            f"Yönetime Git →",
            on_click=lambda: AdminState.set_active_tab(tab_value),
            background="transparent",
            border=f"1px solid {PRIMARY}33",
            color=PRIMARY,
            _hover={"background": f"{PRIMARY}15", "border_color": PRIMARY},
            width="100%",
            size="2",
        ),
        padding="2em",
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="16px",
        spacing="4",
        align="center",
        flex="1",
        transition="all 200ms",
        _hover={"border_color": PRIMARY, "transform": "translateY(-5px)"},
    )


def _intent_badge(label: rx.Var) -> rx.Component:
    """Small pill showing the dominant visitor intent."""
    return rx.cond(
        label != "",
        rx.hstack(
            rx.text(
                "●",
                color=PRIMARY,
                font_size="0.55em",
            ),
            rx.text(
                label,
                font_family=FONT_MONO,
                font_size="0.70em",
                color=PRIMARY,
                white_space="nowrap",
            ),
            padding="0.2em 0.6em",
            border=f"1px solid {PRIMARY}55",
            border_radius="999px",
            background=f"{PRIMARY}0d",
            align="center",
            gap="0.3em",
        ),
        rx.fragment(),
    )


def dashboard_summary_card() -> rx.Component:
    """
    AI-powered visitor intelligence card.

    Layout
    ------
    row 1  icon + title
    row 2  count badge  +  dominant intent pill
    row 3  top-project callout       (hidden when empty)
    row 4  executive summary paragraph
    row 5  visitor expectation       (hidden when empty)
    row 6  top-3 trend topic tags
    row 7  action button
    """
    return rx.vstack(
        # ── row 1: header ────────────────────────────────────────────
        rx.hstack(
            rx.icon("brain", color=PRIMARY, size=22),
            rx.text(
                "Ziyaretçi Analizi",
                color=TEXT,
                font_family=FONT_MONO,
                font_size="1em",
                white_space="nowrap",
            ),
            width="100%",
            spacing="3",
            align="center",
        ),
        # ── rows 2-6: content (loading spinner or real data) ────────────
        rx.cond(
            AdminState.chat_overview_loading,
            rx.hstack(
                rx.text(
                    "Analiz yapılıyor...",
                    color=TEXT_MUTED,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                ),
                align="center",
                gap="0.5em",
            ),
            rx.vstack(
                # ─ row 2: count  +  dominant intent ───────────────────
                rx.hstack(
                    rx.text(
                        rx.cond(
                            AdminState.chat_overview_visitor_count > 0,
                            f"{AdminState.chat_overview_visitor_count} kayıt  ·  {AdminState.chat_overview_message_count} mesaj",
                            "Henüz veri yok",
                        ),
                        color=PRIMARY,
                        font_family=FONT_MONO,
                        font_size="0.80em",
                        font_weight="700",
                    ),
                    _intent_badge(AdminState.chat_dominant_intent),
                    wrap="wrap",
                    gap="0.5em",
                    align="center",
                ),
                # ─ row 3: top project callout ────────────────────────
                rx.cond(
                    AdminState.chat_top_project != "",
                    rx.hstack(
                        rx.text(
                            "★",
                            color=PRIMARY,
                            font_size="0.65em",
                        ),
                        rx.text(
                            "En çok ilgi: ",
                            color=TEXT_MUTED,
                            font_family=FONT_MONO,
                            font_size="0.75em",
                        ),
                        rx.text(
                            AdminState.chat_top_project,
                            color=PRIMARY,
                            font_family=FONT_MONO,
                            font_size="0.75em",
                            font_weight="700",
                        ),
                        gap="0.25em",
                        align="center",
                    ),
                    rx.fragment(),
                ),
                # ─ row 4: executive summary ───────────────────────────
                rx.text(
                    AdminState.chat_overview,
                    color=TEXT_MUTED,
                    font_size="0.80em",
                    line_height="1.65",
                    width="100%",
                    word_break="break-word",
                ),
                # ─ row 5: visitor expectation ─────────────────────────
                rx.cond(
                    AdminState.chat_visitor_expectation != "",
                    rx.hstack(
                        rx.text(
                            "→",
                            color=PRIMARY,
                            font_family=FONT_MONO,
                            font_size="0.75em",
                        ),
                        rx.text(
                            AdminState.chat_visitor_expectation,
                            color=TEXT,
                            font_size="0.78em",
                            font_style="italic",
                            line_height="1.5",
                        ),
                        gap="0.4em",
                        align="start",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                # ─ row 6: trend topic tags ────────────────────────────
                rx.cond(
                    AdminState.chat_overview_topics.length() > 0,
                    rx.flex(
                        rx.foreach(
                            AdminState.chat_overview_topics,
                            lambda topic: rx.text(
                                topic,
                                font_family=FONT_MONO,
                                font_size="0.68em",
                                color=TEXT_MUTED,
                                border=f"1px solid {BORDER}",
                                padding="0.15em 0.55em",
                                border_radius="999px",
                                white_space="nowrap",
                            ),
                        ),
                        wrap="wrap",
                        gap="0.35em",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                spacing="2",
                align_items="start",
            ),
        ),
        # ── row 7: actions ────────────────────────────────────────
        rx.hstack(
            rx.button(
                "Özeti yenile",
                on_click=AdminState.refresh_chat_overview,
                background="transparent",
                border=f"1px solid {BORDER}",
                color=TEXT_MUTED,
                font_family=FONT_MONO,
                font_size="0.78em",
                _hover={"color": PRIMARY, "border_color": PRIMARY},
                flex="1",
                size="2",
            ),
            rx.button(
                "Asistana Sor →",
                on_click=lambda: AdminState.set_active_tab("chat-assistant"),
                background="transparent",
                border=f"1px solid {PRIMARY}33",
                color=PRIMARY,
                font_family=FONT_MONO,
                font_size="0.82em",
                _hover={"background": f"{PRIMARY}15", "border_color": PRIMARY},
                flex="1",
                size="2",
            ),
            width="100%",
            spacing="2",
        ),
        padding="2em",
        background=BG_CARD,
        border=f"1px solid {BORDER}",
        border_radius="16px",
        spacing="4",
        align="start",
        flex="1",
        transition="all 200ms",
        _hover={"border_color": PRIMARY, "transform": "translateY(-5px)"},
    )

def dashboard_tab() -> rx.Component:
    return rx.vstack(
        # ── stat cards row ────────────────────────────────────────────────
        # Use rx.box with display:grid so there is no conflict between the
        # Radix `columns` prop and the style dict (they both write
        # grid-template-columns, causing a race condition).
        rx.box(
            dashboard_card("Toplam Proje", AdminState.total_projects, "layout-grid", "projects"),
            dashboard_card("Toplam Blog", AdminState.total_blogs, "file-text", "blog"),
            dashboard_card("Sohbet Kayıtları", AdminState.total_chats, "message-square", "chats"),
            dashboard_summary_card(),
            display="grid",
            style={
                "grid_template_columns": "repeat(auto-fit, minmax(230px, 1fr))",
                "gap": "1.5rem",
                "align_items": "stretch",
            },
            width="100%",
        ),
        # ─────────────────────────────────────────────────────────────────
        rx.divider(margin_y="2.5em", border_color=BORDER),
        rx.vstack(
            rx.text(
                "Hızlı Erişim",
                font_family=FONT_MONO,
                font_size="0.72em",
                letter_spacing="0.15em",
                color=TEXT_MUTED,
                text_transform="uppercase",
            ),
            rx.flex(
                rx.button(
                    "Yeni Blog Yazısı",
                    on_click=lambda: AdminState.set_active_tab("blog"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                rx.button(
                    "Yeni Proje Ekle",
                    on_click=lambda: AdminState.set_active_tab("projects"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                rx.button(
                    "CV Güncelle",
                    on_click=lambda: AdminState.set_active_tab("cv"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                rx.button(
                    "Sohbet Önerileri",
                    on_click=lambda: AdminState.set_active_tab("chat-suggestions"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                rx.button(
                    "Chat Log Asistanı",
                    on_click=lambda: AdminState.set_active_tab("chat-assistant"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                rx.button(
                    "Eğitim & Deneyim",
                    on_click=lambda: AdminState.set_active_tab("eduexp"),
                    background="transparent",
                    border=f"1px solid {PRIMARY}55",
                    color=PRIMARY,
                    font_family=FONT_MONO,
                    font_size="0.82em",
                    _hover={"background": f"{PRIMARY}18", "border_color": PRIMARY},
                ),
                gap="0.6em",
                wrap="wrap",
                width="100%",
            ),
            width="100%",
            align="start",
            spacing="3",
        ),
        width="100%",
        padding="1em",
    )

def career_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("CV / Geçmiş Yönetimi", size="4", color=TEXT),

        # Education Form
        rx.vstack(
            rx.text("Eğitim Ekle", font_weight="bold", color=PRIMARY),
            rx.hstack(
                rx.input(placeholder="Okul Adı", value=AdminCareerState.edu_okul, on_change=AdminCareerState.set_edu_okul, background=BG),
                rx.input(placeholder="Bölüm", value=AdminCareerState.edu_bolum, on_change=AdminCareerState.set_edu_bolum, background=BG),
                width="100%"
            ),
            rx.hstack(
                rx.input(placeholder="Başlangıç", value=AdminCareerState.edu_baslangic, on_change=AdminCareerState.set_edu_baslangic, background=BG),
                rx.input(placeholder="Mezuniyet", value=AdminCareerState.edu_mezuniyet, on_change=AdminCareerState.set_edu_mezuniyet, background=BG),
                width="100%"
            ),
            rx.text_area(placeholder="Detaylar", value=AdminCareerState.edu_detay, on_change=AdminCareerState.set_edu_detay, width="100%", background=BG),
            rx.button("Eğitim Ekle", on_click=AdminCareerState.add_education, background=PRIMARY, color=BG, width="100%"),
            padding="1.5em", border=f"1px solid {BORDER}", border_radius="10px", width="100%"
        ),

        # Experience Form
        rx.vstack(
            rx.text("Deneyim Ekle", font_weight="bold", color=PRIMARY),
            rx.hstack(
                rx.input(placeholder="Şirket Adı", value=AdminCareerState.exp_sirket, on_change=AdminCareerState.set_exp_sirket, background=BG),
                rx.input(placeholder="Pozisyon", value=AdminCareerState.exp_pozisyon, on_change=AdminCareerState.set_exp_pozisyon, background=BG),
                width="100%"
            ),
            rx.input(placeholder="Süre (örn: 2023 - Devam)", value=AdminCareerState.exp_sure, on_change=AdminCareerState.set_exp_sure, width="100%", background=BG),
            rx.text_area(placeholder="Açıklama", value=AdminCareerState.exp_aciklama, on_change=AdminCareerState.set_exp_aciklama, width="100%", background=BG),
            rx.button("Deneyim Ekle", on_click=AdminCareerState.add_experience, background=PRIMARY, color=BG, width="100%"),
            padding="1.5em", border=f"1px solid {BORDER}", border_radius="10px", width="100%"
        ),

        rx.divider(margin_y="2em", border_color=BORDER),

        # Lists
        rx.grid(
            rx.vstack(
                rx.text("Mevcut Eğitimler", font_weight="bold"),
                rx.foreach(AdminCareerState.educations, lambda edu: rx.hstack(
                    # Use dict key access + Var string concat, NOT f-strings.
                    # f"{edu.okul_adi}" would call __format__ on the Var object
                    # at component-build time, producing a static repr string.
                    rx.text(edu["okul_adi"] + " - " + edu["bolum"], flex="1", font_size="0.9em"),
                    rx.button(rx.icon("trash-2", size=14), on_click=AdminCareerState.delete_education(edu["id"]), color=ACCENT, variant="ghost"),
                    width="100%", padding="0.5em", border_bottom=f"1px solid {BORDER}"
                )),
                width="100%"
            ),
            rx.vstack(
                rx.text("Mevcut Deneyimler", font_weight="bold"),
                rx.foreach(AdminCareerState.experiences, lambda exp: rx.hstack(
                    rx.text(exp["sirket_adi"] + " - " + exp["pozisyon"], flex="1", font_size="0.9em"),
                    rx.button(rx.icon("trash-2", size=14), on_click=AdminCareerState.delete_experience(exp["id"]), color=ACCENT, variant="ghost"),
                    width="100%", padding="0.5em", border_bottom=f"1px solid {BORDER}"
                )),
                width="100%"
            ),
            columns="2", spacing="6", width="100%"
        ),
        width="100%", spacing="6"
    )


def edu_exp_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Deneyim Ekle", font_weight="bold", color=PRIMARY),
                rx.input(placeholder="Sirket", value=AdminEduExpState.exp_company, on_change=AdminEduExpState.set_exp_company, width="100%", background=BG),
                rx.input(placeholder="Rol", value=AdminEduExpState.exp_role, on_change=AdminEduExpState.set_exp_role, width="100%", background=BG),
                rx.hstack(
                    rx.input(placeholder="Baslangic", value=AdminEduExpState.exp_start, on_change=AdminEduExpState.set_exp_start, width="100%", background=BG),
                    rx.input(placeholder="Bitis", value=AdminEduExpState.exp_end, on_change=AdminEduExpState.set_exp_end, width="100%", background=BG),
                    width="100%",
                ),
                rx.text_area(placeholder="Aciklama", value=AdminEduExpState.exp_desc, on_change=AdminEduExpState.set_exp_desc, width="100%", background=BG),
                rx.vstack(
                    rx.text("Etiketler", color=TEXT_MUTED, font_size="0.9em"),
                    rx.flex(
                        rx.foreach(
                            AdminEduExpState.exp_tags_options,
                            lambda tag: rx.box(
                                rx.hstack(
                                    rx.cond(
                                        AdminEduExpState.exp_tags_selected.contains(tag),
                                        rx.text("✓", color=PRIMARY, font_family=FONT_MONO, font_size="0.8em"),
                                        rx.text("○", color=TEXT_MUTED, font_family=FONT_MONO, font_size="0.8em"),
                                    ),
                                    rx.text(tag, font_family=FONT_MONO, font_size="0.8em", color=TEXT),
                                    gap="0.4em",
                                    align="center",
                                ),
                                padding="0.3em 0.8em",
                                border=rx.cond(
                                    AdminEduExpState.exp_tags_selected.contains(tag),
                                    f"1px solid {PRIMARY}",
                                    f"1px solid {BORDER}",
                                ),
                                border_radius="4px",
                                background=rx.cond(
                                    AdminEduExpState.exp_tags_selected.contains(tag),
                                    f"{PRIMARY}15",
                                    BG_CARD,
                                ),
                                cursor="pointer",
                                on_click=lambda: AdminEduExpState.toggle_exp_tag(tag),
                                transition="all 150ms",
                            ),
                        ),
                        wrap="wrap",
                        spacing="2",
                        width="100%",
                    ),
                    width="100%",
                    align_items="start",
                    spacing="2",
                ),
                    rx.hstack(
                        rx.cond(
                            AdminEduExpState.editing_exp_index >= 0,
                            rx.button("Güncelle", on_click=AdminEduExpState.save_experience, background=PRIMARY, color=BG, width="100%"),
                            rx.button("Kaydet", on_click=AdminEduExpState.save_experience, background=PRIMARY, color=BG, width="100%"),
                        ),
                        rx.cond(
                            AdminEduExpState.editing_exp_index >= 0,
                            rx.button("Vazgeç", on_click=AdminEduExpState.cancel_edit_experience, background="transparent", color=ACCENT, border=f"1px solid {ACCENT}", size="1"),
                            rx.fragment(),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                width="100%",
                padding="1.5em",
                border=f"1px solid {BORDER}",
                border_radius="10px",
                align_items="start",
                spacing="3",
            ),
            rx.vstack(
                rx.text("Egitim Ekle", font_weight="bold", color=PRIMARY),
                rx.input(placeholder="Okul", value=AdminEduExpState.edu_school, on_change=AdminEduExpState.set_edu_school, width="100%", background=BG),
                rx.input(placeholder="Bolum", value=AdminEduExpState.edu_dept, on_change=AdminEduExpState.set_edu_dept, width="100%", background=BG),
                rx.input(placeholder="Derece", value=AdminEduExpState.edu_degree, on_change=AdminEduExpState.set_edu_degree, width="100%", background=BG),
                rx.hstack(
                    rx.input(placeholder="Baslangic", value=AdminEduExpState.edu_start, on_change=AdminEduExpState.set_edu_start, width="100%", background=BG),
                    rx.input(placeholder="Bitis", value=AdminEduExpState.edu_end, on_change=AdminEduExpState.set_edu_end, width="100%", background=BG),
                    width="100%",
                ),
                rx.text_area(placeholder="Aciklama", value=AdminEduExpState.edu_desc, on_change=AdminEduExpState.set_edu_desc, width="100%", background=BG),
                rx.hstack(
                    rx.cond(
                        AdminEduExpState.editing_edu_index >= 0,
                        rx.button("Güncelle", on_click=AdminEduExpState.save_education, background=PRIMARY, color=BG, width="100%"),
                        rx.button("Kaydet", on_click=AdminEduExpState.save_education, background=PRIMARY, color=BG, width="100%"),
                    ),
                    rx.cond(
                        AdminEduExpState.editing_edu_index >= 0,
                        rx.button("Vazgeç", on_click=AdminEduExpState.cancel_edit_education, background="transparent", color=ACCENT, border=f"1px solid {ACCENT}", size="1"),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                ),
                width="100%",
                padding="1.5em",
                border=f"1px solid {BORDER}",
                border_radius="10px",
                align_items="start",
                spacing="3",
            ),
            gap="2em",
            align="start",
            width="100%",
        ),
        rx.divider(margin_y="2em", border_color=BORDER),
        rx.grid(
            rx.vstack(
                rx.text("Mevcut Deneyimler", font_weight="bold", color=TEXT),
                rx.foreach(
                    AdminEduExpState.experiences,
                    lambda exp, index: rx.hstack(
                        rx.vstack(
                            rx.text(exp["company"], color=TEXT, font_weight="600"),
                            rx.text(exp["role"], color=TEXT_MUTED, font_size="0.85em"),
                            align_items="start",
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.button("Düzenle", on_click=lambda: AdminEduExpState.start_edit_experience(index), background=PRIMARY, color=BG, size="1"),
                            rx.button("Sil", on_click=lambda: AdminEduExpState.delete_experience(index), background=ACCENT, color=BG, size="1"),
                            spacing="2",
                        ),
                        width="100%",
                        padding="0.75em",
                        border=rx.cond(AdminEduExpState.highlighted_exp_index == index, f"2px solid {PRIMARY}", f"1px solid {BORDER}"),
                        box_shadow=rx.cond(AdminEduExpState.highlighted_exp_index == index, f"0 6px 18px {PRIMARY}33", "none"),
                        border_radius="8px",
                        background=BG,
                        align_items="center",
                    ),
                ),
                width="100%",
                spacing="2",
                align_items="start",
            ),
            rx.vstack(
                rx.text("Mevcut Egitimler", font_weight="bold", color=TEXT),
                rx.foreach(
                    AdminEduExpState.education,
                    lambda edu, index: rx.hstack(
                        rx.vstack(
                            rx.text(edu["school"], color=TEXT, font_weight="600"),
                            rx.text(edu["department"], color=TEXT_MUTED, font_size="0.85em"),
                            align_items="start",
                            spacing="1",
                        ),
                        rx.spacer(),
                        rx.hstack(
                                rx.button("Düzenle", on_click=lambda: AdminEduExpState.start_edit_education(index), background=PRIMARY, color=BG, size="1"),
                            rx.button("Sil", on_click=lambda: AdminEduExpState.delete_education(index), background=ACCENT, color=BG, size="1"),
                            spacing="2",
                        ),
                        width="100%",
                        padding="0.75em",
                        border=rx.cond(AdminEduExpState.highlighted_edu_index == index, f"2px solid {PRIMARY}", f"1px solid {BORDER}"),
                        box_shadow=rx.cond(AdminEduExpState.highlighted_edu_index == index, f"0 6px 18px {PRIMARY}33", "none"),
                        border_radius="8px",
                        background=BG,
                        align_items="center",
                    ),
                ),
                width="100%",
                spacing="2",
                align_items="start",
            ),
            columns="2",
            spacing="6",
            width="100%",
        ),
        width="100%",
        spacing="4",
    )

def admin_page() -> rx.Component:
    return rx.cond(
        AdminAuthState.is_authenticated,
        rx.vstack(
            # Toast
            rx.cond(
                AdminEduExpState.toast_message != "",
                rx.hstack(
                    rx.box(
                        rx.text(AdminEduExpState.toast_message, color=BG),
                        padding="0.6em 1em",
                        background=PRIMARY,
                        border_radius="8px",
                    ),
                    rx.button("Kapat", on_click=AdminEduExpState.clear_toast, background="transparent", color=PRIMARY, border=f"1px solid {PRIMARY}", size="1"),
                    position="fixed",
                    top="1.5em",
                    right="1.5em",
                    z_index=9999,
                    align_items="center",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.heading("Yönetim Paneli", size="6", color=PRIMARY, font_family=FONT_MONO),
                rx.spacer(),
                rx.button("Çıkış Yap", on_click=AdminAuthState.logout, background="transparent", border=f"1px solid {ACCENT}", color=ACCENT),
                width="100%",
                padding="1em 2em",
                background=BG_CARD,
                border_bottom=f"1px solid {BORDER}"
            ),
            rx.tabs.root(
                rx.tabs.list(
                        rx.tabs.trigger("Dashboard", value="dashboard", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Blog Yönetimi", value="blog", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Proje Yönetimi", value="projects", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Sohbet Kayıtları", value="chats", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Chat Suggestions", value="chat-suggestions", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Chat Log Asistanı", value="chat-assistant", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Eğitim & Deneyim", value="eduexp", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("CV Yönetimi", value="cv", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        rx.tabs.trigger("Beceriler", value="skills", style={"white_space": "nowrap", "flex_shrink": "0"}),
                        background=BG_CARD,
                        style={
                            "overflow_x": "auto",
                            "overflow_y": "hidden",
                            "max_width": "100%",
                            "gap": "0.4rem",
                            "padding_bottom": "0.35rem",
                            "scrollbar_width": "thin",
                        }
                ),
                rx.tabs.content(
                    dashboard_tab(),
                    value="dashboard",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    blog_tab(),
                    value="blog",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    project_tab(),
                    value="projects",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    chat_log_tab(),
                    value="chats",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    chat_suggestions_tab(),
                    value="chat-suggestions",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    admin_chat_tab(),
                    value="chat-assistant",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    edu_exp_tab(),
                    value="eduexp",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    cv_tab(),
                    value="cv",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    skills_tab(),
                    value="skills",
                    padding_top="2em"
                ),
                value=AdminState.active_tab,
                on_change=AdminState.set_active_tab,
                width="100%",
                max_width="1200px",
                style={"padding_left": "1rem", "padding_right": "1rem"},
            ),
            width="100%",
            align_items="center",
            padding_bottom="4em",
            background=BG,
            min_height="100vh"
        ),
        login_form()
    )
