import reflex as rx
from typing import TypedDict


class EducationDict(TypedDict):
    school: str
    department: str
    department_en: str
    degree: str
    degree_en: str
    start_year: str
    end_year: str
    description: str
    description_en: str


class ExperienceDict(TypedDict):
    company: str
    role: str
    role_en: str
    start_date: str
    start_date_en: str
    end_date: str
    end_date_en: str
    description: str
    description_en: str
    tags: list[str]


class SkillCategoryDict(TypedDict):
    category: str
    category_en: str
    skills: list[str]


def localize_date_string(date_str: str, lang: str) -> str:
    if not date_str:
        return ""
    if lang != "en":
        return date_str
    
    mapping = {
        "OCAK": "JANUARY", "SUBAT": "FEBRUARY", "ŞUBAT": "FEBRUARY", "MART": "MARCH",
        "NISAN": "APRIL", "NİSAN": "APRIL", "MAYIS": "MAY", "HAZIRAN": "JUNE",
        "HAZİRAN": "JUNE", "TEMMUZ": "JULY", "AGUSTOS": "AUGUST", "AĞUSTOS": "AUGUST",
        "EYLUL": "SEPTEMBER", "EYLÜL": "SEPTEMBER", "EKIM": "OCTOBER", "EKİM": "OCTOBER",
        "KASIM": "NOVEMBER", "ARALIK": "DECEMBER", "DEVAM": "PRESENT", "devam": "PRESENT",
        "Devam": "PRESENT"
    }
    
    val = date_str
    import re
    for tr, en in mapping.items():
        val = re.sub(rf"\b{tr}\b", en, val, flags=re.IGNORECASE)
    return val

class AboutState(rx.State):
    education: list[EducationDict] = []
    experience: list[ExperienceDict] = []
    skills: list[SkillCategoryDict] = []
    cv_path: str = ""

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import (
            load_education,
            load_experience,
            get_cv_path,
            load_skills,
        )

        raw_edu = load_education()
        self.education = [
            {
                "school": e.get("school", ""),
                "department": e.get("department", ""),
                "department_en": e.get("department_en", e.get("department", "")),
                "degree": e.get("degree", ""),
                "degree_en": e.get("degree_en", e.get("degree", "")),
                "start_year": e.get("start_year", ""),
                "end_year": e.get("end_year", ""),
                "description": e.get("description", ""),
                "description_en": e.get("description_en", e.get("description", "")),
            }
            for e in raw_edu
        ]

        raw_exp = load_experience()
        self.experience = [
            {
                "company": e.get("company", ""),
                "role": e.get("role", ""),
                "role_en": e.get("role_en", e.get("role", "")),
                "start_date": e.get("start_date", ""),
                "start_date_en": localize_date_string(e.get("start_date", ""), "en"),
                "end_date": e.get("end_date", ""),
                "end_date_en": localize_date_string(e.get("end_date", ""), "en"),
                "description": e.get("description", ""),
                "description_en": e.get("description_en", e.get("description", "")),
                "tags": [str(t) for t in (e.get("tags") or [])],
            }
            for e in raw_exp
        ]

        self.skills = load_skills()
        self.cv_path = get_cv_path()
