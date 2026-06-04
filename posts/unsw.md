---
cover: /blog/unsw-cover.png
date: '2025-12-15'
description: Bu yazıda, Avustralya'nın New South Wales Üniversitesi tarafından derlenen
  UNSW-NB15 veri seti üzerinde ağ saldırısı tespiti yapan bir proje ele alınıyor.
  175.000 bağlantı kaydı ve 42 özellik içeren bu veri setinde DBSCAN, K-NN (unsupervised)
  ve AutoML (supervised) yöntemleri karşılaştırıldı. Unsupervised yöntemler label
  olmadan anomali varlığını sezebilirken (%51 ve %36 doğruluk), etiketli veriye erişildiğinde
  AutoML %93.5 doğruluğa ulaştı. İki yaklaşımın birbirini tamamladığı ve tek modelin
  production için yeterli olmadığı sonucuna varıldı.
description_en: In this post, a network attack detection project on the UNSW-NB15
  dataset compiled by the University of New South Wales in Australia is evaluated.
  Comparing DBSCAN, K-NN (unsupervised), and AutoML (supervised) methods over 175,000
  connection logs and 42 features, unsupervised methods detected anomalies without
  labels (51% and 36% accuracy), whereas AutoML achieved 93.5% accuracy using labeled
  data. It is concluded that both approaches complement each other and a single model
  is insufficient for production.
tags:
- Network Security
- Anomaly Detection
- Clustering
- Supervised Learning
title: 'UNSW-NB15 ile Anomali Tespiti: Saldırıları Aramak'
title_en: 'Anomaly Detection with UNSW-NB15: Hunting for Network Attacks'
---

Hayal edin: 175.000 paket görmüş olan bir ağ yöneticisi. Bunların 31'i normal, 69'u saldırı. Peki hangileri hangileri? Elinde 42 özellik var - TTL değeri, paket sayısı, protokol türü, port numarası... Gözle incelemek imkansız. İşte bu yazıda, makine öğrenmesi ile saldırıları normal trafikten nasıl ayırt ettiğimizi göreceğiz. Hatta daha ilginç olanı: unsupervised ve supervised yöntemlerinin karşılaşmasını izleyeceğiz.

---

## Proje Hikayesi: KNIME'den Python'a

Başlangıçta KNIME (Konstanz Information Miner) adlı görsel data mining aracında bir iş akışı kuruldu. Ama aslında mesele sadece araç değil - konsept önemliydi. Hem unsupervised learning (DBSCAN, K-NN) hem de supervised learning (AutoML) kullanarak bir "Frankenstein" modeli oluşturduk.

Neden bu garip kombinasyon? Çünkü etiketleri olmayan veriyi keşfetmekten, sonra makine öğrenmesi ile tahmin yapmaktan farkı öğrenmek istiyorduk.

---

## CRISP-DM: Sistematik Bir Soruşturma

### 1. İş Anlayışı: Siber Tehdidi Tanımlamak

"Ne yapmaya çalışıyoruz?"

Yanıt basit ama güçlü: Ağ trafiğinde saldırıları %93.5 doğrulukla tespit etmek.

**Neden?** Çünkü:

- Saldırılar gerçek zamanlı olur - yapılacak en ufak gecikme, sistem çöker
- False positive'ler (normal'i saldırı zannetmek) yöneticileri çıldırtır
- False negative'ler (saldırıyı kaçırmak) felaket demektir

---

### 2. Veri Anlayışı: 175.000 Bağlantıdan Hikaye Çıkarmak

UNSW-NB15 veri seti, Avustralya'nın New South Wales Üniversitesi tarafından gerçek ağ ortamında toplanmış. Yani fake data değil, asıl ağırbaşlı saldırılar:

| Saldırı Türü | Açıklama |
|---|---|
| DoS | Hizmet engelleme saldırıları |
| Port Scanning | Açık kapıları bulmaya çalışma |
| Exploits | Bilinen açıklıkları istismar etme |
| Backdoors | Sistem içine gizli kapı açma |
| Worms | Kendini çoğaltan zararlı kodlar |

**Veri dengesi problem mi?**

- Normal: %31
- Attack: %69

Evet, dengesiz! Ama bu da gerçek hayatın refleksiyonu - ağlarda saldırılar normalden daha az görülür. Ama veri setinde yapay olarak arttırılmış (simulation).

