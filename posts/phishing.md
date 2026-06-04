---
cover: /blog/phishing-cover.png
date: '2025-11-30'
description: Bu yazıda, UCI Machine Learning Repository'den alınan ~11.000 web sitesi
  verisiyle makine öğrenmesi kullanarak phishing tespiti yapan bir proje ele alınıyor.
  CRISP-DM metodolojisiyle ilerleyen projede Logistic Regression, Decision Tree, Gradient
  Boosting ve Random Forest modelleri karşılaştırıldı. En yüksek doğruluk oranına
  (%96.1) ve en düşük overfitting'e sahip Random Forest kazanan model olarak seçildi.
  SSL sertifikası, ankor tag'ları ve web trafiği gibi özelliklerin phishing tespitinde
  en belirleyici faktörler olduğu ortaya çıktı.
description_en: In this post, a project is discussed that detects phishing attempts
  using machine learning on ~11,000 websites from the UCI Machine Learning Repository.
  Structured around the CRISP-DM methodology, the project compares Logistic Regression,
  Decision Tree, Gradient Boosting, and Random Forest models. With the highest accuracy
  (96.1%) and the lowest overfitting, Random Forest was selected as the winning model.
  Features like SSL certificates, anchor tags, and web traffic volume emerged as the
  most critical indicators.
tags:
- Phishing Detection
- Tree-Based Models
- Cyber Security
- Predictive Analytics
title: 'Phishing Web Sitelerini Tespit Etmek: Machine Learning ile Güvenlik'
title_en: 'Detecting Phishing Websites: Machine Learning-Based Security'
---

Her gün milyonlarca insan internette gezerken, bilinçli ya da bilinçsiz bir şekilde tehlikeli web sitelerle karşılaşıyor. Bankacılık bilgilerinizi çalmaya çalışan, kredi kartı numaranızı istemeye çalışan "resmi görünen" sahte siteler... İşte bu yazıda, makine öğrenmesi ile phishing siteleri nasıl tanıdığımızı ve bununla mücadele ettiğimizi keşfedeceğiz.

---

## Proje Hikayesi: Dijital Hırsızlığa Karşı Silah

Phishing, internetteki en yaygın siber saldırı türlerinden biri. Saldırganlar sizin sahip olduğunuz şeyi (para, kişisel bilgiler) çalmaya çalışırken, meşru bir kurumun veya kişinin kimliğini taklit ediyor.

**Örnek senaryo:** Bankanız *"Hesabınız kilitlendi, lütfen tıklayın"* diye bir e-mail gönderiyor ama aslında bu bir sahte site. Tıklayıp şifrenizi girdikten sonra hesabınız boşaltılıyor.

**Soru şu:** Bilgisayar bu sahte siteleri gerçek sitelerden nasıl ayırt edebilir?

İşte bu projektenin temel motivasyonu.

---

## CRISP-DM ile Başlangıç: Sistematik Yaklaşım

Yine başta metodoloji. Rastgele model denemeye başlamadan önce, adım adım ilerlememiz gerekiyor.

### 1. İş Anlayışı: Hedef Açık

"Ne yapıyoruz burada?"

Yanıt: Web sitesini tek bir URL bakarak, phishing mi legitimate mi olduğunu %96 doğrulukla sınıflandırmak.

**Neden önemli?**

- İnternet servis sağlayıcıları tehlikeli siteleri hızlıca blokleyebilir
- E-mail filtrelemeleri daha akıllı hale gelir
- Kullanıcılar gerçek zamanda uyarı alabilir

---

### 2. Veri Anlayışı: Oltalama Tuzakları

UCI Machine Learning Repository'den alınan veri seti, yaklaşık 11.000 web sitesinin özelliklerini içeriyor. Her sitede 30 farklı özellik ölçülmüş:

| Özellik Grubu | Örnekler |
|---|---|
| URL Özellikleri | IP adresi var mı? URL ne kadar uzun? |
| Domain Özellikleri | Kaç yaşında? SSL sertifikası var mı? |
| İçerik Özellikleri | Linkler nasıl? Formlar var mı? |
| Trafik Özellikleri | Google'da indekslenmiş mi? |

**En önemli soru: Veri seti dengeli mi?**

- %56 Phishing (negatif örnek)
- %44 Legitimate (pozitif örnek)

Hafif dengesiz ama çalışılabilir. Dengeli bir set idealdir ama bu gerçek hayatta nadiren olur.

---

### 3. Veri Hazırlığı: Temizlik Operasyonu

Birçok ML projesinden farklı olarak, bu veri seti çoğunlukla temiz geldi. Neden? Çünkü özellikler zaten belirli kurallarla ölçülmüş:

- `-1` → Phishing göstergesi
- `0` → Orta/belirsiz
- `1` → Legitimate göstergesi

Yani kategorik değerler, sayısal değerler değil. Bu bizim için yardımcı oldu.

**Eksik Değer Kontrolü:** Bir veya iki satırda `?` işareti vardı. Tamamen çıkardık. Total 11.000 kayıttan önemsiz bir kayıp.

**Veri Dengesi:** Dengesiz veri sınıflandırma modellerini yanıltabilir. Örneğin, "her şey phishing değil" desen model %56 doğruluk elde ediyor! Bu yüzden stratified split yaptık - eğitim ve test setinde oran aynı kaldı.

---

### 4. Feature Engineering: Özellikleri Anlama

Bu projede çoğu özellik zaten extract edilmişti ama biz yine de çok önemli bir adım attık: multicollinearity analizi.

Bazı özellikler birbirine çok benzer şekilde davranıyordu. Örneğin:

- `URL_Length` ile `Domain_Length` ilişkili
- `having_Sub_Domain` ile `Domain_registeration_length` korelasyonlu

