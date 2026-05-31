---
title: "Ev Elektrik Tüketimini Tahmin Etmek: Regresyon ile Zaman Serisi Analizi"
date: "2025-10-28"
description: "Bu yazıda, UCI Machine Learning Repository'den alınan 'Household Power Consumption' veri seti üzerinde ev elektrik tüketimi tahmini yapan bir proje ele alınıyor. 2 milyonun üzerinde dakikalık kayıt içeren bu veri setinde lag, rolling ve cyclical feature engineering teknikleri uygulandı; Simple Linear Regression, Multiple Linear Regression, Polynomial Regression, Random Forest ve AutoGluon modelleri karşılaştırıldı. En iyi performansı AutoGluon gösterdi (RMSE: 0.345, R²: 0.923). Geçmiş tüketim değerleri ve saat bilgisinin tahmin gücünü en çok belirleyen özellikler olduğu ortaya çıktı."
tags:
  - Time Series Analysis
  - Regression Models
  - Energy Analytics
  - Feature Engineering
cover: "/blog/elektrik-cover.png"
---

Elektrik faturanızın neden bazen beklenmedik şekilde yükseldiğini hiç merak ettiniz mi? Ya da bir sonraki saatte ne kadar elektrik tüketeceğinizi önceden bilseydiniz, enerji kullanımınızı optimize edebilir miydiniz? İşte bu yazıda, makine öğrenmesi ile ev elektrik tüketimini tahmin etme projesine derin bir dalış yapacağız.

---

## Proje Hikayesi: Neden Bu Veri Seti?

UCI Machine Learning Repository'den alınan "Household Power Consumption" veri seti, tam 4 yıllık süreçte bir evin her dakika kaydedilen elektrik tüketim verilerini içeriyor. 2 milyonun üzerinde kayıt, 6 farklı ölçüm değişkeni... İnanılmaz zengin bir veri hazinesi!

Ama işin güzel tarafı şu: Bu sadece bir elektrik sayacının kayıtları değil, aslında bir ailenin yaşam tarzının, günlük rutinlerinin, hatta mevsimsel alışkanlıklarının dijital izdüşümü. Her veri noktası bir hikaye anlatıyor.

---

## CRISP-DM ile Başlangıç

Tıpkı bir mimar nasıl binanın planını çizmeden inşaata başlamazsa, biz de veri bilimi projelerine metodolojisiz atlanamayız. CRISP-DM (Cross-Industry Standard Process for Data Mining) burada devreye giriyor.

### 1. İş Anlayışı: Hedefimiz Net

İlk soru: "Ne başarmaya çalışıyoruz?"

Basit: Bir sonraki saatin elektrik tüketimini tahmin etmek. Ama neden? Çünkü:

- Enerji şirketleri yük dengelemesi yapabilir
- Kullanıcılar tüketim alışkanlıklarını optimize edebilir
- Akıllı ev sistemleri proaktif kararlar alabilir

---

### 2. Veri Anlayışı: İlk Karşılaşma

Veri setini yükledikten sonra ilk gözlem: ~%1.25 eksik veri. Bunlar "?" karakteriyle işaretlenmiş. Klasik bir veri kalitesi problemi ama paniğe gerek yok.

**Verinin yapısına bakalım:**

| Değişken | Açıklama |
|---|---|
| Global_active_power | Ana tüketim (kW) - hedef değişkenimiz |
| Global_reactive_power | Reaktif güç |
| Voltage | Voltaj değeri |
| Global_intensity | Akım şiddeti |
| Sub_metering_1, 2, 3 | Farklı devrelerin tüketimleri |

**İlk keşifler heyecan vericiydi:**

- Gece saatlerinde tüketim dibe vuruyor (02:00-05:00 arası)
- Akşam 18-21 arası peak saatler
- Hafta sonları ortalama %12 daha az tüketim

---

### 3. Veri Hazırlığı: Kirli İşlerin Zamanı

