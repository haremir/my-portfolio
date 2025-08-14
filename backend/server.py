from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Portfolio API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models for Portfolio
class ContactMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="unread")  # unread, read, replied

class ContactMessageCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr  
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=1000)

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    technologies: List[str]
    image_url: str
    demo_url: Optional[str] = None
    code_url: Optional[str] = None
    category: str
    status: str  # "Tamamlandı", "Geliştirme aşamasında"
    featured: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Experience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    position: str
    duration: str
    description: str
    achievements: List[str]
    order: int = 0

class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    level: int = Field(..., ge=0, le=100)  # 0-100 range
    category: str  # "technical", "soft"

class VisitLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Legacy model for backward compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


# Contact Endpoints
@api_router.post("/contact", response_model=ContactMessage)
async def create_contact_message(contact_data: ContactMessageCreate):
    """İletişim formu mesajı gönder"""
    try:
        contact_dict = contact_data.dict()
        contact_obj = ContactMessage(**contact_dict)
        
        # Save to database
        result = await db.contacts.insert_one(contact_obj.dict())
        
        if result.inserted_id:
            logger.info(f"New contact message from {contact_obj.email}")
            return contact_obj
        else:
            raise HTTPException(status_code=500, detail="Mesaj kaydedilemedi")
            
    except Exception as e:
        logger.error(f"Contact message error: {str(e)}")
        raise HTTPException(status_code=500, detail="Mesaj gönderimi sırasında hata oluştu")

@api_router.get("/contacts", response_model=List[ContactMessage])
async def get_contact_messages(skip: int = 0, limit: int = 50):
    """Tüm iletişim mesajlarını getir (Admin)"""
    try:
        contacts = await db.contacts.find().sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return [ContactMessage(**contact) for contact in contacts]
    except Exception as e:
        logger.error(f"Get contacts error: {str(e)}")
        raise HTTPException(status_code=500, detail="Mesajlar alınamadı")


# Project Endpoints
@api_router.get("/projects", response_model=List[Project])
async def get_projects(featured: Optional[bool] = None, category: Optional[str] = None):
    """Projeleri listele"""
    try:
        query = {}
        if featured is not None:
            query["featured"] = featured
        if category and category != "Tümü":
            query["category"] = category
            
        projects = await db.projects.find(query).sort("created_at", -1).to_list(100)
        return [Project(**project) for project in projects]
    except Exception as e:
        logger.error(f"Get projects error: {str(e)}")
        raise HTTPException(status_code=500, detail="Projeler alınamadı")

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Tek proje detayı"""
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Proje bulunamadı")
        return Project(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project error: {str(e)}")
        raise HTTPException(status_code=500, detail="Proje alınamadı")


# Experience Endpoints  
@api_router.get("/experience", response_model=List[Experience])
async def get_experiences():
    """Deneyimleri listele"""
    try:
        experiences = await db.experiences.find().sort("order", 1).to_list(100)
        return [Experience(**exp) for exp in experiences]
    except Exception as e:
        logger.error(f"Get experiences error: {str(e)}")
        raise HTTPException(status_code=500, detail="Deneyimler alınamadı")


# Skills Endpoints
@api_router.get("/skills", response_model=List[Skill])
async def get_skills(category: Optional[str] = None):
    """Becerileri listele"""
    try:
        query = {}
        if category:
            query["category"] = category
            
        skills = await db.skills.find(query).sort("level", -1).to_list(100)
        return [Skill(**skill) for skill in skills]
    except Exception as e:
        logger.error(f"Get skills error: {str(e)}")
        raise HTTPException(status_code=500, detail="Beceriler alınamadı")


# Analytics Endpoints
@api_router.post("/analytics/visit")
async def log_visit(visit_data: dict):
    """Sayfa ziyareti kaydet"""
    try:
        visit_obj = VisitLog(
            page=visit_data.get("page", "/"),
            ip_address=visit_data.get("ip_address"),
            user_agent=visit_data.get("user_agent")
        )
        
        await db.analytics.insert_one(visit_obj.dict())
        return {"success": True}
    except Exception as e:
        logger.error(f"Visit log error: {str(e)}")
        # Don't raise error for analytics, just log it
        return {"success": False}

@api_router.get("/analytics/stats")
async def get_analytics_stats():
    """Ziyaret istatistikleri (Admin)"""
    try:
        total_visits = await db.analytics.count_documents({})
        
        # Son 7 günlük ziyaretler
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_visits = await db.analytics.count_documents({
            "timestamp": {"$gte": week_ago}
        })
        
        # Sayfa bazlı istatistikler
        page_stats = await db.analytics.aggregate([
            {"$group": {"_id": "$page", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]).to_list(10)
        
        return {
            "total_visits": total_visits,
            "recent_visits": recent_visits,
            "page_stats": page_stats
        }
    except Exception as e:
        logger.error(f"Get analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="İstatistikler alınamadı")


# Legacy endpoints for backward compatibility
@api_router.get("/")
async def root():
    return {"message": "Portfolio API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# Include the router in the main app
app.include_router(api_router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
