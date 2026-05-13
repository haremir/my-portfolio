import reflex as rx

from harun_site.components.navbar import navbar
from harun_site.components.footer import footer
from harun_site.state.admin_state import AdminAuthState, AdminBlogState, AdminProjectState, AdminChatLogState
from harun_site.theme import BG, BG_CARD, PRIMARY, TEXT, TEXT_MUTED, BORDER, ACCENT, FONT_SANS, FONT_MONO

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
            rx.input(placeholder="Etiketler (virgülle ayrılmış)", value=AdminBlogState.blog_tags_str, on_change=AdminBlogState.set_blog_tags_str, width="100%", background=BG),
            width="100%",
            spacing="4"
        ),
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
        rx.input(placeholder="Etiketler (virgülle ayrılmış)", value=AdminProjectState.project_tags_str, on_change=AdminProjectState.set_project_tags_str, width="100%", background=BG),
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
            rx.heading("Sohbet Kayıtları", size="4", color=TEXT),
            rx.foreach(
                AdminChatLogState.chat_logs,
                lambda log: rx.hstack(
                    rx.vstack(
                        rx.text(log["timestamp"], color=TEXT, font_size="0.9em"),
                        rx.text(f"{log['message_count']} mesaj", color=TEXT_MUTED, font_size="0.75em"),
                        align_items="start"
                    ),
                    rx.spacer(),
                    rx.button("Gör", on_click=lambda: AdminChatLogState.view_log(log["filename"]), background="transparent", border=f"1px solid {PRIMARY}", color=PRIMARY, size="1"),
                    rx.button("Sil", on_click=lambda: AdminChatLogState.delete_log(log["filename"]), background="transparent", border=f"1px solid {ACCENT}", color=ACCENT, size="1"),
                    width="100%",
                    padding="0.8em",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    background=BG,
                    align_items="center"
                )
            ),
            width="35%",
            height="600px",
            overflow_y="auto",
            spacing="2"
        ),
        
        # Sağ taraf: detay
        rx.box(
            rx.cond(
                AdminChatLogState.selected_log_name != "",
                rx.vstack(
                    rx.text(f"Kayıt: {AdminChatLogState.selected_log_name}", color=PRIMARY, font_family=FONT_MONO),
                    rx.divider(border_color=BORDER),
                    rx.box(
                        rx.vstack(
                            rx.foreach(
                                AdminChatLogState.selected_log,
                                lambda msg: rx.box(
                                    rx.text(msg["role"].upper(), font_size="0.7em", color=PRIMARY, margin_bottom="0.2em", font_family=FONT_MONO),
                                    rx.text(msg["content"], font_size="0.9em"),
                                    background=rx.cond(msg["role"] == "user", f"{PRIMARY}22", BG_CARD),
                                    border=rx.cond(msg["role"] == "user", f"1px solid {PRIMARY}", f"1px solid {BORDER}"),
                                    padding="1em",
                                    border_radius="8px",
                                    width="100%",
                                    margin_bottom="1em"
                                )
                            ),
                            width="100%",
                        ),
                        width="100%",
                        height="500px",
                        overflow_y="auto",
                        padding="1em",
                        background=BG,
                        border_radius="8px"
                    ),
                    width="100%"
                ),
                rx.center(rx.text("Bir kayıt seçin.", color=TEXT_MUTED), height="100%")
            ),
            width="65%",
            height="600px",
            background=BG_CARD,
            border_radius="12px",
            padding="2em",
            border=f"1px solid {BORDER}"
        ),
        width="100%",
        spacing="4",
        align_items="start"
    )

def on_load_admin():
    return [
        AdminBlogState.load_posts(),
        AdminProjectState.load_projects(),
        AdminChatLogState.load_logs()
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
