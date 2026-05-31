---
title: "Windows Event Log'larında Birliktelik Kuralları: Sistem Logs'un Gizli Dili"
date: "2025-11-15"
description: "Bu yazıda, Kaggle'dan alınan 158.184 Windows Event Log kaydı üzerinde Association Rule Mining uygulanıyor. 9 farklı makineye ait Information, Warning, Error ve Type0 log türleri 'market basket' formatına çevrilerek Apriori ve FP-Growth algoritmaları ile analiz edildi. 'Error görüldüğünde Warning her zaman eşlik eder (Confidence: %100)' gibi güçlü birliktelik kuralları ortaya çıktı. Bu kuralların proaktif alarm sistemleri kurarak sorunları önceden tespit etmekte nasıl kullanılabileceği gösterildi."
tags:
  - Association Rule Mining
  - Apriori Algorithm
  - Windows Event Logs
  - Anomaly Detection
cover: "/blog/eventlog-cover.png"
---

Bilgisayarınızı açtığınızda neler oluyor? Binlerce event log üretiliyor. Information, Warning, Error... İşletim sistemi muhabbet ediyor kendisiyle ama biz hiç dinlemiyoruz. Ya peki bu muhabbetin içinde saklı kalıplar varsa? "Error görüldüğünde Warning de olmasi gerekir mi? Belki de sistem sağlığının bir göstergesi?" İşte bu yazıda, Windows Event Log'larında Association Rule Mining ile bu gizli dili deşifre edeceğiz.

---

## Proje Hikayesi: Logs'un Sesi

Windows Event Viewer'ı açıp Event ID'ler, EntryType'lar, Message'ları gördüğünüzde, sanki karmaşık bir kütüphanede geziyorsunuz gibi hissedersiniz. Ama bir sistem yöneticisinin gözüyle bakarsanız, burada hikayeler var.

- "Neden bu makinede hep Error ve Warning bir arada görülüyor?"
- "Information log'ları diğer makinelerde de bu kadar mı sık?"
- "Eğer bunu öngörebilsem, sorun çıkmadan alarm kurabilirim!"

İşte bu sorular bizi bu projeye attı. 158.184 event log kaydı, 9 makine, ve 4 tip EntryType - ama içinde nasıl desenler saklı?

---

## CRISP-DM: Association Rule Mining Yolculuğu

### 1. İş Anlayışı: Sistem Sağlığının Pusulaları

"Ne başarmaya çalışıyoruz?"

Cevap: Windows Event Log'larındaki EntryType'lar arasında güçlü birliktelik kuralları bularak, proaktif sistem izleme ve alarm sistemleri geliştirebilmek.

**Neden?** Çünkü:

- System log'ları kendi aralarında "konuşurlar" - desenler vardır
- Bu desenleri bilebilirsen, sorun çıkmadan reaction system kurabilirsin
- Bir makinede "Error → Warning" kuralı varsa, error görünce warning bekleyebilirsin

---

### 2. Veri Anlayışı: 158.184 Log Kaydı'nın İçine Bakış

Veri seti Kaggle'dan alındı - real Windows Event Log'ları. İçinde ne var?

**Temel Kolonlar:**

| Kolon | Açıklama |
|---|---|
| MachineName | 9 farklı bilgisayar (Machine1, Machine2, ..., Machine9) |
| EntryType | 4 kategorisi var (aşağıda) |

**EntryType Kategorileri:**

| Tür | Anlamı |
|---|---|
| Information | "Her şey yolunda" mesajı |
| Warning | "Dikkat et, sorun olabilir" uyarısı |
| Error | "Sorun var!" hatası |
| Type 0 | Bilinmeyen/sınıflandırılamayan türü |

**Sorular Hemen Çıkıyor:**

- Hangi makinelerde en çok error var?
- Error görüldüğünde warning de görülüyor mu?
- Information log'ları bağımsız mı, yoksa diğerleriyle ilişkili?

---

### 3. Veri Hazırlığı: Transaction Format'ına Çevirme

Association Rule Mining'in sihri burada başlıyor. Normale bakarsan:

```
MachineName | EntryType
Machine1    | Information
Machine1    | Warning
Machine1    | Error
Machine2    | Information
...
```

