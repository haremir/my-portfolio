# Backend Implementation Contracts

Bu dosya, frontend'de kullanılan mock verilerin backend'de nasıl implement edileceğini ve API contract'larını tanımlar.

## 1. Veri Modelleri

### Contact Model
```python
class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    subject: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "unread"  # unread, read, replied
```

### Project Model  
```python
class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    technologies: List[str]
    image_url: str
    demo_url: Optional[str]
    code_url: Optional[str]
    category: str
    status: str  # "Tamamlandı", "Geliştirme aşamasında"
    featured: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Experience Model
```python
class Experience(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company: str
    position: str
    duration: str
    description: str
    achievements: List[str]
    order: int  # For sorting
```

### Skill Model
```python
class Skill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    level: int  # 0-100
    category: str  # "technical", "soft"
```

## 2. API Endpoints

### Contact Endpoints
- `POST /api/contact` - İletişim formu gönderimi
- `GET /api/contacts` - Admin için tüm mesajları listele
- `PUT /api/contact/{id}` - Mesaj durumunu güncelle
- `DELETE /api/contact/{id}` - Mesajı sil

### Project Endpoints  
- `GET /api/projects` - Tüm projeleri listele (query params: featured, category)
- `GET /api/projects/{id}` - Tek proje detayı
- `POST /api/projects` - Yeni proje ekle (admin)
- `PUT /api/projects/{id}` - Proje güncelle (admin)
- `DELETE /api/projects/{id}` - Proje sil (admin)

### Resume Endpoints
- `GET /api/experience` - Tüm deneyimleri listele
- `GET /api/skills` - Tüm becerileri listele
- `POST /api/experience` - Yeni deneyim ekle (admin)
- `PUT /api/experience/{id}` - Deneyim güncelle (admin)
- `POST /api/skills` - Yeni beceri ekle (admin)
- `PUT /api/skills/{id}` - Beceri güncelle (admin)

### Analytics Endpoints
- `POST /api/analytics/visit` - Sayfa ziyareti kaydet
- `GET /api/analytics/stats` - Ziyaret istatistikleri (admin)

## 3. Mock Data'dan Backend'e Geçiş Planı

### Şu Anda Mock'ta Olan Veriler:
1. **portfolioData.personal** → Hardcoded kalacak (config dosyası)
2. **portfolioData.projects** → MongoDB'de `projects` collection'ında
3. **portfolioData.resume.experience** → MongoDB'de `experiences` collection'ında  
4. **portfolioData.resume.skills** → MongoDB'de `skills` collection'ında
5. **portfolioData.contact.services** → Hardcoded kalacak
6. **portfolioData.contact.social** → Hardcoded kalacak

### Dinamik Olacak Veriler:
- Contact form submissions → `contacts` collection
- Project CRUD operations → `projects` collection  
- Experience CRUD operations → `experiences` collection
- Skills CRUD operations → `skills` collection
- Visit analytics → `analytics` collection

## 4. Frontend Entegrasyon Değişiklikleri

### İletişim Formu (ContactPage.jsx)
```javascript
// Mock'tan değişecek:
const handleSubmit = async (e) => {
  e.preventDefault();
  setIsSubmitting(true);
  
  try {
    const response = await axios.post(`${API}/contact`, formData);
    if (response.status === 201) {
      toast({
        title: "Mesaj Gönderildi!",
        description: "En kısa sürede size dönüş yapacağım.",
      });
      setFormData({ name: '', email: '', subject: '', message: '' });
    }
  } catch (error) {
    toast({
      title: "Hata",
      description: "Mesaj gönderilemedi. Lütfen tekrar deneyin.",
      variant: "destructive"
    });
  } finally {
    setIsSubmitting(false);
  }
};
```

### Projeler (ProjectsPage.jsx)
```javascript
// Mock data yerine API'den veri çekme:
const [projects, setProjects] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Projeler yüklenirken hata:', error);
    } finally {
      setLoading(false);
    }
  };
  
  fetchProjects();
}, []);
```

### Ana Sayfa (HomePage.jsx)
```javascript
// Featured projeler için API çağrısı:
useEffect(() => {
  const fetchFeaturedProjects = async () => {
    try {
      const response = await axios.get(`${API}/projects?featured=true`);
      setFeaturedProjects(response.data);
    } catch (error) {
      console.error('Öne çıkan projeler yüklenirken hata:', error);
    }
  };
  
  fetchFeaturedProjects();
}, []);
```

## 5. Veritabanı Seed Data

Backend implement edildiğinde, mevcut mock data'yı veritabanına seed etmek için:

### Projects Seed:
- GameGain - Oyun Geliri Tahmini
- Fraud Eye - Dolandırıcılık Tespiti  
- ScoutMaster - Futbol Oyuncusu Analizi
- CineMatch - Film Öneri Sistemi
- AltinEx - Altın Takip Uygulaması
- Real Estate Forecast

### Experience Seed:
- Serbest Çalışan (2023 - Devam ediyor)
- ETÜ Bilgisayar Mühendisliği Öğrencisi (2021 - Devam ediyor)

### Skills Seed:
- Technical: Python (95%), Machine Learning (90%), Data Analysis (90%), vb.
- Soft: Analitik Düşünme, Problem Çözme, Takım Çalışması, vb.

## 6. Güvenlik ve Doğrulama

- Contact form için rate limiting (her IP'den dakikada max 2 mesaj)
- Email validation ve sanitization
- XSS protection için input sanitization
- CORS ayarları
- Request body size limits

## 7. Error Handling

- 400: Bad Request (validation errors)
- 404: Not Found (resource doesn't exist)  
- 429: Too Many Requests (rate limiting)
- 500: Internal Server Error

Her endpoint için consistent error response format:
```json
{
  "error": true,
  "message": "Error description",
  "details": "Additional error details if needed"
}
```