---

### 3. Veri Hazırlığı: 42 Özellikten 39'a İnme

Verinin ham hali:

| Grup | Örnekler |
|---|---|
| Zaman Özellikleri | Flow duration, paket zamanlaması |
| Trafik Özellikleri | Gönderilen/alınan paket sayısı, byte sayısı |
| Ağ Özellikleri | Kaynak/hedef port, protokol (TCP/UDP) |
| State Özellikleri | TCP flagları (SYN, ACK, FIN vs.) |
| İçerik Özellikleri | Transaction sayısı, rate |

Eksik değer kontrol ettik - az sayıda NaN vardı, direkt çıkardık.

Sonra kritik adım: **Normalizasyon**

```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_normalized = scaler.fit_transform(X)
```

Neden? Çünkü unsupervised algoritmaları (DBSCAN, K-NN) Öklid mesafesini kullanıyor. Eğer bir özellik 0-10 aralığında, diğer 0-1000 aralığında olursa, büyük değerler hükim olur.

---

### 4. Modelleme: İki Dünyanın Buluşması

Burada ilginç bir paradigma çatışması yaşadık. Normalde ya unsupervised ya da supervised dersiniz. Ama biz her ikisini denedik çünkü merakımız vardı.

#### A. Unsupervised Learning: Veri Sesini Dinlemek

**DBSCAN** *(Density-Based Spatial Clustering of Applications with Noise)*

Temel fikir: Eğer noktalar sıkı bir şekilde bir arada toplu ise, normal davranış. Yalnız dolaşan noktalar ise anomali.

```python
from sklearn.cluster import DBSCAN

dbscan = DBSCAN(eps=0.5, min_samples=5)
labels = dbscan.fit_predict(X_normalized)

# -1 = Noise (Anomaly), 0,1,2... = Normal Clusters
```

Parametreler kritik:

- `eps=0.5` → Komşuluk yarıçapı (ne kadar yakın = komşu?)
- `min_samples=5` → En az 5 komşusu olmalı normal olarak sayılmak

| Metrik | Sonuç |
|---|---|
| Tespit edilen anomali | 687 (%68.7) |
| Gerçek anomali | 690 (%69) |
| Accuracy | %51.30 |

---

**K-NN** *(K-Nearest Neighbors Distance)*

Farklı yaklaşım: Her nokta için en yakın 5 komşusunun ortalama uzaklığını hesapla. Eğer bu uzaklık threshold'dan büyükse, yalnız demektir = anomali.

```python
from sklearn.neighbors import NearestNeighbors

knn = NearestNeighbors(n_neighbors=5)
distances, indices = knn.kneighbors(X_normalized)

# Her noktanın ortalama uzaklığı
avg_distances = distances[:, 1:].mean(axis=1)

# Threshold > 1.2 => Anomaly
predictions = np.where(avg_distances > 1.2, 1, 0)
```

| Metrik | Sonuç |
|---|---|
| Tespit edilen anomali | 380 (%38) |
| Accuracy | %36.00 |