Ama biz bunu "market basket" formatına çevirmeliyiz:

```
Transaction (Makine) | Items (EntryType'lar)
Machine1             | Information, Warning, Error
Machine2             | Information, Warning, Type0
Machine3             | Information, Type0
...
```

Yani her makine bir transaction, her EntryType de bir item. Mantık: "Bu makine hangi log tiplerini üretiyor?"

**Binary Matrix Oluşturma:**

```python
pivot = pd.crosstab(df['MachineName'], df['EntryType'])
binary_matrix = (pivot > 0).astype(int)
```

Sonuç:

| MachineName | Information | Warning | Error | Type0 |
|---|---|---|---|---|
| Machine1 | 1 | 1 | 1 | 0 |
| Machine2 | 1 | 1 | 0 | 1 |
| Machine3 | 1 | 0 | 1 | 1 |
| ... | | | | |

Bu binary matrix'i association algorithms'a veriyoruz.

---

### 4. Modelleme: Apriori vs FP-Growth Düellosu

#### A. Apriori Algoritması

Temel fikir: Eğer bir itemset sık ise, onun subsetleri de sıktır. Yani:

- Eğer (Error, Warning) sık ise
- O zaman (Error) ve (Warning) da sık olmalı

```python
from mlxtend.frequent_patterns import apriori

frequent_itemsets = apriori(
    binary_matrix,
    min_support=0.2,  # En az %20'de görülmesi gerekir
    use_colnames=True
)
```

**Minimum Support = 0.2 (20%) Neden?** 9 makinenin %20'si = yaklaşık 2 makine. Çok rare olmayan ama çok yaygın da olmayan kuralları buluyoruz.

Sonuç: **15 frequent itemset** bulundu.

---

#### B. FP-Growth Algoritması

Apriori'nin daha hızlı versiyonu. Aynı sonuçları verir ama RAM daha az tüketir.

```python
from mlxtend.frequent_patterns import fpgrowth

frequent_itemsets = fpgrowth(
    binary_matrix,
    min_support=0.2,
    use_colnames=True
)
```

Sonuç: Apriori ile aynı **15 frequent itemset**.

Performans test ettik, FP-Growth biraz daha hızlı ama farkı minimal. Apriori daha basit ve readable.

---

#### C. Association Rules Üretme

Şimdi itemset'lerden kurallar çıkarıyoruz:

```python
from mlxtend.frequent_patterns import association_rules

rules = association_rules(
    frequent_itemsets,
    metric="confidence",
    min_threshold=0.5  # %50 confidence
)
```

İşte bu adımda, X => Y formatında kurallar doğuyor:

- Error => Warning
- (Error, Warning) => Information
- Information => Type0
- vb.

---

### 5. Değerlendirme: Metrikleri Anlamak

**Support:** Kuralın kaç transaction'da görüldüğü

```
Error => Warning
Support = 7/9 = 77.8%
```
Yani 9 makinenin 7'sinde, Error ve Warning bir arada görülüyor.

---

**Confidence:** Antecedent (öncül) varsa, consequent (sonuç) olma olasılığı

```
Error => Warning
Confidence = 100%
```
Yani Error görüldüğünde, HER ZAMAN Warning de görülüyor!

---

**Lift:** X ve Y'nin bağımlılık derecesi

```
Lift = P(X ∩ Y) / (P(X) * P(Y))

Error => Warning
Lift = 1.286
```

- `> 1` → Pozitif korelasyon (Error ve Warning bir arada görülme eğilimi var)
- `= 1` → Bağımsız
- `< 1` → Negatif korelasyon

---

### 6. Ana Bulgular: Sistemin Kendi Hikayesi

