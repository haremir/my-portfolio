---
title: "Kredi Kartı Dolandırıcılık Tespiti: Makine Öğrenmesi ile Güvenlik Çözümü"
date: "2025-05-15"
description: "Bu yazıda, 284.807 işlem içeren ve yalnızca %0.17'si dolandırıcılık olan dengesiz bir kredi kartı veri seti üzerinde makine öğrenmesi tabanlı bir tespit sistemi geliştirilen 'Fraud Eye' projesi ele alınıyor. SMOTE ve örnekleme teknikleriyle sınıf dengesizliği giderildikten sonra XGBoost ve Logistic Regression modelleri karşılaştırıldı. XGBoost, 0.9799 ROC AUC ve 0.8222 Average Precision ile ana model olarak seçildi. Dolandırıcılık sinyallerinin belirli PCA bileşenlerinde ve düşük tutarlı işlemlerde yoğunlaştığı gözlemlendi."
tags:
  - Supervised Learning
  - XGBoost
  - SMOTE
  - Financial Security
  - Anomaly Detection
cover: "/blog/fraud-cover.png"
---

Kredi kartı dolandırıcılığı, dijitalleşen dünyada finansal güvenliği tehdit eden en büyük sorunlardan biri hâline geldi. Her yıl milyonlarca kullanıcı kötü niyetli kişilerin hedefi olurken, bankalar milyarlarca dolar zararla karşılaşıyor. Ben de bu soruna çözüm üretmek için yola çıktım. Geleneksel yöntemlerin yetersiz kaldığını görünce, makine öğrenmesi tekniklerini kullanarak etkili ve ölçeklenebilir bir dolandırıcılık tespit sistemi geliştirmeye karar verdim.

**Fraud Eye** adını verdiğim bu projede, veri analizi, ön işleme ve modelleme süreçlerinin her aşamasını dikkatle yürüttüm. Amacım, kredi kartı işlemlerinde anomalileri erken aşamada yakalayarak kullanıcıların güvenliğini artırmaktı.

---

## Veri Seti ve Keşifsel Veri Analizi (EDA)

### Kullandığım Veri Setinin Özellikleri

Projede kullandığım veri seti, her kredi kartı işlemi için detaylı bilgiler içeriyor:

| Özellik | Açıklama |
|---|---|
| Amount | İşlem tutarı |
| Time | Zaman damgası |
| v1–v28 | PCA ile dönüştürülmüş 28 özellik |
| Class | İşlem türü (0: normal, 1: dolandırıcılık) |

Veriler anonimleştirilmiş ve bazı değişkenler PCA ile özniteliklere ayrılmış durumda.

### İstatistiksel Görünüm

- **Toplam işlem sayısı:** 284.807
- **Dolandırıcılık işlemi oranı:** Yaklaşık %0.17

Bu ciddi dengesizlik, modelleme sırasında özel teknikler kullanmamı gerektirdi.

### Veri Görselleştirmeleri

- İşlem tutarlarının dağılımını incelediğimde, dolandırıcılıkların çoğunlukla düşük tutarlı işlemlerde yoğunlaştığını fark ettim.
- Zaman bazlı analizlerde ise dolandırıcılıkların belirli saat aralıklarında artış gösterdiğini gözlemledim.
- Ayrıca korelasyon matrisleri üzerinden öznitelikler arasındaki ilişkileri analiz ederek anlamlı desenleri ortaya çıkardım.

---

## Veri Ön İşleme

Modellemeye başlamadan önce veriyi iyileştirmek ve süreçleri optimize etmek için şu adımları izledim:

- Eksik veri analizi yaptım, eksik gözlem olmadığını tespit ettim.
- İşlem tutarlarında aykırı değerleri belirleyip sınırlandırdım.
- Özellikleri StandardScaler ile aynı ölçeğe çektim.
- SMOTE ve under/over sampling tekniğini kullanarak dolandırıcılık sınıfını dengeledim, ayrıca ağırlıklı sınıflandırma stratejilerini de değerlendirdim.

---

## Model Geliştirme

### XGBoost Modeli

XGBoost algoritmasını, güçlü öğrenme kapasitesi ve performansı nedeniyle tercih ettim. Parametreleri şu şekilde ayarladım:

- `learning_rate`: 0.01
- `max_depth`: 5
- `n_estimators`: 100

Hiperparametreleri GridSearchCV ile optimize ettim.

**Performans Metrikleri:**

| Metrik | Sonuç |
|---|---|
| ROC AUC Score | 0.9799 |
| Average Precision | 0.8222 |
| Accuracy | 0.9998 |

---

### Logistic Regression Modeli

Logistic Regression modelini, özellikle açıklanabilirliğin önemli olduğu durumlar için alternatif olarak denedim. L2 regularizasyon uyguladım.

**Performans Metrikleri:**

| Metrik | Sonuç |
|---|---|
| ROC AUC Score | 0.9723 |
| Average Precision | 0.7845 |
| Accuracy | 0.9992 |

---

## Model Değerlendirme

### Karşılaştırmalı Analiz

- Modelleri karşılaştırdığımda, XGBoost'un ROC eğrisinin daha üstte yer aldığını ve daha az false negative ürettiğini gördüm.
- Precision-Recall eğrisinin altında kalan alan (AUPRC) da XGBoost için daha yüksekti.
- Ayrıca özellik önemliliği analiziyle XGBoost, yorumlanabilir ve güvenilir sonuçlar sundu.

### Model Seçimi

Bu analizlerin sonunda, yüksek doğruluk ve düşük hata oranı nedeniyle XGBoost'u ana model olarak seçtim. Ancak, daha açıklanabilir bir yaklaşım gerektiğinde Logistic Regression modeline de başvurabileceğimi not ettim. Gerçek zamanlı sistemlerde hız ve yorumlanabilirlik gibi faktörler model seçiminde belirleyici olabilir.

---

## Sonuçlar ve İçgörüler

- Verilerdeki dolandırıcılık göstergeleri özellikle bazı PCA bileşenlerinde ve işlem tutarındaki anormalliklerde yoğunlaştı.
- XGBoost modeli, düşük dolandırıcılık oranına rağmen güçlü bir doğruluk ve duyarlılık sergiledi.

---

## Teknik Detaylar

### Kullandığım Kütüphaneler

- Python 3.8+
- pandas, numpy
- scikit-learn, xgboost
- matplotlib, seaborn

### Proje Yapısı

Projeyi, veri işleme, modelleme, görselleştirme ve değerlendirme adımlarını modüler şekilde organize ederek yönetilebilir bir yapı kurdum.

---

Bu projeyi geliştirirken hem makine öğrenmesi uygulamalarındaki yetkinliğimi hem de veri analizine olan hakimiyetimi derinleştirme fırsatı buldum. Geri bildirimleriniz ve katkılarınız, projeyi daha ileri taşımak adına benim için çok değerli.

İlginiz ve desteğiniz için teşekkür ederim!

📍 LinkedIn üzerinden bana ulaşabilirsiniz.