Correlation matrix'i çizdik ve 0.8'den yüksek korelasyona sahip olanları çıkardık. Neden? Çünkü gereksiz özellikler:

- Model karmaşıklığını artırır
- Overfitting riskini yükseltir
- Eğitim süresini uzatır

**Sonuç:** 30 özellikten 28 özellik kaldı. İlişkili olanları bir temizlik operasyonuyla çıkarmıştık.

---

### 5. Modelleme: Dört Yolcu, Bir Destinasyon

Dört farklı sınıflandırıcıyı test ettik:

#### Logistic Regression (Baseline)

Basit, hızlı, yorumlanabilir. Probabilistik yaklaşım:

| Metrik | Sonuç |
|---|---|
| Test Accuracy | %92.1 |
| F1-Score | 0.921 |
| ROC-AUC | 0.972 |

Güzel bir baseline ama daha iyisini yapmamız gerekti.

---

#### Decision Tree

Belki de en açık-seçik model. "Eğer SSL var ise → legitimate" gibi karar kuralları:

| Metrik | Sonuç |
|---|---|
| Test Accuracy | %94.2 |
| F1-Score | 0.942 |
| ROC-AUC | 0.941 |

Daha iyi ama hafif bir sorun: %5 overfitting (train: %99, test: %94).

---

#### Gradient Boosting

Sequential olarak öğrenen, önceki hataları düzeltmeye çalışan model:

| Metrik | Sonuç |
|---|---|
| Test Accuracy | %96.0 |
| F1-Score | 0.960 |
| ROC-AUC | 0.988 |

Çok güçlü! Ama 18 saniye eğitim süresi biraz uzun.

---

#### Random Forest (Kazanan 🏆)

100 ağacın demokratik oyuyla karar veren ensemble modeli:

| Metrik | Sonuç |
|---|---|
| Test Accuracy | **%96.1** |
| F1-Score | **0.961** |
| ROC-AUC | **0.989** |
| Training Time | ~2 saniye |

**Kazanan! Neden?**

- En yüksek accuracy (%96.1)
- En düşük overfitting (%1.1 fark)
- Hızlı eğitim ve tahmin
- Feature importance bilgisi veriyor

---

### 6. Değerlendirme: Sayılardan Öteye

Confusion matrix incelemesi heyecan vericiydi:

|  | Predicted: Phishing | Predicted: Legitimate |
|---|---|---|
| **Actual: Phishing** | 1234 | 42 |
| **Actual: Legitimate** | 48 | 1176 |

Modelin "yanlış negatifleri" (phishing'i legitimate diye sınıflandırma): 42 Modelin "yanlış pozitifler" (legitimate'i phishing diye sınıflandırma): 48

Ayrımı dengeli - ne false pozitif ne de false negative'de saç baş yolmayan miktarda hata.

---

**Feature Importance Analizi:**

Random Forest bize önemli bir secret verdi - hangi özellikler gerçekten önemli?

| Özellik | Önem Skoru |
|---|---|
| SSLfinal_State | %12.45 |
| URL_of_Anchor | %9.87 |
| Request_URL | %8.76 |
| web_traffic | %8.12 |
| Google_Index | %7.54 |

Bu özellikler saldırganlar için "işaret" gibi - bize phishing olasılığını söylüyor.

---

### 7. Deployment: Gerçek Dünyaya

Modeli joblib ile kaydettik. Üretim ortamında nasıl çalışacağını hayal edin:

```python
import joblib

model = joblib.load('models/random_forest.pkl')

# Yeni bir URL'nin 30 feature'ını hesapla
url_features = extract_features(suspicious_url)

# Tahmin yap
prediction = model.predict([url_features])
probability = model.predict_proba([url_features])

if prediction[0] == -1:
    print("⚠️ PHISHING! Confidence: %.2f%%" % (probability[0][0] * 100))
else:
    print("✅ Legitimate. Confidence: %.2f%%" % (probability[0][1] * 100))
```

---

## Öğrendiklerim: Güvenlik Mimarı Notları

**Basit özellikler güçlüdür:** IP adresi, SSL sertifikası, URL uzunluğu gibi basit şeyler phishing tespiti için şaşırtıcı derecede etkili.

**Ensemble modeller ensemble problemlere karşı gelir:** Random Forest'ın 100 ağacı, tekil bir ağacın yanılmalarını telafi ediyor.

**Overfitting her zaman tehdit:** %99 eğitim accuracy ile %94 test accuracy görmek bizi Decision Tree'yi elemeye zorladı.

**Feature importance business insight verir:** Machine learning sadece tahmin değil, veri hakkında hikaye de söylüyor.

**Model yeterli değil:** %96 accuracy çok güzel ama production'da:

- Google Safe Browsing API
- VirusTotal
- User reporting

gibi katmanlarla kombine edilmeli. Tek başına model siber saldırıya karşı kalkan değildir.

---

## Pratik Uyarılar: Siz de Koruyabilirsiniz

Bu model çok iyi ama insan faktörü unutulmamalı:

- Tanımadığınız yerden e-mail geldi? Linke tıklamadan önce bekleyin
- URL'ye baktığınızda "https://" yerine "http://" varsa şüphelenin
- Müşteri hizmeti asla şifre soramaz
- Banka "acil işlem" talebinde bulunmaz

---

## Sonuç: Dijital Şüphecilik

Phishing, teknolojinin "sosyal mühendislik" ile buluştuğu noktadır. Ne kadar iyi makine öğrenmesi modeli olursa olsun, insan farkındalığı en önemli güvenlik katmanıdır.

Ama bilmek iyi bir başlangıç. İnternet güvenli bir yer olmayabilir ama en azından artık nasıl bakmamız gerektiğini biliyoruz.