Veri biliminin %80'i buradadır derler. Haklılar da.

**Eksik Değerlerle Savaş:** "?" karakterlerini tespit ettik ve NaN'a çevirdik. Sonra stratejik bir karar: Bu değerler %1.25'lik küçük bir oran olduğu için direkt çıkardık. Daha büyük bir oran olsaydı imputation (doldurma) yöntemlerine başvururduk.

**Datetime İşlemleri:** Tarih ve saat bilgileri ayrı kolonlardaydı. Birleştirdik ve tek bir Datetime kolonu oluşturduk. Sonra pandas'ın muhteşem datetime özelliklerini kullanarak:

- Saat, gün, ay, yıl çıkardık
- Haftanın günü (Monday=0, Sunday=6)
- Hafta sonu mu? (binary flag)
- Mevsim bilgisi
- Günün zamanı (sabah, öğle, akşam, gece)

**Outlier Temizliği:** IQR (Interquartile Range) yöntemiyle aykırı değerleri tespit ettik. Çok uç değerleri kırptık (clip) ama tamamen çıkarmadık - çünkü bazen yüksek tüketim gerçekten de olabilir (misafir geldiğinde, parti yapıldığında vb.).

---

### 4. Feature Engineering: Sihrin Gerçekleştiği Yer

Zaman serisi problemlerinde ham veri yeterli değildir. Veriye "zaman bilinci" kazandırmamız gerekiyor.

**Lag Features (Gecikmeli Özellikler):** En önemli keşif: 1 saat önceki tüketim değeri, şu anki tüketimi tahmin etmek için en güçlü özellik!

```python
df['Global_active_power_lag_1'] = df['Global_active_power'].shift(1)
df['Global_active_power_lag_24'] = df['Global_active_power'].shift(24)
df['Global_active_power_lag_168'] = df['Global_active_power'].shift(168)  # 1 hafta
```

Mantık basit: Dünkü saat 20:00'deki tüketim, bugünkü 20:00'deki tüketim hakkında çok şey söylüyor.

**Rolling Features (Yuvarlanan Pencere):** Son 24 saatin ortalaması, standart sapması, minimum ve maksimum değerleri. Bu özellikler "trend" bilgisini yakalıyor:

```python
df['rolling_mean_24'] = df['Global_active_power'].rolling(window=24).mean()
df['rolling_std_24'] = df['Global_active_power'].rolling(window=24).std()
```

**Cyclical Features (Döngüsel Özellikler):** Saat 23 ile saat 0 arasında matematiksel olarak 23 birim fark var ama gerçekte sadece 1 saat. Bu problemi sin/cos transformasyonuyla çözdük:

```python
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
```

Bu matematiksel bir güzellik: Döngüsel değişkenleri sürekli bir uzayda temsil ediyoruz.

---

### 5. Modelleme: Karşılaştırma Zamanı

Beş farklı yaklaşımı denedik:

**Simple Linear Regression:** En basit model. Sadece Global_active_power_lag_1 ile tahmin.

| Metrik | Sonuç |
|---|---|
| RMSE | 0.641 |
| R² | 0.756 |

Sonuç: Fena değil ama yeterli değil.

---

**Multiple Linear Regression:** Tüm özellikleri kullandık.

| Metrik | Sonuç |
|---|---|
| RMSE | 0.601 |
| R² | 0.789 |

---

**Polynomial Regression (degree=2):** Özellikler arası etkileşimleri yakalamak için polinom terimleri ekledik:

| Metrik | Sonuç |
|---|---|
| RMSE | 0.534 |
| R² | 0.832 |

Güzel bir iyileşme!

---

**Random Forest:** 100 ağaç, maksimum derinlik 20:

| Metrik | Sonuç |
|---|---|
| RMSE | 0.421 |
| R² | 0.887 |

Artık işler ciddileşmeye başladı. Random Forest'ın ensemble gücü fark yaratıyor.

