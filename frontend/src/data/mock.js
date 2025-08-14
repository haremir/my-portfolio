// Mock data for Harun Emirhan Bostancı's portfolio website

export const portfolioData = {
    // Personal information
    personal: {
      name: "Harun Emirhan Bostancı",
      title: "Veri Bilimci & AI Geliştirici",
      subtitle: "Modern makine öğrenmesi teknikleri ile yaratıcı çözümler geliştiren tutkulu bir veri bilimci",
      email: "harunemirhanbostanci@gmail.com",
      phone: "+90 555 123 45 67",
      location: "İstanbul, Türkiye",
      bio: "ETÜ Bilgisayar Mühendisliği öğrencisi olarak veri bilimi ve yapay zeka alanında kendimi geliştiriyorum. Python, TensorFlow ve PyTorch ile makine öğrenmesi projeleri geliştiriyorum. Özellikle dolandırıcılık tespiti, oyun geliri tahmini ve spor analitiği alanlarında deneyim sahibiyim."
    },
  
    // Navigation menu
    navigation: [
      { name: "Ana Sayfa", path: "/", active: true },
      { name: "Projeler", path: "/projeler", active: false },
      { name: "Özgeçmiş", path: "/ozgecmis", active: false },
      { name: "İletişim", path: "/iletisim", active: false }
    ],
  
    // Featured projects for homepage - Real projects from GitHub
    featuredProjects: [
      {
        id: 1,
        title: "GameGain - Oyun Geliri Tahmini",
        description: "İlk 15 günlük oyuncu davranışlarını analiz ederek 90 günlük oyun gelirini tahmin eden makine öğrenmesi modeli",
        technologies: ["Python", "Pandas", "Scikit-learn", "XGBoost"],
        image: "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=500",
        demoUrl: "https://github.com/haremir/GameGain-",
        codeUrl: "https://github.com/haremir/GameGain-",
        featured: true
      },
      {
        id: 2,
        title: "Fraud Eye - Dolandırıcılık Tespiti",
        description: "Kredi kartı dolandırıcılığını tespit etmek için geliştirilmiş makine öğrenmesi sistemi",
        technologies: ["Python", "TensorFlow", "Pandas", "Seaborn"],
        image: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=500",
        demoUrl: "https://github.com/haremir/fraud_eye",
        codeUrl: "https://github.com/haremir/fraud_eye",
        featured: true
      },
      {
        id: 3,
        title: "ScoutMaster - Futbol Oyuncusu Değer Analizi",
        description: "Futbol oyuncularının becerilerini ve piyasa değerlerini analiz ederek gelecek sezon değer artışlarını tahmin eden sistem",
        technologies: ["Python", "Jupyter", "Pandas", "Matplotlib"],
        image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500",
        demoUrl: "https://github.com/haremir/ScoutMaster",
        codeUrl: "https://github.com/haremir/ScoutMaster",
        featured: true
      }
    ],
  
    // All projects - Real GitHub projects
    projects: [
      {
        id: 1,
        title: "GameGain - Oyun Geliri Tahmini",
        description: "İlk 15 günlük oyuncu davranışlarını analiz ederek 90 günlük oyun gelirini tahmin eden makine öğrenmesi modeli. Kullanıcı seviyesinde gelir tahmini için etkili veri analizi ve modelleme teknikleri kullanılmıştır.",
        technologies: ["Python", "Pandas", "Scikit-learn", "XGBoost", "Matplotlib"],
        image: "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=500",
        demoUrl: "https://github.com/haremir/GameGain-",
        codeUrl: "https://github.com/haremir/GameGain-",
        category: "Machine Learning",
        status: "Tamamlandı",
        featured: true
      },
      {
        id: 2,
        title: "Fraud Eye - Dolandırıcılık Tespiti",
        description: "Kredi kartı dolandırıcılığını tespit etmek için geliştirilmiş makine öğrenmesi sistemi. Anomali tespiti ve sınıflandırma algoritmaları kullanılmıştır.",
        technologies: ["Python", "TensorFlow", "Pandas", "Seaborn", "Scikit-learn"],
        image: "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=500",
        demoUrl: "https://github.com/haremir/fraud_eye",
        codeUrl: "https://github.com/haremir/fraud_eye",
        category: "Fraud Detection",
        status: "Tamamlandı",
        featured: true
      },
      {
        id: 3,
        title: "ScoutMaster - Futbol Oyuncusu Analizi",
        description: "Futbol oyuncularının becerilerini ve piyasa değerlerini analiz ederek gelecek sezon değer artışlarını tahmin eden sistem. Spor analitiği ve prediktif modelleme içerir.",
        technologies: ["Python", "Jupyter", "Pandas", "Matplotlib", "Seaborn"],
        image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500",
        demoUrl: "https://github.com/haremir/ScoutMaster",
        codeUrl: "https://github.com/haremir/ScoutMaster",
        category: "Sports Analytics",
        status: "Tamamlandı",
        featured: true
      },
      {
        id: 4,
        title: "CineMatch - Film Öneri Sistemi",
        description: "Collaborative filtering kullanarak kişiselleştirilmiş film önerileri sunan sistem. Kullanıcı davranışlarını analiz ederek benzer beğenilere sahip kullanıcıları bulur.",
        technologies: ["Python", "Jupyter", "Pandas", "NumPy", "Scikit-learn"],
        image: "https://images.unsplash.com/photo-1489599317698-2f4e7bac6adb?w=500",
        demoUrl: "https://github.com/haremir/CineMatch",
        codeUrl: "https://github.com/haremir/CineMatch",
        category: "Recommendation System",
        status: "Tamamlandı",
        featured: false
      },
      {
        id: 5,
        title: "AltinEx - Altın Takip Uygulaması",
        description: "Altın fiyatlarını takip eden finansal analiz uygulaması. Gerçek zamanlı veri analizi ve görselleştirme özellikleri içerir.",
        technologies: ["Python", "Flask", "SQLite", "Matplotlib"],
        image: "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=500",
        demoUrl: "https://github.com/haremir/AltinEx",
        codeUrl: "https://github.com/haremir/AltinEx",
        category: "Fintech",
        status: "Tamamlandı",
        featured: false
      },
      {
        id: 6,
        title: "Real Estate Forecast",
        description: "Emlak fiyat tahmin modeli - ACUNMEDYA ev ödevi olarak geliştirildi. Gayrimenkul piyasası analizi ve fiyat tahmin algoritmaları içerir.",
        technologies: ["Python", "Jupyter", "Pandas", "Scikit-learn"],
        image: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=500",
        demoUrl: "https://github.com/haremir/real_estate_forecast",
        codeUrl: "https://github.com/haremir/real_estate_forecast",
        category: "Real Estate",
        status: "Tamamlandı",
        featured: false
      }
    ],
  
    // Resume/CV data
    resume: {
      experience: [
        {
          id: 1,
          company: "Serbest Çalışan",
          position: "Veri Bilimci & AI Geliştirici",
          duration: "2023 - Devam ediyor",
          description: "Çeşitli projeler üzerinde çalışarak makine öğrenmesi ve veri analizi alanında deneyim kazanıyorum.",
          achievements: [
            "6+ makine öğrenmesi projesinin başarıyla tamamlanması",
            "Dolandırıcılık tespiti algoritması geliştirilmesi",
            "Oyun geliri tahmin modelinin oluşturulması",
            "GitHub'da Pull Shark achievement kazanılması"
          ]
        },
        {
          id: 2,
          company: "Eskişehir Teknik Üniversitesi",
          position: "Bilgisayar Mühendisliği Öğrencisi",
          duration: "2021 - Devam ediyor",
          description: "Akademik eğitimim süresince veri yapıları, algoritmalar ve makine öğrenmesi konularında derinlemesine bilgi ediniyorum.",
          achievements: [
            "Başarılı akademik performans",
            "Veri bilimi projeleri geliştirme",
            "Takım çalışması ve proje yönetimi deneyimi"
          ]
        }
      ],
      education: [
        {
          id: 1,
          school: "Eskişehir Teknik Üniversitesi",
          degree: "Bilgisayar Mühendisliği Lisans",
          duration: "2021 - Devam ediyor",
          gpa: "Devam ediyor"
        }
      ],
      skills: {
        technical: [
          { name: "Python", level: 95 },
          { name: "Machine Learning", level: 90 },
          { name: "Data Analysis", level: 90 },
          { name: "TensorFlow", level: 85 },
          { name: "PyTorch", level: 85 },
          { name: "Pandas", level: 95 },
          { name: "Scikit-learn", level: 90 },
          { name: "SQL", level: 80 },
          { name: "Git", level: 85 },
          { name: "Jupyter", level: 95 }
        ],
        soft: [
          "Analitik Düşünme",
          "Problem Çözme",
          "Takım Çalışması",
          "Proje Yönetimi",
          "İletişim",
          "Araştırma"
        ]
      },
      languages: [
        { name: "Türkçe", level: "Ana dil" },
        { name: "İngilizce", level: "İleri seviye" },
        { name: "Almanca", level: "Temel seviye" }
      ]
    },
  
    // Contact information and social links
    contact: {
      email: "harunemirhanbostanci@gmail.com",
      phone: "+90 555 123 45 67",
      location: "İstanbul, Türkiye",
      availability: "Yeni projeler ve iş fırsatları için müsait",
      social: [
        { name: "LinkedIn", url: "https://www.linkedin.com/in/harun-emirhan-bostanci-24144726b", icon: "linkedin" },
        { name: "GitHub", url: "https://github.com/haremir", icon: "github" },
        { name: "Kaggle", url: "https://kaggle.com/harunemirhanbostanci", icon: "github" },
        { name: "Blog", url: "https://haremir.blogspot.com/", icon: "behance" }
      ],
      services: [
        {
          title: "Makine Öğrenmesi Modelleri",
          description: "Sınıflandırma, regresyon ve kümeleme algoritmaları ile özel ML modelleri geliştirme"
        },
        {
          title: "Veri Analizi ve Görselleştirme",
          description: "Pandas, NumPy ve Matplotlib ile kapsamlı veri analizi ve raporlama"
        },
        {
          title: "Dolandırıcılık Tespiti",
          description: "Finansal veri analizi ve anomali tespiti sistemleri geliştirme"
        },
        {
          title: "Teknik Danışmanlık",
          description: "Veri bilimi projeleri, algoritma seçimi ve model optimizasyonu konularında danışmanlık"
        }
      ]
    }
  };
  
  export default portfolioData;