import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.state.admin_state import AdminAuthState, AdminBlogState, AdminProjectState, AdminChatLogState, AdminCVState, AdminState, AdminCareerState, AdminEduExpState
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
        rx.input(placeholder="Proje İsmi", value=AdminProjectState.project_name, on_change=AdminProjectState.set_project_name, width="100%", background=BG),
        tag_checkbox_grid(AdminProjectState),
        rx.text_area(placeholder="Açıklama", value=AdminProjectState.project_desc, on_change=AdminProjectState.set_project_desc, width="100%", background=BG),
        rx.button("Projeyi Kaydet", on_click=AdminProjectState.save_project, background=PRIMARY, color=BG, width="100%"),
        
        rx.divider(margin_y="2em", border_color=BORDER),
        
        rx.heading("Mevcut Projeler", size="4", color=TEXT),
        rx.vstack(
                rx.foreach(
                AdminProjectState.all_admin_projects,
                lambda proj, index: rx.hstack(
                    rx.text(proj["name"], color=TEXT, flex="1"),
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

def dashboard_tab() -> rx.Component:
    return rx.vstack(
        rx.grid(
            dashboard_card("Toplam Proje", AdminState.total_projects, "layout-grid", "projects"),
            dashboard_card("Toplam Blog", AdminState.total_blogs, "file-text", "blog"),
            dashboard_card("Sohbet Kayıtları", AdminState.total_chats, "message-square", "chats"),
            columns="3",
            spacing="6",
            width="100%",
        ),
        rx.divider(margin_y="3em", border_color=BORDER),
        rx.vstack(
            rx.heading("Hızlı Erişim", size="4", color=TEXT_MUTED),
            rx.flex(
                rx.button(
                    "Yeni Blog Yazısı", 
                    on_click=lambda: AdminState.set_active_tab("blog"),
                    background=PRIMARY, color=BG
                ),
                rx.button(
                    "Yeni Proje Ekle", 
                    on_click=lambda: AdminState.set_active_tab("projects"),
                    background=PRIMARY, color=BG
                ),
                rx.button(
                    "CV Güncelle", 
                    on_click=lambda: AdminState.set_active_tab("cv"),
                    background=PRIMARY, color=BG
                ),
                rx.button(
                    "Egitim & Deneyim", 
                    on_click=lambda: AdminState.set_active_tab("eduexp"),
                    background=PRIMARY, color=BG
                ),
                spacing="4",
                wrap="wrap",
            ),
            width="100%",
            align="start",
            spacing="4",
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
                    rx.text(f"{edu.okul_adi} - {edu.bolum}", flex="1", font_size="0.9em"),
                    rx.button(rx.icon("trash-2", size=14), on_click=lambda: AdminCareerState.delete_education(edu.id), color=ACCENT, variant="ghost"),
                    width="100%", padding="0.5em", border_bottom=f"1px solid {BORDER}"
                )),
                width="100%"
            ),
            rx.vstack(
                rx.text("Mevcut Deneyimler", font_weight="bold"),
                rx.foreach(AdminCareerState.experiences, lambda exp: rx.hstack(
                    rx.text(f"{exp.sirket_adi} - {exp.pozisyon}", flex="1", font_size="0.9em"),
                    rx.button(rx.icon("trash-2", size=14), on_click=lambda: AdminCareerState.delete_experience(exp.id), color=ACCENT, variant="ghost"),
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

@rx.page(
    route="/admin", 
    on_load=[AdminState.load_admin_data, AdminEduExpState.on_load]
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
                    rx.tabs.trigger("Dashboard", value="dashboard"),
                    rx.tabs.trigger("Blog Yönetimi", value="blog"),
                    rx.tabs.trigger("Proje Yönetimi", value="projects"),
                    rx.tabs.trigger("Sohbet Kayıtları", value="chats"),
                    rx.tabs.trigger("Eğitim & Deneyim", value="eduexp"),
                    rx.tabs.trigger("CV Yönetimi", value="cv"),
                    background=BG_CARD
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
                    edu_exp_tab(),
                    value="eduexp",
                    padding_top="2em"
                ),
                rx.tabs.content(
                    cv_tab(),
                    value="cv",
                    padding_top="2em"
                ),
                value=AdminState.active_tab,
                on_change=AdminState.set_active_tab,
                width="100%",
                max_width="1000px"
            ),
            width="100%",
            align_items="center",
            padding_bottom="4em",
            background=BG,
            min_height="100vh"
        ),
        login_form()
    )