**Top 5 Kural (Lift'e göre):**

**Error => Warning**
- Support: 77.8% | Confidence: 100% | Lift: 1.286
- Yorum: Güçlü ilişki. Error görülünce Warning bekleyebiliriz.

**Warning => Error**
- Support: 77.8% | Confidence: 85.7% | Lift: 1.286
- Yorum: Simetrik ilişki. Ama biraz daha zayıf (sadece %85 confidence).

**(Error, Warning) => Information**
- Support: 55.6% | Confidence: 66.7% | Lift: 1.0
- Yorum: Information bağımsız görülüyor. Error ve Warning varsa da, yoksa da Information ortaya çıkıyor.

**Type0 => Information**
- Support: 44.4% | Confidence: 100% | Lift: 1.5
- Yorum: Type0 görüldüğünde DAIMA Information da var!

**Information => Type0**
- Support: 44.4% | Confidence: 66.7% | Lift: 1.5
- Yorum: Information varsa, Type0 olma olasılığı %66.7.

---

### 7. Deployment: Proaktif Alarm Sistemi

Bu kuralları nasıl kullanırız?

**Senaryo 1: Error Alarmı**

```python
# Eğer Error görülürse
if 'Error' in event_types:
    # Warning beklemek normal (kuraldan biliyoruz)
    # Eğer Warning YOKSA => alarm ver!
    if 'Warning' not in event_types:
        ALERT("Sistem anormali! Error var ama Warning yok!")
```

**Senaryo 2: Type0 Alarmı**

```python
# Eğer Type0 görülürse
if 'Type0' in event_types:
    # Information HER ZAMAN varsa (Confidence: 100%)
    # Eğer Information YOKSA => ciddi sorun!
    if 'Information' not in event_types:
        CRITICAL_ALERT("Type0 ama Information yok! Sistem kompromize olmuş olabilir!")
```

**Senaryo 3: Anomali Tespiti**

```python
# Destek olmayan kombinasyon bulundu mu?
if rule_found == False:
    ANOMALY_LOG("Bu kombinasyon bizim kurallarımızda yok!")
    investigate_machine()
```

---

## Öğrendiklerim: Log Sistemi Dersleri

**Bağlamsal veriler çok değerli:** Bireysel log'lar değersiz ama bir arada bakınca anlamlar ortaya çıkıyor.

**Association Mining "bilmek" değil "anlama" demek:** %77.8 support sadece sayı değil, sistem mimarisinin bir göstergesi.

**Confidence > Support:** %78 makinede görülse de, consistency (confidence) daha önemli. %100 confidence daha güvenilir.

**Lift, gerçek ilişkiyi gösterir:** Lift 1.0'a yakın itemset'ler aslında bağımsız - kaçırabilirsin.

**Minimum Support tuning kritik:** Çok yüksek olursa (%50), çok rare kurallar bulursun. Çok düşük olursa (%1), noise'a batırsın.

**Kontekst her şey:** Transaction'ın "makine" olması burada mantıklı. Başka context (zaman aralığı, user, process type) seçseydin, bambaşka kurallar bulurdun.

---

## Pratik Uyarılar: Sistem Yöneticisi Gözlüğüyle

- Tek kuralı değil, kurallar topluluğunu izle
- Lift 1.0'dan uzak kuralları prioritize et
- Seasonal patterns'i dikkate al (aylar değişebilir)
- Machine learning model'le combination yap (anomaly detection için)

---

## Sonuç: Logs Sessiz Değil, İzlediğimiz Yok

Windows Event Log'ları sistem sağlığının kronikası gibidir. Sadece error saymak değil, onların diğer eventlerle nasıl ilişkili olduğunu bilmek proaktif bakım yapmanıza yardımcı olur.

Association Rule Mining bu ilişkileri gün ışığına çıkarıyor. Bir Error görüldüğünde Warning beklemesi normal mi? Evet. Ama Warning olmadıysa? Dikkat et.

Sistem size çiçekle konuşuyor. Sadece dinle.

---

## İletişim

📧 E-mail: harunemirhan826@gmail.com 💼 LinkedIn: https://www.linkedin.com/in/haremir826/ 🔗 GitHub: https://github.com/haremir

Windows Event Log analizi ve sistem yönetimi yolculuğunuzda başarılar dilerim! 🖥️

---

> **Not:** Bu metodoloji sadece Windows Event Log'ları için değil. Aynı teknik e-ticaret (market basket analysis), tıp (symptom co-occurrence), sosyal ağlar (user behavior patterns) gibi alanlarda da uygulanabilir. Context değişir, lojik kalır!