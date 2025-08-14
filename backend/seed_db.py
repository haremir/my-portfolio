#!/usr/bin/env python3
"""
Portfolio Database Seed Script
Bu script veritabanına initial data ekler
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Load environment variables
load_dotenv('.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL'] 
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]


async def seed_projects():
    """Projeleri seed et"""
    projects = [
        {
            "id": str(uuid.uuid4()),
            "title": "GameGain - Oyun Geliri Tahmini",
            "description": "İlk 15 günlük oyuncu davranışlarını analiz ederek 90 günlük oyun gelirini tahmin eden makine öğrenmesi modeli. Kullanıcı seviyesinde gelir tahmini için etkili veri analizi ve modelleme teknikleri kullanılmıştır.",
            "technologies": ["Python", "Pandas", "Scikit-learn", "XGBoost", "Matplotlib"],
            "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=500",
            "demo_url": "https://github.com/haremir/GameGain-",
            "code_url": "https://github.com/haremir/GameGain-",
            "category": "Machine Learning",
            "status": "Tamamlandı",
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Fraud Eye - Dolandırıcılık Tespiti",
            "description": "Kredi kartı dolandırıcılığını tespit etmek için geliştirilmiş makine öğrenmesi sistemi. Anomali tespiti ve sınıflandırma algoritmaları kullanılmıştır.",
            "technologies": ["Python", "TensorFlow", "Pandas", "Seaborn", "Scikit-learn"],
            "image_url": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=500",
            "demo_url": "https://github.com/haremir/fraud_eye",
            "code_url": "https://github.com/haremir/fraud_eye",
            "category": "Fraud Detection",
            "status": "Tamamlandı",
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "ScoutMaster - Futbol Oyuncusu Analizi",
            "description": "Futbol oyuncularının becerilerini ve piyasa değerlerini analiz ederek gelecek sezon değer artışlarını tahmin eden sistem. Spor analitiği ve prediktif modelleme içerir.",
            "technologies": ["Python", "Jupyter", "Pandas", "Matplotlib", "Seaborn"],
            "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500",
            "demo_url": "https://github.com/haremir/ScoutMaster",
            "code_url": "https://github.com/haremir/ScoutMaster",
            "category": "Sports Analytics",
            "status": "Tamamlandı",
            "featured": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "CineMatch - Film Öneri Sistemi",
            "description": "Collaborative filtering kullanarak kişiselleştirilmiş film önerileri sunan sistem. Kullanıcı davranışlarını analiz ederek benzer beğenilere sahip kullanıcıları bulur.",
            "technologies": ["Python", "Jupyter", "Pandas", "NumPy", "Scikit-learn"],
            "image_url": "https://images.unsplash.com/photo-1489599317698-2f4e7bac6adb?w=500",
            "demo_url": "https://github.com/haremir/CineMatch",
            "code_url": "https://github.com/haremir/CineMatch",
            "category": "Recommendation System",
            "status": "Tamamlandı",
            "featured": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "AltinEx - Altın Takip Uygulaması",
            "description": "Altın fiyatlarını takip eden finansal analiz uygulaması. Gerçek zamanlı veri analizi ve görselleştirme özellikleri içerir.",
            "technologies": ["Python", "Flask", "SQLite", "Matplotlib"],
            "image_url": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=500",
            "demo_url": "https://github.com/haremir/AltinEx",
            "code_url": "https://github.com/haremir/AltinEx",
            "category": "Fintech",
            "status": "Tamamlandı",
            "featured": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Real Estate Forecast",
            "description": "Emlak fiyat tahmin modeli - ACUNMEDYA ev ödevi olarak geliştirildi. Gayrimenkul piyasası analizi ve fiyat tahmin algoritmaları içerir.",
            "technologies": ["Python", "Jupyter", "Pandas", "Scikit-learn"],
            "image_url": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=500",
            "demo_url": "https://github.com/haremir/real_estate_forecast",
            "code_url": "https://github.com/haremir/real_estate_forecast",
            "category": "Real Estate",
            "status": "Tamamlandı",
            "featured": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    # Clear existing projects
    await db.projects.delete_many({})
    
    # Insert new projects
    result = await db.projects.insert_many(projects)
    print(f"✅ {len(result.inserted_ids)} proje eklendi")


async def seed_experiences():
    """Deneyimleri seed et"""
    experiences = [
        {
            "id": str(uuid.uuid4()),
            "company": "Serbest Çalışan",
            "position": "Veri Bilimci & AI Geliştirici",
            "duration": "2023 - Devam ediyor",
            "description": "Çeşitli projeler üzerinde çalışarak makine öğrenmesi ve veri analizi alanında deneyim kazanıyorum.",
            "achievements": [
                "6+ makine öğrenmesi projesinin başarıyla tamamlanması",
                "Dolandırıcılık tespiti algoritması geliştirilmesi", 
                "Oyun geliri tahmin modelinin oluşturulması",
                "GitHub'da Pull Shark achievement kazanılması"
            ],
            "order": 1
        },
        {
            "id": str(uuid.uuid4()),
            "company": "Eskişehir Teknik Üniversitesi",
            "position": "Bilgisayar Mühendisliği Öğrencisi", 
            "duration": "2021 - Devam ediyor",
            "description": "Akademik eğitimim süresince veri yapıları, algoritmalar ve makine öğrenmesi konularında derinlemesine bilgi ediniyorum.",
            "achievements": [
                "Başarılı akademik performans",
                "Veri bilimi projeleri geliştirme",
                "Takım çalışması ve proje yönetimi deneyimi"
            ],
            "order": 2
        }
    ]
    
    # Clear existing experiences
    await db.experiences.delete_many({})
    
    # Insert new experiences
    result = await db.experiences.insert_many(experiences)
    print(f"✅ {len(result.inserted_ids)} deneyim eklendi")


async def seed_skills():
    """Becerileri seed et"""
    skills = [
        # Technical Skills
        {"id": str(uuid.uuid4()), "name": "Python", "level": 95, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Machine Learning", "level": 90, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Data Analysis", "level": 90, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "TensorFlow", "level": 85, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "PyTorch", "level": 85, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Pandas", "level": 95, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Scikit-learn", "level": 90, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "SQL", "level": 80, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Git", "level": 85, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Jupyter", "level": 95, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "OpenCV", "level": 75, "category": "technical"},
        {"id": str(uuid.uuid4()), "name": "Flask", "level": 80, "category": "technical"},
        
        # Soft Skills
        {"id": str(uuid.uuid4()), "name": "Analitik Düşünme", "level": 95, "category": "soft"},
        {"id": str(uuid.uuid4()), "name": "Problem Çözme", "level": 90, "category": "soft"},
        {"id": str(uuid.uuid4()), "name": "Takım Çalışması", "level": 85, "category": "soft"},
        {"id": str(uuid.uuid4()), "name": "Proje Yönetimi", "level": 80, "category": "soft"},
        {"id": str(uuid.uuid4()), "name": "İletişim", "level": 85, "category": "soft"},
        {"id": str(uuid.uuid4()), "name": "Araştırma", "level": 90, "category": "soft"}
    ]
    
    # Clear existing skills
    await db.skills.delete_many({})
    
    # Insert new skills
    result = await db.skills.insert_many(skills)
    print(f"✅ {len(result.inserted_ids)} beceri eklendi")


async def main():
    """Ana seeding fonksiyonu"""
    print("🌱 Portfolio veritabanı seeding başlıyor...")
    
    try:
        await seed_projects()
        await seed_experiences() 
        await seed_skills()
        
        print("🎉 Tüm seed işlemleri başarıyla tamamlandı!")
        
    except Exception as e:
        print(f"❌ Seed işlemi sırasında hata: {str(e)}")
    
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())