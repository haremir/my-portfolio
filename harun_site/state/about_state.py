import reflex as rx
from typing import TypedDict


class EducationDict(TypedDict):
    school: str
    department: str
    degree: str
    start_year: str
    end_year: str
    description: str


class ExperienceDict(TypedDict):
    company: str
    role: str
    start_date: str
    end_date: str
    description: str
    tags: list[str]


class AboutState(rx.State):
    education: list[EducationDict] = []
    experience: list[ExperienceDict] = []
    cv_path: str = ""

    @rx.event
    def on_load(self):
        from harun_site.utils.data_manager import (
            load_education,
            load_experience,
            get_cv_path,
        )

        self.education = load_education()
        self.experience = load_experience()
        self.cv_path = get_cv_path()
