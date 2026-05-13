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

class ChatSummaryDict(TypedDict):
    filename: str
    date: str
    summary: str
    top_topics: list[str]
    message_count: int

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
    
    available_tags: list[str] = []
    selected_tags: list[str] = []
    new_tag_name: str = ""
    
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

    def set_new_tag_name(self, val: str):
        self.new_tag_name = val

    def toggle_tag(self, tag: str):
        if tag in self.selected_tags:
            self.selected_tags = [t for t in self.selected_tags if t != tag]
        else:
            self.selected_tags = self.selected_tags + [tag]

    def add_new_tag(self):
        if self.new_tag_name:
            data_manager.add_tag(self.new_tag_name)
            if self.new_tag_name not in self.selected_tags:
                self.selected_tags = self.selected_tags + [self.new_tag_name]
            self.new_tag_name = ""
            self.load_tags()

    def load_tags(self):
        self.available_tags = data_manager.load_tags()

    def load_posts(self):
        self.load_tags()
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
            
        data_manager.save_blog_post(
            slug=self.blog_slug,
            title=self.blog_title,
            date=date_to_save,
            description=self.blog_description,
            tags=self.selected_tags,
            content=self.blog_content,
            cover=self.blog_cover_path
        )
        
        # Clear form
        self.blog_title = ""
        self.blog_slug = ""
        self.blog_date = ""
        self.blog_description = ""
        self.selected_tags = []
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
    
    available_tags: list[str] = []
    selected_tags: list[str] = []
    new_tag_name: str = ""
    
    def set_project_name(self, val: str):
        self.project_name = val
        
    def set_project_desc(self, val: str):
        self.project_desc = val

    def set_new_tag_name(self, val: str):
        self.new_tag_name = val

    def toggle_tag(self, tag: str):
        if tag in self.selected_tags:
            self.selected_tags = [t for t in self.selected_tags if t != tag]
        else:
            self.selected_tags = self.selected_tags + [tag]

    def add_new_tag(self):
        if self.new_tag_name:
            data_manager.add_tag(self.new_tag_name)
            if self.new_tag_name not in self.selected_tags:
                self.selected_tags = self.selected_tags + [self.new_tag_name]
            self.new_tag_name = ""
            self.load_tags()

    def load_tags(self):
        self.available_tags = data_manager.load_tags()

    def load_projects(self):
        self.load_tags()
        self.all_admin_projects = data_manager.load_projects()

    def save_project(self):
        if not self.project_name:
            return rx.window_alert("Proje ismi zorunludur.")
            
        data_manager.add_project(self.project_name, self.project_desc, self.selected_tags)
        
        self.project_name = ""
        self.project_desc = ""
        self.selected_tags = []
        
        self.load_projects()

    def delete_project(self, index: int):
        data_manager.delete_project(index)
        self.load_projects()


class AdminChatLogState(rx.State):
    chat_logs: list[ChatSummaryDict] = []
    selected_log: list[ChatMessageDict] = []
    selected_log_name: str = ""
    
    def load_logs(self):
        import json
        summary_dir = data_manager.SUMMARIES_DIR
        if not summary_dir.exists():
            self.chat_logs = []
            return
        logs = []
        for f in sorted(summary_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                logs.append({
                    "filename": f.name,
                    "date": data.get("date", f.stem),
                    "summary": data.get("summary", ""),
                    "top_topics": data.get("top_topics", []),
                    "message_count": data.get("message_count", 0),
                })
            except Exception:
                pass
        self.chat_logs = logs
        
    def view_log(self, filename: str):
        # This now might not work if we only have summaries. 
        # But wait, the user wants to read from summaries.
        # If they want to see messages, they need the original log too.
        # I'll keep the view_log pointing to CHAT_LOGS_DIR if filename matches.
        self.selected_log_name = filename
        self.selected_log = data_manager.load_chat_log_messages(filename)
        
    def delete_log(self, filename: str):
        # Delete both summary and original log
        summary_path = data_manager.SUMMARIES_DIR / filename
        if summary_path.exists():
            summary_path.unlink()
        
        data_manager.delete_chat_log(filename)
        if self.selected_log_name == filename:
            self.selected_log_name = ""
            self.selected_log = []
        self.load_logs()

class AdminCVState(rx.State):
    cv_filename: str = ""
    cv_url: str = ""
    
    def load_cv(self):
        self.cv_url = data_manager.get_cv_path()
        if self.cv_url:
            self.cv_filename = self.cv_url.split("/")[-1]
        else:
            self.cv_filename = ""

    async def handle_cv_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = await file.read()
            self.cv_url = data_manager.save_cv(upload_data, file.filename)
            self.cv_filename = file.filename
            break
        return rx.window_alert("CV yüklendi!")

    def delete_cv(self):
        cv_dir = data_manager.CV_DIR
        for f in cv_dir.glob("*.pdf"):
            f.unlink()
        self.cv_url = ""
        self.cv_filename = ""
        return rx.window_alert("CV silindi!")
