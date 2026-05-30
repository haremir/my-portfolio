import os
import sys
import reflex as rx
from harun_site.utils import data_manager
from harun_site.utils.project_registry import project_url_from_slug
from harun_site.utils.markdown_parser import get_all_posts, get_post_by_slug
from typing import TypedDict
from sqlmodel import Session, select
from harun_site.models import EducationModel, ExperienceModel, get_engine

def slugify(text: str) -> str:
    tr_map = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
    }
    for tr_char, eng_char in tr_map.items():
        text = text.replace(tr_char, eng_char)
    
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

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
    id: str
    title: str
    slug: str
    url: str
    aliases: list[str]
    name: str
    desc: str
    tags: list[str]

class ChatSummaryDict(TypedDict):
    filename: str
    date: str
    summary: str
    top_topics: list[str]
    message_count: int


# ── Flat TypedDicts for AdminEduExpState ────────────────────────────────────────────
# All fields are plain str / list[str] so Reflex serialises them as
# JSON scalars/arrays — never as nested objects.

class ExperienceEntry(TypedDict):
    company: str
    role: str
    start_date: str
    end_date: str
    description: str
    tags: list[str]

class EducationEntry(TypedDict):
    school: str
    department: str
    degree: str
    start_year: str
    end_year: str
    description: str


# ── Flat TypedDicts for AdminCareerState ──────────────────────────────────────────────
# These replace list[EducationModel] / list[ExperienceModel] in the state.
# SQLModel ORM objects must NEVER be stored as Reflex state vars —
# they are not plain JSON and the Optional[int] id field can become null.

class EducationCareerDict(TypedDict):
    id: int          # always int (0 when freshly created, never None)
    okul_adi: str
    bolum: str
    baslangic_yili: str
    mezuniyet_yili: str
    detay: str

