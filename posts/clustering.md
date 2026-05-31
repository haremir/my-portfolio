---
title: "Ağ Trafiğini Anlamak: Clustering ile Anomali Tespiti"
date: "2025-10-12"
description: "Bu yazıda, UNSW-NB15 veri seti üzerinde unsupervised clustering kullanarak ağ trafiğindeki gizli paternler keşfediliyor. 175.000'in üzerinde bağlantı kaydı ve 42 özellik üzerinde K-Means ve Fuzzy C-Means algoritmaları karşılaştırıldı. Silhouette skoru açısından daha iyi performans gösteren K-Means, 5 optimal küme üretti: normal trafik, DoS saldırıları, port scanning, exploitation girişimleri ve diğer anomaliler. Etiket kullanılmadan üretilen bu kümelerin gerçek saldırı türleriyle örtüştüğü görüldü."
tags:
  - Unsupervised Learning
  - Clustering
  - Network Security
  - Anomaly Detection
cover: "/blog/clustering-cover.png"
---

Bir yazılım mimarisinin kalbi nedir? Güvenliği! Ve güvenliğin başını ise ağ trafik analizleri çeker. Her gün binlerce bağlantı, milyonlarca paket, sınırsız veri akışı... İçinde gizli saldırılar, anomaliler, tehditler var. Peki bunları nasıl buluyoruz? İşte bu yazıda, clustering ile ağ trafiğinde gizli paternleri keşfetme yolculuğuna çıkacağız.

---

## Proje Hikayesi: UNSW-NB15 ile Tanışma

Siber güvenlik araştırmalarında en meşhur veri setlerinden biri UNSW-NB15 - "UNSW NetFlow BigData 2015". University of New South Wales tarafından gerçek ağ ortamında çekilen, 175.000'in üzerinde bağlantı kaydı içeriyor.

**Özel olan ne?** Bu, salt trafik paketi değil, gerçek saldırı örnekleri içeriyor:

- DoS (Denial of Service) saldırıları
- Port scanning denemeler
- Exploit (açıklık istismarı) girişimleri
- Zararlı yazılım iletişimi
- Brute force login denemeler

Ama soru şu: Hangi özelliklere bakarak, saldırıyı tanıyabiliriz?

---

## CRISP-DM: Sistematik Detektiflik

Herhangi bir soruşturmada olduğu gibi, burada da metodoloji hayati önem taşıyor.

### 1. İş Anlayışı: Soruşturma Başlangıcı

"Ne arıyoruz?"

Cevap: Ağ trafiğinde doğal gruplar bulmak ve bu grupların saldırı türleriyle ilişkisini anlama.

**Neden?** Çünkü:

- Normal trafik bir pattern gösterir
- Saldırılar kendi özel pattern'lerini oluşturur
- Eğer pattern'ler farklıysa, gruplandırırken ayrılacaklar

Supervised learning (sınıflandırma) burada işe yaramayabilir - çünkü biz zaten saldırı etiketlerini biliyoruz. Ama unsupervised learning (kümeleme) verinin kendi sesini dinlemeyi sağlıyor.

---

### 2. Veri Anlayışı: 175.000 Bağlantı Merkür Benzeri

UNSW-NB15 veri seti gerçekten müthiş. 42 özellik, herbiri bir network flow'ın farklı yönünü ölçüyor:

| Grup | Örnekler |
|---|---|
| Zaman Özellikleri | Bağlantı süresi (duration), ne kadar veri gönderildikten sonra başladı? |
| Trafik Özellikleri | Kaynak ve hedef port, protokol (TCP/UDP), flow rate, paket sayıları |
| Hedef Özellikleri | Hedef makinenin load'ı, state flags (SYN, ACK, RST vs.), TTL |
| İçerik Özellikleri | Bir bağlantıdaki transaction sayısı, Irkn (Initial RTS counter number) |

**En önemli soru: Veri normal dağılım mı?**

Çoğu özellik çarpık dağılım gösteriyordu. Mesela "sload" (source load) değerleri 0-60 arasında yoğunlaşmış ama birkaçı 1000'lere çıkıyor. Bu da standardizasyon (scaling) ihtiyacını gösteriyor.

---

### 3. Veri Hazırlığı: Standart Sayfa Düzeni

Clustering algoritmaları Öklid mesafesi kullanırlar (genellikle). Bu mesafe yüksek değerlerin etkisiyle bozulabilir.

**Scaling Operasyonu:** StandardScaler kullanarak her özelliği 0-1 aralığına getirdik:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)
```

Şimdi her özellik eşit ağırlığa sahip. Bir özellik 1000 değerine sahipse bile, scale edilmişse 0-1'de olur.

**Eksik Değer Temizliği:** Bazı kayıtlarda missing value vardı. Direkt çıkardık - ~%2 kaybımız var.

**Outlier Kontrolü:** IQR yöntemiyle uç değerleri tespit ettik. Kırptık ama çıkarmadık - çünkü bir DDoS saldırısı asıl "aykırı" olabilir ama biz onu görmek istiyoruz!

---

### 4. Feature Engineering: Boyut Azaltma Düşüncüsü

42 özellik çok mu? Varyans analizi yaptık. Bazı özellikler sabitti - tüm bağlantılarda aynı değer. Bunları çıkardık.

Sonra: Korelasyon temizliği. 0.95'ten yüksek korelasyona sahip özellikler birbiri yerine geçebilir - sadece birini tuttuk.

**Sonuç:** 42 özellikten 35 özellik.

Neden bütün özelliği almadık? Çünkü "boyut lanetinden" (curse of dimensionality) kaçınmak istiyoruz. Daha az özellikle daha net kümeler oluşabilir.

---

### 5. Modelleme: İki Yaklaşım, Bir Hedef

#### K-Means Clustering

Centroid-based yaklaşım. Çıngıl gibi çalışır:

1. K adet random merkez seç
2. Her noktayı en yakın merkeze ata
3. Merkezleri güncelleştir
4. Tekrarla

```python
from sklearn.cluster import KMeans

kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)
```

| Metrik | Sonuç |
|---|---|
| Silhouette Score | 0.4523 ⭐ |
| Davies-Bouldin Index | 0.8721 (düşük = iyi) |
| Calinski-Harabasz Score | 12,847 (yüksek = iyi) |

5 küme optimal çıktı. İteratif olarak 2'den 10'a kadar denedik - Silhouette skoru 5'te pik yapıyor.

---

#### Fuzzy C-Means

"Yumuşak" clustering. Bir noktanın birden fazla kümeye kısmen ait olabileceğini söyler:

```python
import skfuzzy as fuzz

cntr, u, u0, d, jm, p, fpc = fuzz.cluster.cmeans(
    X_scaled.T, c=5, m=2.0, error=1e-5, maxiter=150)
```

| Metrik | Sonuç |
|---|---|
| Silhouette | 0.4312 (K-Means'e kıyasla %4.7 daha düşük) |
| Davies-Bouldin | 0.9156 (biraz daha kötü) |

**Kazanan: K-Means**

Neden? Basit ve net kümeler verirken, FCM biraz daha belirsiz alanlar yarattı. Bu projekte net ayrılma istediğimiz için K-Means yeterli oldu.

---

### 6. Değerlendirme: Kümeler Hikaye Anlatıyor

Beş küme ne anlam taşıyordu?

**Cluster 0 - Normal Trafik (%31)**
- Düşük rate, normal paket sayıları
- Balanced upload/download
- Label analizi: Çoğu "Normal"

**Cluster 1 - DoS Saldırıları (%24)**
- Çok yüksek packet rate
- Kaynak load çok yüksek
- Kısa süre, yüksek intensity
- Label: Çoğu "DoS"

**Cluster 2 - Port Scanning (%18)**
- Çok sayıda connection attempt
- Farklı portlara bağlantı denemeleri
- Düşük veri transfer
- Label: Çoğu "Reconnaissance"

**Cluster 3 - Exploitation Girişimleri (%15)**
- Anormal protocol kullanımı
- Garip flag kombinasyonları
- Specific port patterns
- Label: Çoğu "Exploits"

**Cluster 4 - Diğer Anomaliler (%12)**
- Karışık, belirlenemeyen pattern'ler
- Zararlı yazılım iletişimi, Backdoor vb.
- Label: Karışık saldırı türleri

---

### 7. Deployment: Gerçek Zamanlı Anomali Tespiti

Modeli kaydettikten sonra, yeni bir flow geldiğinde:

```python
import joblib
import numpy as np

# Modeli yükle
kmeans = joblib.load('models/kmeans_model.pkl')
scaler = joblib.load('models/scaler.pkl')

# Yeni flow
new_flow = extract_features_from_packet()  # 35 özellik
new_flow_scaled = scaler.transform([new_flow])

# Kümeyi tahmin et
cluster = kmeans.predict(new_flow_scaled)

if cluster in [1, 2, 3]:  # Saldırı kümesiyse
    print("⚠️ ANOMALI TESPİT EDİLDİ - Cluster:", cluster)
    alert_admin()
else:
    print("✅ Normal trafik")
```

---

## Öğrendiklerim: Ağ Güvenliği Dersleri

**Unsupervised Learning keşfetme aracıdır:** Etiketler olmadan veri bize sürprizler gösterir.

**Scaling hayatidir:** Scaled vs. unscaled veriler tamamen farklı kümeler verdi.

**Optimal küme sayısı denemeyle bulunur:** Elbow method, Silhouette analizi, domain knowledge - hepsi önemli.

**Kümeler otomatik etiketlenmez:** Machine learning sayıları grup etse de, bu grupların "ne" olduğunu biz bulmalıyız.

**Ensemble detection gerekir:** Sadece clustering yeterli değil. Pattern matching, anomaly scoring, user behavior analysis gibi katmanlara ihtiyaç var.

---

## Pratik Uygulama: SOC (Security Operation Center) Gözlüğüyle

Bu kümelerin kullanım alanları:

- **Real-time anomaly detection:** Yeni flow'lar "saldırı kümelerinden" ne kadar uzak?
- **Investigative lead:** Bir saldırı bulunduysa, benzer pattern'leri arayabiliriz.
- **Baseline model:** Normal trafik modeli oluşturduk - sapmaları izleriz.
- **False positive azaltma:** Genuine port scanning'i (yönetici çalışması) normal kümede tuttuk.

---

## Sonuç: Görünmeyen Tehditler

Ağ trafiği kitap sayfaları gibidir - doğru "lense" bakarsanız, her satırda hikaye vardır. Clustering bu lens'i sağlıyor. Makine öğrenmesi sayesinde, bir SOC analisti çalışanı, daha yapabileceği işler bulabiliyor.

Güvenlik hiçbir zaman %100 değildir ama her geçen gün daha iyi hale gelir.

---

## İletişim

📧 E-mail: harunemirhan826@gmail.com 💼 LinkedIn: https://www.linkedin.com/in/haremir826/ 🔗 GitHub: https://github.com/haremir

Siber güvenlik yolculuğunuzda başarılar dilerim! 🔐

---

> **Not:** UNSW-NB15 veri seti açık kaynaktır ve NetworkX, Zeek gibi araçlarla flow'lar çıkarılmıştır. Kendi ağınız için benzer analysis yapabilirsiniz!