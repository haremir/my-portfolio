import os
import reflex as rx
from harun_site.utils import data_manager
from harun_site.utils.markdown_parser import get_all_posts
from typing import TypedDict

class ChatMessageDict(TypedDict):
    role: str
    content: str

class ChatLogDict(TypedDict):
    timestamp: str
    message_count: int
    filename: str

class AdminPostDict(TypedDict):
    slug: str
    title: str
    date: str

class AdminProjectDict(TypedDict):
    name: str
    desc: str
    tags: list[str]

class AdminAuthState(rx.State):
    password: str = ""
    is_authenticated: bool = False
    login_error: str = ""

    def set_password(self, value: str):
        self.password = value

    def login(self):
        env_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        if self.password == env_password:
            self.is_authenticated = True
            self.login_error = ""
            self.password = ""
        else:
            self.login_error = "Hatalı şifre"
            self.password = ""

    def logout(self):
        self.is_authenticated = False


class AdminBlogState(rx.State):
    all_admin_posts: list[AdminPostDict] = []
    
    # Form fields
    blog_title: str = ""
    blog_slug: str = ""
    blog_date: str = ""
    blog_description: str = ""
    blog_tags_str: str = ""
    blog_content: str = ""
    blog_cover_path: str = ""
    
    is_uploading: bool = False
    
    def set_blog_title(self, val: str):
        self.blog_title = val
        
    def set_blog_slug(self, val: str):
        self.blog_slug = val
        
    def set_blog_date(self, val: str):
        self.blog_date = val
        
    def set_blog_description(self, val: str):
        self.blog_description = val
        
    def set_blog_tags_str(self, val: str):
        self.blog_tags_str = val
        
    def set_blog_content(self, val: str):
        self.blog_content = val
        
    def set_blog_cover_path(self, val: str):
        self.blog_cover_path = val
    
    def load_posts(self):
        posts = get_all_posts()
        self.all_admin_posts = [
            {
                "slug": p.slug,
                "title": p.title,
                "date": p.date,
            }
            for p in posts
        ]

    async def handle_upload(self, files: list[rx.UploadFile]):
        self.is_uploading = True
        yield
        
        for file in files:
            upload_data = await file.read()
            filename = file.filename
            
            # Save to assets/blog
            # Ensure assets/blog exists
            import pathlib
            assets_dir = pathlib.Path.cwd() / "assets" / "blog"
            assets_dir.mkdir(parents=True, exist_ok=True)
            
            outfile = assets_dir / filename
            with open(outfile, "wb") as f:
                f.write(upload_data)
                
            self.blog_cover_path = f"/blog/{filename}"
            break # only one file
            
        self.is_uploading = False

    def save_post(self):
        if not self.blog_slug or not self.blog_title:
            return rx.window_alert("Slug ve Başlık zorunludur.")
            
        tags = [t.strip() for t in self.blog_tags_str.split(",") if t.strip()]
        
        # If date is empty, use today
        date_to_save = self.blog_date
        if not date_to_save:
            from datetime import datetime
            date_to_save = datetime.now().strftime("%Y-%m-%d")
            
        data_manager.save_blog_post(
            slug=self.blog_slug,
            title=self.blog_title,
            date=date_to_save,
            description=self.blog_description,
            tags=tags,
            content=self.blog_content,
            cover=self.blog_cover_path
        )
        
        # Clear form
        self.blog_title = ""
        self.blog_slug = ""
        self.blog_date = ""
        self.blog_description = ""
        self.blog_tags_str = ""
        self.blog_content = ""
        self.blog_cover_path = ""
        
        self.load_posts()
        return rx.window_alert("Blog yazısı kaydedildi!")

    def delete_post(self, slug: str):
        data_manager.delete_blog_post(slug)
        self.load_posts()


class AdminProjectState(rx.State):
    all_admin_projects: list[AdminProjectDict] = []
    
    project_name: str = ""
    project_desc: str = ""
    project_tags_str: str = ""
    
    def set_project_name(self, val: str):
        self.project_name = val
        
    def set_project_desc(self, val: str):
        self.project_desc = val
        
    def set_project_tags_str(self, val: str):
        self.project_tags_str = val
    
    def load_projects(self):
        self.all_admin_projects = data_manager.load_projects()

    def save_project(self):
        if not self.project_name:
            return rx.window_alert("Proje ismi zorunludur.")
            
        tags = [t.strip() for t in self.project_tags_str.split(",") if t.strip()]
        data_manager.add_project(self.project_name, self.project_desc, tags)
        
        self.project_name = ""
        self.project_desc = ""
        self.project_tags_str = ""
        
        self.load_projects()

    def delete_project(self, index: int):
        data_manager.delete_project(index)
        self.load_projects()


class AdminChatLogState(rx.State):
    chat_logs: list[ChatLogDict] = []
    selected_log: list[ChatMessageDict] = []
    selected_log_name: str = ""
    
    def load_logs(self):
        self.chat_logs = data_manager.load_chat_logs()
        
    def view_log(self, filename: str):
        self.selected_log_name = filename
        self.selected_log = data_manager.load_chat_log_messages(filename)
        
    def delete_log(self, filename: str):
        data_manager.delete_chat_log(filename)
        if self.selected_log_name == filename:
            self.selected_log_name = ""
            self.selected_log = []
        self.load_logs()