class ExperienceCareerDict(TypedDict):
    id: int
    sirket_adi: str
    pozisyon: str
    sure: str
    aciklama: str

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
    @rx.event
    def set_new_tag_name(self, value: str):
        self.new_tag_name = value

    @rx.event
    def set_project_name(self, value: str):
        self.project_name = value

    @rx.event
    def set_project_desc(self, value: str):
        self.project_desc = value

    @rx.event
    def set_cs_problem(self, value: str):
        self.cs_problem = value

    @rx.event
    def set_cs_architecture(self, value: str):
        self.cs_architecture = value

    @rx.event
    def set_architecture_image(self, value: str):
        self.architecture_image = value

    @rx.event
    def set_cs_stack_reason(self, value: str):
        self.cs_stack_reason = value

    @rx.event
    def set_cs_challenges(self, value: str):
        self.cs_challenges = value

    @rx.event
    def set_cs_learnings(self, value: str):
        self.cs_learnings = value
    is_uploading: bool = False
    editing_blog_slug: str = ""

    # Reflex auto-generates set_<var_name> event handlers for every state var.
    # The manual one-liner setters that were here are identical to the
    # auto-generated versions and were missing @rx.event — removed.

    # Explicit setters (frontend relies on set_<var> handlers when
    # automatic generation is not available).
    @rx.event
    def set_blog_title(self, value: str):
        self.blog_title = value

    @rx.event
    def set_blog_slug(self, value: str):
        self.blog_slug = value

    @rx.event
    def set_blog_date(self, value: str):
        self.blog_date = value

    @rx.event
    def set_blog_description(self, value: str):
        self.blog_description = value

    @rx.event
    def set_blog_tags_str(self, value: str):
        self.blog_tags_str = value

    @rx.event
    def set_blog_content(self, value: str):
        self.blog_content = value

    @rx.event
    def set_new_tag_name(self, value: str):
        self.new_tag_name = value

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

    @rx.event
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
        if not self.blog_title.strip():
            return rx.window_alert("Yazı başlığı zorunludur.")
        
        slug = self.blog_slug.strip()
        if not slug:
            slug = slugify(self.blog_title)
            if not slug:
                return rx.window_alert("Başlıktan geçerli bir URL adı (slug) üretilemedi. Lütfen elle girin.")

        data_manager.save_blog_post(
            slug=slug,
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
    project_slug: str = ""
    project_aliases_str: str = ""
    project_desc: str = ""
    editing_project_index: int = -1
    # Case study fields
    cs_problem: str = ""
    cs_architecture: str = ""
    cs_stack_reason: str = ""
    cs_challenges: str = ""
    cs_learnings: str = ""
    architecture_image: str = ""

    available_tags: list[str] = []
    selected_tags: list[str] = []
    new_tag_name: str = ""

    @rx.event
    def set_project_name(self, value: str):
        self.project_name = value

    @rx.event
    def set_project_slug(self, value: str):
        self.project_slug = value

    @rx.event
    def set_project_aliases_str(self, value: str):
        self.project_aliases_str = value

    @rx.event
    def set_project_desc(self, value: str):
        self.project_desc = value

    @rx.event
    def set_cs_problem(self, value: str):
        self.cs_problem = value

    @rx.event
    def set_cs_architecture(self, value: str):
        self.cs_architecture = value

    @rx.event
    def set_cs_stack_reason(self, value: str):
        self.cs_stack_reason = value

    @rx.event
    def set_cs_challenges(self, value: str):
        self.cs_challenges = value

    @rx.event
    def set_cs_learnings(self, value: str):
        self.cs_learnings = value

    @rx.event
    def set_architecture_image(self, value: str):
        self.architecture_image = value

    @rx.event
    def set_new_tag_name(self, value: str):
        self.new_tag_name = value

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
        # Strip every project to only the fields AdminProjectDict declares.
        # load_projects() returns canonical dicts that include a nested
        # case_study object — that nested dict must never reach the frontend
        # state delta.
        self.all_admin_projects = [
            {
                "id": p.get("id", ""),
                "title": p.get("title", p.get("name", "")),
                "slug": p.get("slug", ""),
                "url": p.get("url", ""),
                "aliases": [str(a) for a in (p.get("aliases") or [])],
                "name": p.get("name", ""),
                "desc": p.get("desc", ""),
                "tags": [str(t) for t in (p.get("tags") or [])],
            }
            for p in data_manager.load_projects()
        ]

    @rx.event
    def save_project(self):
        if not self.project_name.strip():
            return rx.window_alert("Proje başlığı zorunludur.")
        
        slug = self.project_slug.strip()
        if not slug:
            slug = slugify(self.project_name)
            if not slug:
                return rx.window_alert("Başlıktan geçerli bir slug üretilemedi. Lütfen elle girin.")
        
        # If editing an existing project, replace it
        projects = data_manager.load_projects()
        
        if self.project_aliases_str.strip():
            aliases = [alias.strip().lower() for alias in self.project_aliases_str.split(",") if alias.strip()]
        else:
            # Auto-generate aliases based on project name
            aliases = []
            title_clean = self.project_name.strip().lower()
            aliases.append(title_clean)
            
            slugified = slugify(self.project_name)
            if slugified not in aliases:
                aliases.append(slugified)
                
            if ' ' in title_clean or '-' in title_clean:
                no_spaces = title_clean.replace(' ', '').replace('-', '')
                if no_spaces not in aliases:
                    aliases.append(no_spaces)
                with_spaces = title_clean.replace('-', ' ')
                if with_spaces not in aliases:
                    aliases.append(with_spaces)
                    
        # Build case_study dict with both legacy and new keys for compatibility
        case_study = {
            "problem": self.cs_problem or "",
            "architecture": self.cs_architecture or "",
            "stack_reason": self.cs_stack_reason or "",
            "why_this_stack": self.cs_stack_reason or self.cs_stack_reason or "",
            "challenges": self.cs_challenges or "",
            "learnings": self.cs_learnings or "",
            "lessons_learned": self.cs_learnings or self.cs_learnings or "",
            "architecture_image": self.architecture_image or "",
        }

        project_dict = {
            "id": slug,
            "title": self.project_name.strip(),
            "name": self.project_name.strip(),
            "slug": slug,
            "url": project_url_from_slug(slug),
            "aliases": aliases,
            "desc": self.project_desc,
            "tags": self.selected_tags,
            "case_study": case_study,
        }

        if self.editing_project_index is not None and self.editing_project_index >= 0 and self.editing_project_index < len(projects):
            projects[self.editing_project_index] = project_dict
            data_manager.save_projects(projects)
        else:
            projects.append(project_dict)
            data_manager.save_projects(projects)

        self.project_name = ""
        self.project_slug = ""
        self.project_aliases_str = ""
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
            self.project_name = p.get("title", p.get("name", ""))
            self.project_slug = p.get("slug", "")
            self.project_aliases_str = ", ".join(p.get("aliases") or [])
            self.project_desc = p.get("desc", "")
            self.selected_tags = p.get("tags", []) or []
            cs = p.get("case_study", {}) or {}
            # support both legacy and new keys
            self.cs_problem = cs.get("problem", "")
            self.cs_architecture = cs.get("architecture", "")
            self.cs_stack_reason = cs.get("why_this_stack") or cs.get("stack_reason", "")
            self.cs_challenges = cs.get("challenges", "")
            self.cs_learnings = cs.get("lessons_learned") or cs.get("learnings", "")
            self.architecture_image = cs.get("architecture_image", "")
            self.editing_project_index = idx

    @rx.event
    def cancel_edit_project(self):
        self.project_name = ""
        self.project_slug = ""
        self.project_aliases_str = ""
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


class AdminChatAssistantState(rx.State):
    messages: list[ChatMessageDict] = []
    input_value: str = ""
    is_loading: bool = False
    chat_log_count: int = 0
    chat_message_count: int = 0
    status_text: str = "Sohbet kayıtları hakkında soru sorabilirsin."

    @rx.event
    def on_load(self):
        logs = data_manager.load_chat_logs()
        self.chat_log_count = len(logs)
        self.chat_message_count = sum(log.get("message_count", 0) for log in logs)
        if self.chat_log_count == 0:
            self.status_text = (
                "Henüz sohbet kaydı yok. İlk ziyaretçi konuşması sonrası "
                "burada analiz yapabilirsin."
            )
        else:
            self.status_text = (
                f"{self.chat_log_count} kayıt · {self.chat_message_count} mesaj analiz için hazır. "
                "Ziyaretçi davranışı, proje ilgisi veya intent dağılımı hakkında soru sor."
            )
        print(
            f"[ADMIN_ANALYTICS] assistant on_load  "
            f"logs={self.chat_log_count}  messages={self.chat_message_count}"
        )

    @rx.event
    def set_input_value(self, value: str):
        self.input_value = value

    @rx.event
    def handle_keydown(self, key: str, info: rx.event.KeyInputInfo):
        if key == "Enter":
            return self.send_message()

    @rx.event
    def reset_chat(self):
        self.messages = []
        self.input_value = ""
        self.status_text = "Sohbet kayıtları hakkında soru sorabilirsin."

    @rx.event
    async def send_message(self):
        content = self.input_value.strip()
        if not content:
            return

        self.messages = [*self.messages, {"role": "user", "content": content}]
        self.input_value = ""
        self.is_loading = True
        yield

        try:
            from harun_site.utils.data_manager import load_chat_log_messages, load_chat_logs
            from harun_site.utils.groq_client import answer_admin_chat_about_logs

            logs = load_chat_logs()
            payload = []
            for log in logs[:20]:
                messages = load_chat_log_messages(log["filename"])
                user_samples = [
                    m.get("content", "")[:200]
                    for m in messages
                    if m.get("role") == "user"
                ][:4]
                assistant_samples = [
                    m.get("content", "")[:120]
                    for m in messages
                    if m.get("role") == "assistant"
                ][:2]
                payload.append(
                    {
                        "filename": log["filename"],
                        "timestamp": log.get("timestamp", ""),
                        "message_count": log.get("message_count", 0),
                        "user_samples": user_samples,
                        "assistant_samples": assistant_samples,
                    }
                )

            print(
                f"[ADMIN_ANALYTICS] send_message  "
                f"history_turns={len(self.messages)}  log_payload={len(payload)}"
            )

            # Pass the full conversation history — multi-turn memory is handled
            # inside answer_admin_chat_about_logs via proper role-based messages
            answer = await answer_admin_chat_about_logs(self.messages, payload)

        except Exception as exc:
            print(f"[ADMIN_ANALYTICS] send_message error: {exc}")
            answer = (
                "Şu an sohbet kayıtlarını işlerken bir sorun oluştu. "
                "Daha sonra tekrar deneyebilirsin."
            )

        self.messages = [*self.messages, {"role": "assistant", "content": answer}]
        self.is_loading = False
        yield

    @rx.event
    async def shortcut_intent_distribution(self):
        """Kısayol: ziyaretçi intent dağılımını analiz et."""
        if self.is_loading:
            return
        self.is_loading = True
        yield
        try:
            from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages
            from harun_site.utils.groq_client import answer_admin_chat_about_logs

            logs = load_chat_logs()
            payload = []
            for log in logs[:20]:
                messages = load_chat_log_messages(log["filename"])
                user_samples = [m.get("content", "")[:200] for m in messages if m.get("role") == "user"][:4]
                payload.append({"filename": log["filename"], "message_count": log.get("message_count", 0), "user_samples": user_samples})

            question = (
                "Ziyaretçi intent dağılımını analiz et: teknik sorular, kariyer/işe alım, "
                "proje soruları, kişisel sorular, çalışma isteği, AI/tech stack. "
                "Recruiter intent, hiring signals, conversion intent ve technical depth expectations "
                "özellikle görünüyorsa belirt. Her kategoride yaklaşık kaç kayıt var? "
                "Yüzde veya sıklıkla ver. Dominant intent nedir?"
            )
            self.messages = [*self.messages, {"role": "user", "content": question}]
            answer = await answer_admin_chat_about_logs(self.messages, payload)
        except Exception:
            answer = "Intent dağılımı analizi şu an yapılamıyor."

        self.messages = [*self.messages, {"role": "assistant", "content": answer}]
        self.is_loading = False
        yield

    @rx.event
    async def shortcut_top_project(self):
        """Kısayol: en çok ilgi çeken projeyi bul."""
        if self.is_loading:
            return
        self.is_loading = True
        yield
        try:
            from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages
            from harun_site.utils.groq_client import answer_admin_chat_about_logs

            logs = load_chat_logs()
            payload = []
            for log in logs[:20]:
                messages = load_chat_log_messages(log["filename"])
                user_samples = [m.get("content", "")[:200] for m in messages if m.get("role") == "user"][:4]
                payload.append({"filename": log["filename"], "message_count": log.get("message_count", 0), "user_samples": user_samples})

            question = (
                "Hangi proje ziyaretçilerden en fazla soru ve ilgi alıyor? "
                "Proje bazlı karşılaştırma yap. Teknik derinlik beklentisi, trust signals, "
                "recruiter-grade ilgi ve conversion intent hangi projelerde yoğunlaşıyor?"
            )
            self.messages = [*self.messages, {"role": "user", "content": question}]
            answer = await answer_admin_chat_about_logs(self.messages, payload)
        except Exception:
            answer = "Proje analizi şu an yapılamıyor."

        self.messages = [*self.messages, {"role": "assistant", "content": answer}]
        self.is_loading = False
        yield

    @rx.event
    async def shortcut_visitor_patterns(self):
        """Kısayol: ziyaretçi davranış patternlerini çıkar."""
        if self.is_loading:
            return
        self.is_loading = True
        yield
        try:
            from harun_site.utils.data_manager import load_chat_logs, load_chat_log_messages
            from harun_site.utils.groq_client import answer_admin_chat_about_logs

            logs = load_chat_logs()
            payload = []
            for log in logs[:20]:
                messages = load_chat_log_messages(log["filename"])
                user_samples = [m.get("content", "")[:200] for m in messages if m.get("role") == "user"][:4]
                assistant_samples = [m.get("content", "")[:120] for m in messages if m.get("role") == "assistant"][:2]
                payload.append({
                    "filename": log["filename"],
                    "message_count": log.get("message_count", 0),
                    "user_samples": user_samples,
                    "assistant_samples": assistant_samples,
                })

            question = (
                "Ziyaretçi davranış patternlerini analiz et: "
                "En çok hangi soru tipleri tekrar ediyor? "
                "Konuşmalar nasıl başlıyor ve nasıl devam ediyor? "
                "İşe alım niyetli ziyaretçiler hangi sinyalleri veriyor? "
                "Missing content, project trust signals ve repeated visitor patterns var mı?"
            )
            self.messages = [*self.messages, {"role": "user", "content": question}]
            answer = await answer_admin_chat_about_logs(self.messages, payload)
        except Exception:
            answer = "Pattern analizi şu an yapılamıyor."

        self.messages = [*self.messages, {"role": "assistant", "content": answer}]
        self.is_loading = False
        yield


class AdminSuggestionsState(rx.State):
    suggestions: list[str] = []
    new_suggestion: str = ""

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_suggestions

        self.suggestions = load_suggestions()

    @rx.event
    def set_new_suggestion(self, value: str):
        self.new_suggestion = value

    @rx.event
    def add_suggestion(self):
        if not self.new_suggestion.strip():
            return
        if len(self.suggestions) >= 8:
            return
        self.suggestions = self.suggestions + [self.new_suggestion.strip()]
        from harun_site.utils.data_manager import save_suggestions

        save_suggestions(self.suggestions)
        self.new_suggestion = ""

    @rx.event
    def delete_suggestion(self, index: int):
        self.suggestions = [s for i, s in enumerate(self.suggestions) if i != index]
        from harun_site.utils.data_manager import save_suggestions

        save_suggestions(self.suggestions)


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

    @rx.event
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
    experiences: list[ExperienceEntry] = []
    exp_tags_options: list[str] = []
    editing_exp_index: int = -1

    # Egitim form
    edu_school: str = ""
    edu_dept: str = ""
    edu_degree: str = ""
    edu_start: str = ""
    edu_end: str = ""
    edu_desc: str = ""
    education: list[EducationEntry] = []
    editing_edu_index: int = -1
    # UI helpers
    toast_message: str = ""
    highlighted_exp_index: int = -1
    highlighted_edu_index: int = -1

    @rx.event
    def set_exp_company(self, value: str):
        self.exp_company = value

    @rx.event
    def set_exp_role(self, value: str):
        self.exp_role = value

    @rx.event
    def set_exp_start(self, value: str):
        self.exp_start = value

    @rx.event
    def set_exp_end(self, value: str):
        self.exp_end = value

    @rx.event
    def set_exp_desc(self, value: str):
        self.exp_desc = value

    @rx.event
    def set_edu_school(self, value: str):
        self.edu_school = value

    @rx.event
    def set_edu_dept(self, value: str):
        self.edu_dept = value

    @rx.event
    def set_edu_degree(self, value: str):
        self.edu_degree = value

    @rx.event
    def set_edu_start(self, value: str):
        self.edu_start = value

    @rx.event
    def set_edu_end(self, value: str):
        self.edu_end = value

    @rx.event
    def set_edu_desc(self, value: str):
        self.edu_desc = value

    @rx.event
    def set_project_name(self, value: str):
        self.project_name = value

    @rx.event
    def set_project_desc(self, value: str):
        self.project_desc = value

    @rx.event
    def set_cs_problem(self, value: str):
        self.cs_problem = value

    @rx.event
    def set_cs_architecture(self, value: str):
        self.cs_architecture = value

    @rx.event
    def set_cs_stack_reason(self, value: str):
        self.cs_stack_reason = value

    @rx.event
    def set_cs_challenges(self, value: str):
        self.cs_challenges = value

    @rx.event
    def set_cs_learnings(self, value: str):
        self.cs_learnings = value

    @rx.event
    def set_architecture_image(self, value: str):
        self.architecture_image = value

    @rx.event
    def set_new_tag_name(self, value: str):
        self.new_tag_name = value

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
        # Compute highlight BEFORE clearing editing_exp_index so the
        # edit-path (highlighting the updated row) actually fires.
        saved_idx = self.editing_exp_index
        self.editing_exp_index = -1
        if saved_idx is not None and saved_idx >= 0:
            self.highlighted_exp_index = saved_idx
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
        # Compute highlight BEFORE clearing editing_edu_index (same fix
        # as save_experience — the old code always fell to the else branch).
        saved_edu_idx = self.editing_edu_index
        self.editing_edu_index = -1
        if saved_edu_idx is not None and saved_edu_idx >= 0:
            self.highlighted_edu_index = saved_edu_idx
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

    # ── dashboard analytics card ───────────────────────────────────────
    chat_overview: str = "Henüz sohbet özeti yok."
    chat_overview_topics: list[str] = []
    chat_overview_loading: bool = False
    chat_overview_visitor_count: int = 0
    chat_overview_message_count: int = 0
    # enriched analytics fields (populated by load_chat_overview)
    chat_dominant_intent: str = ""       # e.g. "teknik merak"
    chat_top_project: str = ""           # e.g. "CebirX"
    chat_visitor_expectation: str = ""   # one-sentence visitor want
    _overview_loaded: bool = False
    _overview_force_refresh: bool = False

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

        # Chats count (actual chat logs)
        self.total_chats = len(data_manager.load_chat_logs())

        # Also load sub-states
        return [
            AdminBlogState.load_posts,
            AdminProjectState.load_projects,
            AdminChatLogState.load_logs,
            AdminState.load_chat_overview,
            AdminChatAssistantState.on_load,
            AdminSuggestionsState.on_load,
            AdminCVState.load_cv,
            AdminCareerState.load_career,
            AdminSkillsState.on_load,
        ]

    @rx.event
    def refresh_chat_overview(self):
        self._overview_loaded = False
        self._overview_force_refresh = True
        return AdminState.load_chat_overview

    @rx.event
    async def load_chat_overview(self):
        force = self._overview_force_refresh
        self._overview_force_refresh = False
        from harun_site.utils.data_manager import (
            load_chat_log_messages,
            load_chat_logs,
            load_dashboard_overview_cache,
            save_dashboard_overview_cache,
        )
        from harun_site.utils.groq_client import (
            ADMIN_AI_ON_LOAD,
            chat_logs_fingerprint,
            summarize_chat_logs,
        )

        if self._overview_loaded and not force:
            return

        self.chat_overview_loading = True
        yield

        logs = load_chat_logs()
        self.chat_overview_visitor_count = len(logs)
        self.chat_overview_message_count = sum(
            log.get("message_count", 0) for log in logs
        )

        print(
            f"[ADMIN_ANALYTICS] load_chat_overview started  "
            f"total_logs={self.chat_overview_visitor_count}  "
            f"total_messages={self.chat_overview_message_count}"
        )

        if not logs:
            self.chat_overview = "Henüz sohbet kaydı yok."
            self.chat_overview_topics = []
            self.chat_dominant_intent = ""
            self.chat_top_project = ""
            self.chat_visitor_expectation = ""
            self.chat_overview_loading = False
            print("[ADMIN_ANALYTICS] no logs — skipping AI summarisation")
            self._overview_loaded = True
            yield
            return

        fingerprint = chat_logs_fingerprint(logs)
        if not force:
            cached = load_dashboard_overview_cache(fingerprint)
            if cached:
                self._apply_overview(cached)
                self.chat_overview_loading = False
                self._overview_loaded = True
                print("[ADMIN_ANALYTICS] overview from cache", file=sys.stderr)
                yield
                return

        if not ADMIN_AI_ON_LOAD and not force:
            self._apply_overview_fallback()
            self.chat_overview_loading = False
            self._overview_loaded = True
            print("[ADMIN_ANALYTICS] AI skipped (ADMIN_AI_ON_LOAD=false)", file=sys.stderr)
            yield
            return

        # Build a richer payload: include both user and assistant samples
        payload = []
        for log in logs[:15]:
            messages = load_chat_log_messages(log["filename"])
            user_samples = [
                m.get("content", "")[:200]
                for m in messages
                if m.get("role") == "user"
            ][:4]
            assistant_samples = [
                m.get("content", "")[:120]
                for m in messages
                if m.get("role") == "assistant"
            ][:2]
            payload.append(
                {
                    "filename": log["filename"],
                    "timestamp": log.get("timestamp", ""),
                    "message_count": log.get("message_count", 0),
                    "sample_queries": user_samples,   # kept for backward compat
                    "user_samples": user_samples,
                    "assistant_samples": assistant_samples,
                }
            )

        try:
            overview = await summarize_chat_logs(payload)
            if overview:
                save_dashboard_overview_cache(fingerprint, overview)
                self._apply_overview(overview)
                print(
                    f"[ADMIN_ANALYTICS] summary ready  "
                    f"dominant_intent={self.chat_dominant_intent!r}  "
                    f"top_project={self.chat_top_project!r}",
                    file=sys.stderr,
                )
            else:
                self._apply_overview_fallback()
        except Exception as exc:
            print(f"[ADMIN_ANALYTICS] AI summarisation failed: {exc}", file=sys.stderr)
            self._apply_overview_fallback()

        self.chat_overview_loading = False
        self._overview_loaded = True
        yield

    def _apply_overview(self, overview: dict):
        self.chat_overview = overview.get("summary", self.chat_overview)
        self.chat_overview_topics = overview.get("top_topics", []) or []
        self.chat_dominant_intent = overview.get("dominant_intent", "")
        self.chat_top_project = overview.get("top_project", "")
        self.chat_visitor_expectation = overview.get("visitor_expectation", "")

    def _apply_overview_fallback(self):
        self.chat_overview = (
            f"{self.chat_overview_visitor_count} sohbet kaydı · "
            f"{self.chat_overview_message_count} mesaj. "
            "Özet için dashboard kartında yenile veya AI kotası dolunca bekleyin."
        )
        self.chat_overview_topics = ["teknik sorular", "proje analizi", "kariyer"]
        self.chat_dominant_intent = "teknik merak"
        self.chat_top_project = ""
        self.chat_visitor_expectation = ""

class AdminCareerState(rx.State):

    # ── Flat TypedDict lists — SQLModel ORM objects removed from state. ──────
    educations: list[EducationCareerDict] = []
    experiences: list[ExperienceCareerDict] = []

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


    @rx.event
    def load_career(self):
        """Load all education and experience rows from SQLite.

        Uses Session(get_engine()) directly — rx.session() relies on the
        deprecated rx.Model layer (removed in Reflex 1.0).  The try/except
        ensures the admin panel never crashes when the DB file is absent
        or the tables have not yet been created.
        """
        import sys
        try:
            with Session(get_engine()) as session:
                edu_models = session.exec(select(EducationModel)).all()
                exp_models = session.exec(select(ExperienceModel)).all()
            # Flatten ORM instances to plain TypedDicts — Optional[int] id
            # is coerced to int (0 if None) so the frontend never sees null.
            self.educations = [
                {
                    "id": int(e.id or 0),
                    "okul_adi": e.okul_adi or "",
                    "bolum": e.bolum or "",
                    "baslangic_yili": e.baslangic_yili or "",
                    "mezuniyet_yili": e.mezuniyet_yili or "",
                    "detay": e.detay or "",
                }
                for e in edu_models
            ]
            self.experiences = [
                {
                    "id": int(e.id or 0),
                    "sirket_adi": e.sirket_adi or "",
                    "pozisyon": e.pozisyon or "",
                    "sure": e.sure or "",
                    "aciklama": e.aciklama or "",
                }
                for e in exp_models
            ]
        except Exception as exc:
            print(
                f"[AdminCareerState.load_career] DB error: {type(exc).__name__}: {exc}\n"
                "  Tables may not exist yet — run 'alembic upgrade head'.",
                file=sys.stderr,
            )
            self.educations = []
            self.experiences = []

    @rx.event
    def add_education(self):
        import sys
        try:
            with Session(get_engine()) as session:
                session.add(
                    EducationModel(
                        okul_adi=self.edu_okul,
                        bolum=self.edu_bolum,
                        baslangic_yili=self.edu_baslangic,
                        mezuniyet_yili=self.edu_mezuniyet,
                        detay=self.edu_detay,
                    )
                )
                session.commit()
        except Exception as exc:
            print(f"[AdminCareerState.add_education] {type(exc).__name__}: {exc}", file=sys.stderr)
            return
        self.edu_okul = ""
        self.edu_bolum = ""
        self.edu_baslangic = ""
        self.edu_mezuniyet = ""
        self.edu_detay = ""
        self.load_career()

    @rx.event
    def delete_education(self, id: int):
        import sys
        try:
            with Session(get_engine()) as session:
                edu = session.exec(
                    select(EducationModel).where(EducationModel.id == id)
                ).first()
                if edu:
                    session.delete(edu)
                    session.commit()
        except Exception as exc:
            print(f"[AdminCareerState.delete_education] {type(exc).__name__}: {exc}", file=sys.stderr)
            return
        self.load_career()

    @rx.event
    def add_experience(self):
        import sys
        try:
            with Session(get_engine()) as session:
                session.add(
                    ExperienceModel(
                        sirket_adi=self.exp_sirket,
                        pozisyon=self.exp_pozisyon,
                        sure=self.exp_sure,
                        aciklama=self.exp_aciklama,
                    )
                )
                session.commit()
        except Exception as exc:
            print(f"[AdminCareerState.add_experience] {type(exc).__name__}: {exc}", file=sys.stderr)
            return
        self.exp_sirket = ""
        self.exp_pozisyon = ""
        self.exp_sure = ""
        self.exp_aciklama = ""
        self.load_career()

    @rx.event
    def delete_experience(self, id: int):
        import sys
        try:
            with Session(get_engine()) as session:
                exp = session.exec(
                    select(ExperienceModel).where(ExperienceModel.id == id)
                ).first()
                if exp:
                    session.delete(exp)
                    session.commit()
        except Exception as exc:
            print(f"[AdminCareerState.delete_experience] {type(exc).__name__}: {exc}", file=sys.stderr)
            return
        self.load_career()


class SkillCategoryDict(TypedDict):
    category: str
    skills: list[str]


class AdminSkillsState(rx.State):
    skills_list: list[SkillCategoryDict] = []
    category: str = ""
    skills_str: str = ""
    editing_index: int = -1

    @rx.event
    def set_category(self, value: str):
        self.category = value

    @rx.event
    def set_skills_str(self, value: str):
        self.skills_str = value

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import load_skills
        self.skills_list = load_skills()

    @rx.event
    def save_category(self):
        if not self.category.strip():
            return rx.window_alert("Kategori adı zorunludur.")
        
        # parse skills_str by comma
        skills_parsed = [s.strip() for s in self.skills_str.split(",") if s.strip()]
        
        new_cat = {
            "category": self.category.strip(),
            "skills": skills_parsed
        }
        
        from harun_site.utils.data_manager import save_skills
        
        current_list = list(self.skills_list)
        if 0 <= self.editing_index < len(current_list):
            current_list[self.editing_index] = new_cat
        else:
            current_list.append(new_cat)
            
        self.skills_list = current_list
        save_skills(self.skills_list)
        
        # reset
        self.category = ""
        self.skills_str = ""
        self.editing_index = -1
        
    @rx.event
    def start_edit(self, index: int):
        if 0 <= index < len(self.skills_list):
            cat = self.skills_list[index]
            self.category = cat.get("category", "")
            self.skills_str = ", ".join(cat.get("skills", []))
            self.editing_index = index

    @rx.event
    def cancel_edit(self):
        self.category = ""
        self.skills_str = ""
        self.editing_index = -1

    @rx.event
    def delete_category(self, index: int):
        if 0 <= index < len(self.skills_list):
            self.skills_list = [c for i, c in enumerate(self.skills_list) if i != index]
            from harun_site.utils.data_manager import save_skills
            save_skills(self.skills_list)
            if self.editing_index == index:
                self.cancel_edit()
