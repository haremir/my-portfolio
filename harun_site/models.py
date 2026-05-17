import reflex as rx
from typing import Optional
from sqlmodel import Field

class EducationModel(rx.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    okul_adi: str = ""
    bolum: str = ""
    baslangic_yili: str = ""
    mezuniyet_yili: str = ""
    detay: str = ""

class ExperienceModel(rx.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sirket_adi: str = ""
    pozisyon: str = ""
    sure: str = ""
    aciklama: str = ""
