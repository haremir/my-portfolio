import os
import reflex as rx
from harun_site.utils import data_manager
from harun_site.utils.markdown_parser import get_all_posts, get_post_by_slug
from typing import TypedDict
from harun_site.models import EducationModel, ExperienceModel

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

    @rx.event
    def set_password(self, value: str):
        self.password = value

    @rx.event
    def login(self):
        env_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        if self.password == env_password:
            self.is_authenticated = True
            self.login_error = ""
            self.password = ""
        else:
            self.login_error = "Hatalı şifre"
            self.password = ""

    @rx.event
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
    editing_blog_slug: str = ""
    
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

    @rx.event
    def toggle_tag(self, tag: str):
        if tag in self.selected_tags:
            self.selected_tags = [t for t in self.selected_tags if t != tag]
        else:
            self.selected_tags = self.selected_tags + [tag]

    @rx.event
    def add_new_tag(self):
        if self.new_tag_name:
            data_manager.add_tag(self.new_tag_name)
            if self.new_tag_name not in self.selected_tags:
                self.selected_tags = self.selected_tags + [self.new_tag_name]
            self.new_tag_name = ""
            self.load_tags()

    @rx.event
    def delete_tag(self, tag: str):
        data_manager.delete_tag(tag)
        self.selected_tags = [item for item in self.selected_tags if item != tag]
        self.load_tags()

    @rx.event
    def load_tags(self):
        self.available_tags = data_manager.load_tags()

    @rx.event
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

    @rx.event
    def start_edit_post(self, slug: str):
        post = get_post_by_slug(slug)
        if not post:
            return
        self.blog_slug = post.slug
        self.blog_title = post.title
        self.blog_date = post.date
        self.blog_description = post.description
        self.selected_tags = post.tags
        self.blog_content = post.content
        self.blog_cover_path = post.cover or ""
        self.editing_blog_slug = slug

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

    @rx.event
    def save_post(self):
        if not self.blog_slug or not self.blog_title:
            return rx.window_alert("Slug ve Başlık zorunludur.")
            
        data_manager.save_blog_post(
            slug=self.blog_slug,
            title=self.blog_title,
            date=self.blog_date,
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
        self.editing_blog_slug = ""
        return rx.window_alert("Blog yazısı kaydedildi!")

    @rx.event
    def delete_post(self, slug: str):
        data_manager.delete_blog_post(slug)
        self.load_posts()

    @rx.event
    def cancel_edit_post(self):
        self.blog_slug = ""
        self.blog_title = ""
        self.blog_date = ""
        self.blog_description = ""
        self.selected_tags = []
        self.blog_content = ""
        self.blog_cover_path = ""
        self.editing_blog_slug = ""


class AdminProjectState(rx.State):
    all_admin_projects: list[AdminProjectDict] = []
    
    project_name: str = ""
    project_desc: str = ""
    editing_project_index: int = -1
    
    available_tags: list[str] = []
    selected_tags: list[str] = []
    new_tag_name: str = ""
    
    def set_project_name(self, val: str):
        self.project_name = val
        
    def set_project_desc(self, val: str):
        self.project_desc = val

    def set_new_tag_name(self, val: str):
        self.new_tag_name = val

    @rx.event
    def toggle_tag(self, tag: str):
        if tag in self.selected_tags:
            self.selected_tags = [t for t in self.selected_tags if t != tag]
        else:
            self.selected_tags = self.selected_tags + [tag]

    @rx.event
    def add_new_tag(self):
        if self.new_tag_name:
            data_manager.add_tag(self.new_tag_name)
            if self.new_tag_name not in self.selected_tags:
                self.selected_tags = self.selected_tags + [self.new_tag_name]
            self.new_tag_name = ""
            self.load_tags()

    @rx.event
    def delete_tag(self, tag: str):
        data_manager.delete_tag(tag)
        self.selected_tags = [item for item in self.selected_tags if item != tag]
        self.load_tags()

    @rx.event
    def load_tags(self):
        self.available_tags = data_manager.load_tags()

    @rx.event
    def load_projects(self):
        self.load_tags()
        self.all_admin_projects = data_manager.load_projects()

    @rx.event
    def save_project(self):
        if not self.project_name:
            return rx.window_alert("Proje ismi zorunludur.")
        # If editing an existing project, replace it
        projects = data_manager.load_projects()
        if self.editing_project_index is not None and self.editing_project_index >= 0 and self.editing_project_index < len(projects):
            projects[self.editing_project_index] = {"name": self.project_name, "desc": self.project_desc, "tags": self.selected_tags}
            data_manager.save_projects(projects)
        else:
            data_manager.add_project(self.project_name, self.project_desc, self.selected_tags)

        self.project_name = ""
        self.project_desc = ""
        self.selected_tags = []
        self.editing_project_index = -1

        self.load_projects()

    @rx.event
    def start_edit_project(self, index: int):
        projects = data_manager.load_projects()
        # index may be an integer index or a project dict passed from the UI.
        idx = None
        if isinstance(index, dict):
            # try to find matching project by name+desc
            for i, p in enumerate(projects):
                if p.get("name") == index.get("name") and p.get("desc") == index.get("desc"):
                    idx = i
                    break
        else:
            try:
                idx = int(index)
            except Exception:
                idx = None

        if idx is None:
            return

        if 0 <= idx < len(projects):
            p = projects[idx]
            self.project_name = p.get("name", "")
            self.project_desc = p.get("desc", "")
            self.selected_tags = p.get("tags", []) or []
            self.editing_project_index = idx

    @rx.event
    def cancel_edit_project(self):
        self.project_name = ""
        self.project_desc = ""
        self.selected_tags = []
        self.editing_project_index = -1

    @rx.event
    def delete_project(self, index: int):
        projects = data_manager.load_projects()
        idx = None
        if isinstance(index, dict):
            for i, p in enumerate(projects):
                if p.get("name") == index.get("name") and p.get("desc") == index.get("desc"):
                    idx = i
                    break
        else:
            try:
                idx = int(index)
            except Exception:
                idx = None

        if idx is None:
            return

        data_manager.delete_project(idx)
        self.load_projects()


class AdminChatLogState(rx.State):
    chat_logs: list[ChatSummaryDict] = []
    selected_log: list[ChatMessageDict] = []
    selected_log_name: str = ""
    
    @rx.event
    def load_logs(self):
        logs = data_manager.load_chat_logs()
        self.chat_logs = [
            {
                "filename": log["filename"],
                "date": log.get("timestamp", log["filename"]),
                "summary": "",
                "top_topics": [],
                "message_count": log.get("message_count", 0),
            }
            for log in logs
        ]

    @rx.event
    def view_log(self, filename: str):
        self.selected_log_name = filename
        self.selected_log = data_manager.load_chat_log_messages(filename)

    @rx.event
    def delete_log(self, filename: str):
        data_manager.delete_chat_log(filename)
        if self.selected_log_name == filename:
            self.selected_log_name = ""
            self.selected_log = []
        self.load_logs()

    @rx.event
    def clear_all_logs(self):
        data_manager.clear_all_chat_logs()
        self.chat_logs = []
        self.selected_log = []
        self.selected_log_name = ""
        return rx.window_alert("Tüm sohbet geçmişi silindi.")


class AdminCVState(rx.State):
    cv_filename: str = ""
    cv_url: str = ""
    
    @rx.event
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

    @rx.event
    def delete_cv(self):
        cv_dir = data_manager.CV_DIR
        for f in cv_dir.glob("*.pdf"):
            f.unlink()
        self.cv_url = ""
        self.cv_filename = ""
        return rx.window_alert("CV silindi!")


class AdminEduExpState(rx.State):
    # Deneyim form
    exp_company: str = ""
    exp_role: str = ""
    exp_start: str = ""
    exp_end: str = ""
    exp_desc: str = ""
    exp_tags_selected: list[str] = []
    experiences: list[dict] = []
    exp_tags_options: list[str] = []
    editing_exp_index: int = -1

    # Egitim form
    edu_school: str = ""
    edu_dept: str = ""
    edu_degree: str = ""
    edu_start: str = ""
    edu_end: str = ""
    edu_desc: str = ""
    education: list[dict] = []
    editing_edu_index: int = -1
    # UI helpers
    toast_message: str = ""
    highlighted_exp_index: int = -1
    highlighted_edu_index: int = -1

    def set_exp_company(self, value: str):
        self.exp_company = value

    def set_exp_role(self, value: str):
        self.exp_role = value

    def set_exp_start(self, value: str):
        self.exp_start = value

    def set_exp_end(self, value: str):
        self.exp_end = value

    def set_exp_desc(self, value: str):
        self.exp_desc = value

    def set_edu_school(self, value: str):
        self.edu_school = value

    def set_edu_dept(self, value: str):
        self.edu_dept = value

    def set_edu_degree(self, value: str):
        self.edu_degree = value

    def set_edu_start(self, value: str):
        self.edu_start = value

    def set_edu_end(self, value: str):
        self.edu_end = value

    def set_edu_desc(self, value: str):
        self.edu_desc = value

    @rx.event
    def start_edit_experience(self, index: int):
        if 0 <= index < len(self.experiences):
            e = self.experiences[index]
            self.exp_company = e.get("company", "")
            self.exp_role = e.get("role", "")
            self.exp_start = e.get("start_date", "")
            self.exp_end = e.get("end_date", "")
            self.exp_desc = e.get("description", "")
            self.exp_tags_selected = e.get("tags", []) or []
            self.editing_exp_index = index

    @rx.event
    def cancel_edit_experience(self):
        self.exp_company = self.exp_role = self.exp_start = self.exp_end = self.exp_desc = ""
        self.exp_tags_selected = []
        self.editing_exp_index = -1

    @rx.event
    def start_edit_education(self, index: int):
        if 0 <= index < len(self.education):
            ed = self.education[index]
            self.edu_school = ed.get("school", "")
            self.edu_dept = ed.get("department", "")
            self.edu_degree = ed.get("degree", "")
            self.edu_start = ed.get("start_year", "")
            self.edu_end = ed.get("end_year", "")
            self.edu_desc = ed.get("description", "")
            self.editing_edu_index = index

    @rx.event
    def cancel_edit_education(self):
        self.edu_school = self.edu_dept = self.edu_degree = self.edu_start = self.edu_end = self.edu_desc = ""
        self.editing_edu_index = -1

    @rx.event
    def show_toast(self, message: str):
        self.toast_message = message

    @rx.event
    def clear_toast(self):
        self.toast_message = ""

    @rx.event
    def toggle_exp_tag(self, tag: str):
        if tag in self.exp_tags_selected:
            self.exp_tags_selected = [t for t in self.exp_tags_selected if t != tag]
        else:
            self.exp_tags_selected = self.exp_tags_selected + [tag]

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_education, load_experience, load_tags

        self.education = load_education()
        self.experiences = load_experience()
        tags = load_tags()
        self.exp_tags_options = tags if tags else ["Python", "YOLOv8", "CLIP", "Whisper"]

    @rx.event
    def save_experience(self):
        if not self.exp_company or not self.exp_role:
            return

        from harun_site.utils.data_manager import save_experience

        new_exp = {
            "company": self.exp_company,
            "role": self.exp_role,
            "start_date": self.exp_start,
            "end_date": self.exp_end,
            "description": self.exp_desc,
            "tags": self.exp_tags_selected,
        }
        # If editing, replace existing entry
        if self.editing_exp_index is not None and self.editing_exp_index >= 0 and self.editing_exp_index < len(self.experiences):
            self.experiences[self.editing_exp_index] = new_exp
        else:
            self.experiences = self.experiences + [new_exp]
        save_experience(self.experiences)
        self.exp_company = ""
        self.exp_role = ""
        self.exp_start = ""
        self.exp_end = ""
        self.exp_desc = ""
        self.exp_tags_selected = []
        self.editing_exp_index = -1
        # show non-blocking toast and highlight the saved item
        # highlight last item (or updated index)
        if self.editing_exp_index is not None and self.editing_exp_index >= 0:
            self.highlighted_exp_index = self.editing_exp_index
        else:
            self.highlighted_exp_index = len(self.experiences) - 1
        self.show_toast("Deneyim kaydedildi!")

    @rx.event
    def delete_experience(self, index: int):
        from harun_site.utils.data_manager import save_experience

        self.experiences = [e for i, e in enumerate(self.experiences) if i != index]
        save_experience(self.experiences)

        # reset edit index if necessary
        if self.editing_exp_index == index:
            self.cancel_edit_experience()
        # set a toast
        self.show_toast("Deneyim silindi!")

    @rx.event
    def save_education(self):
        if not self.edu_school or not self.edu_dept:
            return

        from harun_site.utils.data_manager import save_education

        new_edu = {
            "school": self.edu_school,
            "department": self.edu_dept,
            "degree": self.edu_degree,
            "start_year": self.edu_start,
            "end_year": self.edu_end,
            "description": self.edu_desc,
        }
        if self.editing_edu_index is not None and self.editing_edu_index >= 0 and self.editing_edu_index < len(self.education):
            self.education[self.editing_edu_index] = new_edu
        else:
            self.education = self.education + [new_edu]
        save_education(self.education)
        self.edu_school = ""
        self.edu_dept = ""
        self.edu_degree = ""
        self.edu_start = ""
        self.edu_end = ""
        self.edu_desc = ""
        self.editing_edu_index = -1
        if self.editing_edu_index is not None and self.editing_edu_index >= 0:
            self.highlighted_edu_index = self.editing_edu_index
        else:
            self.highlighted_edu_index = len(self.education) - 1
        self.show_toast("Eğitim kaydedildi!")

    @rx.event
    def delete_education(self, index: int):
        from harun_site.utils.data_manager import save_education

        self.education = [e for i, e in enumerate(self.education) if i != index]
        save_education(self.education)

        if self.editing_edu_index == index:
            self.editing_edu_index = -1
        self.show_toast("Eğitim silindi!")

class AdminState(rx.State):
    total_projects: int = 0
    total_blogs: int = 0
    total_chats: int = 0
    active_tab: str = "dashboard"

    @rx.event
    def set_active_tab(self, tab: str):
        self.active_tab = tab

    @rx.event
    def load_admin_data(self):
        # Projects count
        projects = data_manager.load_projects()
        self.total_projects = len(projects)
        
        # Blogs count
        posts = get_all_posts()
        self.total_blogs = len(posts)
        
        # Chats count (Total summaries)
        summary_dir = data_manager.SUMMARIES_DIR
        if summary_dir.exists():
            self.total_chats = len(list(summary_dir.glob("*.json")))
        else:
            self.total_chats = 0
            
        # Also load sub-states
        return [
            AdminBlogState.load_posts,
            AdminProjectState.load_projects,
            AdminChatLogState.load_logs,
            AdminCVState.load_cv,
            AdminCareerState.load_career,
        ]

class AdminCareerState(rx.State):
    
    educations: list[EducationModel] = []
    experiences: list[ExperienceModel] = []
    
    # Form fields
    edu_okul: str = ""
    edu_bolum: str = ""
    edu_baslangic: str = ""
    edu_mezuniyet: str = ""
    edu_detay: str = ""
    
    exp_sirket: str = ""
    exp_pozisyon: str = ""
    exp_sure: str = ""
    exp_aciklama: str = ""

    def set_edu_okul(self, val: str): self.edu_okul = val
    def set_edu_bolum(self, val: str): self.edu_bolum = val
    def set_edu_baslangic(self, val: str): self.edu_baslangic = val
    def set_edu_mezuniyet(self, val: str): self.edu_mezuniyet = val
    def set_edu_detay(self, val: str): self.edu_detay = val
    def set_exp_sirket(self, val: str): self.exp_sirket = val
    def set_exp_pozisyon(self, val: str): self.exp_pozisyon = val
    def set_exp_sure(self, val: str): self.exp_sure = val
    def set_exp_aciklama(self, val: str): self.exp_aciklama = val

    @rx.event
    def load_career(self):
        with rx.session() as session:
            self.educations = session.exec(EducationModel.select()).all()
            self.experiences = session.exec(ExperienceModel.select()).all()

    @rx.event
    def add_education(self):
        with rx.session() as session:
            session.add(
                EducationModel(
                    okul_adi=self.edu_okul,
                    bolum=self.edu_bolum,
                    baslangic_yili=self.edu_baslangic,
                    mezuniyet_yili=self.edu_mezuniyet,
                    detay=self.edu_detay
                )
            )
            session.commit()
        self.edu_okul = ""
        self.edu_bolum = ""
        self.edu_baslangic = ""
        self.edu_mezuniyet = ""
        self.edu_detay = ""
        self.load_career()

    @rx.event
    def delete_education(self, id: int):
        with rx.session() as session:
            edu = session.exec(EducationModel.select().where(EducationModel.id == id)).first()
            if edu:
                session.delete(edu)
                session.commit()
        self.load_career()

    @rx.event
    def add_experience(self):
        with rx.session() as session:
            session.add(
                ExperienceModel(
                    sirket_adi=self.exp_sirket,
                    pozisyon=self.exp_pozisyon,
                    sure=self.exp_sure,
                    aciklama=self.exp_aciklama
                )
            )
            session.commit()
        self.exp_sirket = ""
        self.exp_pozisyon = ""
        self.exp_sure = ""
        self.exp_aciklama = ""
        self.load_career()

    @rx.event
    def delete_experience(self, id: int):
        with rx.session() as session:
            exp = session.exec(ExperienceModel.select().where(ExperienceModel.id == id)).first()
            if exp:
                session.delete(exp)
                session.commit()
        self.load_career()