---

**AutoGluon (AutoML):** Büyük finali bıraktık sona. AutoGluon'a 10 dakika süre verdik ve geri çekilip izledik:

| Metrik | Sonuç |
|---|---|
| RMSE | **0.345** |
| R² | **0.923** |

**Kazanan!** AutoGluon bir WeightedEnsemble modeli oluşturdu - Random Forest, XGBoost ve LightGBM'in zeki bir kombinasyonu.

---

### 6. Değerlendirme: Sayılardan Öteye

RMSE 0.345 ne demek pratikte? Ortalama 0.345 kW hata yapıyoruz. Bir ev için ortalama tüketim 1-2 kW civarında olduğunda, bu oldukça iyi bir tahmin.

**Feature Importance Analizi:**

| Özellik | Önem Skoru |
|---|---|
| Global_active_power_lag_1 | %28.3 |
| hour | %15.7 |
| rolling_mean_24 | %12.4 |
| dayofweek | %9.8 |
| Voltage | %8.1 |

Yani geçmiş değerler ve zaman bilgisi en önemliler. Mantıklı!

**Residual Analizi:** Hatalar normal dağılıma yakın, sistematik bir sapma yok. Model genel olarak dengeli tahminler yapıyor.

---

### 7. Deployment: Gerçek Dünyaya Geçiş

Modeli joblib ile kaydettik. Production ortamında kullanım senaryosu:

```python
import joblib
import pandas as pd

# Model yükle
model = joblib.load('models/automl/best_model.pkl')

# Son 1 saatlik veriyi al
last_hour_data = get_latest_hour_data()

# Feature engineering uygula
features = create_features(last_hour_data)

# Tahmin
prediction = model.predict(features)
print(f"Sonraki saat tahmini: {prediction[0]:.2f} kW")
```

---

## Öğrendiklerim: Altın Notlar

**Zaman serisi için feature engineering hayatidir:** Ham veri hiçbir zaman yeterli değildir. Lag, rolling ve cyclical özellikleri mutlaka ekleyin.

**AutoML güçlü ama anlamadan kullanmayın:** AutoGluon muhteşem sonuç verdi ama neden iyi çalıştığını bilmek kritik. Traditional modelleri önce denemek size intuition kazandırıyor.

**Veri kalitesi > Model seçimi:** Eksik değerleri doğru işlemek, outlier'ları anlamak ve uygun şekilde ele almak, en fancy modelden daha önemli.

**Validation stratejisi önemli:** Zaman serisi problemlerinde random split kullanmayın! Kronolojik split yapın - geçmişle geleceği tahmin edin, geleceğe geçmişi karıştırmayın.

**Görselleştirme ihmal edilmemeli:** Daily pattern, weekly pattern, seasonal decomposition grafikleri veriyi anlamamızı sağladı. Sayılar önemli ama grafikler hikayeyi anlatır.

---

## Sonuç: Bir Projeksiyon

Bu proje sadece elektrik tahmini değil, aslında zaman serisi analizi için bir blueprint. Aynı yaklaşım:

- Hisse senedi fiyat tahmini
- Hava durumu tahmini
- Satış projeksiyonu
- Trafik yoğunluğu tahmini

gibi sayısız probleme uyarlanabilir.

Önemli olan metodoloji, sistematik yaklaşım ve veriyi anlama sanatı. Geri kalanı teknik detay.

---

## İletişim

📧 E-mail: harunemirhan826@gmail.com 💼 LinkedIn: https://www.linkedin.com/in/haremir826/ 🔗 GitHub: https://github.com/haremir

Veri bilimi yolculuğunuzda başarılar dilerim! 🚀

---

> **Not:** Bu projede kullanılan tüm kod ve notebook'lar GitHub repository'mde mevcut. Denemek, geliştirmek veya sorularınızı paylaşmak için çekinmeyin!