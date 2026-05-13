import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.state.admin_state import AdminAuthState, AdminBlogState, AdminProjectState, AdminChatLogState, AdminCVState
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
                    rx.button("Sil", on_click=lambda: AdminBlogState.delete_post(post["slug"]), background=ACCENT, color=BG, size="1"),
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
                    rx.button("Sil", on_click=lambda: AdminProjectState.delete_project(index), background=ACCENT, color=BG, size="1"),
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
        # Sol taraf: liste
        rx.vstack(
            rx.heading("Sohbet Özetleri", size="4", color=TEXT),
            rx.foreach(
                AdminChatLogState.chat_logs,
                lambda log: rx.vstack(
                    rx.hstack(
                        rx.text(log["date"], color=TEXT, font_size="0.8em", font_family=FONT_MONO),
                        rx.spacer(),
                        rx.text(f"{log['message_count']} mesaj", color=TEXT_MUTED, font_size="0.75em"),
                        rx.button(
                            rx.icon("trash-2", size=14),
                            on_click=lambda: AdminChatLogState.delete_log(log["filename"]),
                            background="transparent",
                            color=ACCENT,
                            _hover={"color": "red"},
                            padding="0"
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

def on_load_admin():
    return [
        AdminBlogState.load_posts(),
        AdminProjectState.load_projects(),
        AdminChatLogState.load_logs(),
        AdminCVState.load_cv()
    ]

@rx.page(route="/admin", on_load=on_load_admin)
def admin_page() -> rx.Component:
    return rx.cond(
        AdminAuthState.is_authenticated,
        rx.vstack(
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
                    rx.tabs.trigger("Blog Yönetimi", value="blog"),
                    rx.tabs.trigger("Proje Yönetimi", value="projects"),
                    rx.tabs.trigger("Sohbet Kayıtları", value="chats"),
                    rx.tabs.trigger("CV Yönetimi", value="cv"),
                    background=BG_CARD
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
                    cv_tab(),
                    value="cv",
                    padding_top="2em"
                ),
                defaultValue="blog",
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