Çok konservatif! Ama bunu optimize edebiliriz (threshold'u düşürerek).

---

#### B. Supervised Learning: Makine Öğrenmesinin Hızlı Cevabı

**AutoML (AutoGluon)**

Şimdi labelleri kullandık. AutoGluon otomatik olarak:

- Farklı modeller denedi (XGBoost, LightGBM, RandomForest)
- Hyperparameter'ları optimize etti
- Stack ensemble oluşturdu

```python
from autogluon.tabular import TabularPredictor

predictor = TabularPredictor(label='label', problem_type='binary')
predictor.fit(train_data, time_limit=120, presets='medium_quality')
```

| Metrik | Sonuç |
|---|---|
| Accuracy | **%93.50** ✅ |
| F1-Score | **0.9537** ✅ |
| ROC-AUC | **0.9806** ✅ |

Devasa bir sıçrama!

---

### 5. Değerlendirme: Sayılar Hikaye Anlatıyor

Confusion Matrix'i inceledik - AutoML neler yapıyor?

|  | Tahmin: Normal | Tahmin: Attack |
|---|---|---|
| **Gerçek: Normal** | 1058 | 10 |
| **Gerçek: Attack** | 48 | 884 |

- True Negatives (1058): Normal trafiği normal diye tespit etti - harika!
- False Positives (10): Normal'i saldırı dedi - minyon hata
- False Negatives (48): Saldırıyı kaçırdı - sorun!
- True Positives (884): Saldırıyı yakaladı - güzel!

**Büyük sorular:**

- "48 saldırıyı neden kaçırdı?" → Muhtemelen bilinmeyen saldırı türleri (zero-day)
- "10 normal'i neden saldırı dedi?" → Biraz agresif sınıflandırma

---

### 6. Ensemble: İki Yönemin Buluşması

Unsupervised ve supervised'i birleştirelim ne olur?

**Hard voting** — ikisi de anomaly derse → anomaly:

```python
ensemble_pred = np.where((dbscan_pred == 1) & (knn_pred == 1), 1, 0)
```

Sonuç: K-NN ile aynı (%36) çünkü K-NN daha kısıtlı.

**Soft voting** — birisi anomaly derse → anomaly:

```python
ensemble_pred = np.where((dbscan_pred == 1) | (knn_pred == 1), 1, 0)
```

Bu DBSCAN'i dominant yapar.

---

### 7. Deployment: Gerçek Dünyaya

AutoML modelini deployment package'a koyduk:

```python
import pickle

# Modeli kaydet
with open('deployment_package.pkl', 'wb') as f:
    pickle.dump({
        'model': automl_predictor,
        'scaler': scaler,
        'feature_names': feature_names
    }, f)
```

Production'da:

```python
with open('deployment_package.pkl', 'rb') as f:
    package = pickle.load(f)

model = package['model']
scaler = package['scaler']

# Yeni flow geldi
new_flow = get_network_flow()  # 39 özellik
new_flow_scaled = scaler.transform([new_flow])
prediction = model.predict(new_flow_scaled)

if prediction[0] == 1:
    print("🚨 SALDIRI TESPİT EDİLDİ!")
    alert_security_team()
else:
    print("✅ Normal trafik")
```

---

## Öğrendiklerim: Siber Güvenlik Dersleri

**Unsupervised learning ilk adım olabilir:** DBSCAN hiç label görmeden doğru anomali sayısını buldu. Bu, elimizde yeni veri türü varsa çok değerli.

**Normalizasyon çok kritik:** Normalized olmayan veriyle DBSCAN tamamen farklı sonuç verdi.

**Label dengesi problem değil, fırsat:** %69 anomali, dengesiz görünse de, gerçek veriyi temsil ediyor.

**Ensemble çift kesici bir kılıç:** Hard voting çok konservatif, soft voting çok liberal. Ortada yol bulmalıyız.

**Real-time detection ne demek:** 175.000 paketi test etmek çok ama, yeni bir paket geldiğinde tahmin saniyenin ufak bir bölümüne sığıyor.

---

## Pratik Uyarılar: SOC Analisti Gözlüğüyle

Bu model %93.5 de olsa, tek başına yeterli değil:

- Pattern matching ile kombinle
- Threshold'u sensitivity'ye göre ayarla
- User behavior analytics (UBA) ekle
- Threat intelligence entegre et

---

## Sonuç: Gizli Saldırılar ve Açık İstatistikler

Ağ trafiği bir dil gibi konuşuyor - eğer dinleyebilirsen. DBSCAN'ın bulduğu "sessiz anomaliler", AutoML'nin öğrendiği "labelled pattern'ler" - ikisi birlikte mükemmel bir dinleyici oluşturuyor.

Ama hatırla: makine öğrenmesi silah değil, tespite yardımcı. İnsan farkındalığı, iyi ağ mimarisi ve güvenlik kültürü asıl koruyu sağlıyor.

---

## İletişim

📧 E-mail: harunemirhan826@gmail.com 💼 LinkedIn: https://www.linkedin.com/in/haremir826/ 🔗 GitHub: https://github.com/haremir

Siber güvenlik ve anomali tespiti yolculuğunuzda başarılar dilerim! 🔐

---

> **Not:** UNSW-NB15 veri seti açık kaynak ve yeniden üretilebilir. Kendi ağınız için benzer analiz yapabilir, parametre'leri tune edebilirsiniz. GitHub'da tüm kod ve KNIME workflow'u mevcut!