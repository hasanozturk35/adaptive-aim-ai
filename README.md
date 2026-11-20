# Adaptif AI Nişan Alma Oyunu

Bir arcade tarzı oyunda, oyuncunun performansına dinamik olarak uyum sağlayan adaptif bir yapay zekaya sahip hedef kullanılan interaktif bir projedir.

## 🎮 Oyun Özellikleri

### Temel Mekanik
- **Oyuncu**: Ekran altında konumlandırılan çemberin her yönde hareket edebilir
- **Hedef**: Ekranda hareket eden kırmızı çember - oyuncunun vurmayı amaçladığı hedef
- **Atış Mekanizmesi**: Mouse tıklaması ile hedef yönünde ışın gönder

### Adaptif AI Sistemi

Hedef yapay zekası, oyuncunun performansını sürekli analiz ederek davranışını değiştirir:

#### 📊 Analiz Edilen Metrikler:
1. **İsabet Yüzdesi**: Son atışlardaki başarı oranı
2. **Atış Sıklığı**: Oyuncunun saniyede kaç atış yapması
3. **Atış Açıları**: Oyuncunun hangi açılardan atış yaptığı
4. **Tepki Süresi**: Oyuncunun atışlar arasındaki zaman farkı

#### 🤖 AI Öğrenme Mekanizması:

**Zorluk Seviyesi Dinamiği:**
- Oyuncu %65+ başarı oranında → Zorluk artar
- Oyuncu %35- başarı oranında → Zorluk azalır
- Zorluk seviyesi 0.0 (çok kolay) ile 1.0 (çok zor) arasında

**Davranış Stratejileri:**

1. **Wander (Dolaşma)** - Düşük zorlukta aktif
   - Basit rastgele hareket
   - Tahmin edilebilir yön değişimleri

2. **Evade (Kaçma)** - Orta-yüksek zorlukta
   - Oyuncudan aktif olarak kaçma
   - Mesafeye göre kaçma hızını artırma
   - Yan hareketler ekleyerek daha zor hedef haline gelme

3. **Fake Dodge (Sahte Hareket)** - Yüksek zorlukta
   - Beklenmeyen yön değişiklikleri
   - Oyuncuyu aldatan hareket modelleri

4. **Sprint (Hızlı Kaçış)** - En yüksek zorlukta
   - Maximum hızda kaçma
   - Ani, güç hareketler

#### 🧠 Makine Öğrenmesi Bileşenleri:

**1. Açı Öğrenimi:**
```
learned_angles_to_avoid = {
    45: 0.8,   # 45 derecede sık atış yapılıyor
    90: 0.6,   # 90 derecede atış yapılıyor
    180: 0.4,  # 180 derecede az atış yapılıyor
}
```
- Oyuncunun en çok attığı açıları öğrenir
- Başarılı atışlara daha yüksek ağırlık verir (3x)
- Bu açılardan daha çok kaçmaya çalışır

**2. Strateji Seçimi:**
- Düşük zorluk → Dolaşma strateji tercih edilir
- Orta zorluk → Kaçma + dolaşma karışımı
- Yüksek zorluk → Sahte hareketler, hızlı kaçış kombinasyonları

**3. Adaptif Parametre Ayarlaması:**
- **Hız**: 2-8 arası, zorlukla beraber artma
- **Kaçınma Gücü**: 0.1-0.7 arası, zorlukla beraber artma
- **Strateji Rastgeleliği**: 0.7-0.2 arası, zorluk arttıkça strateji daha belirgin hale gelme

## 🎮 Oynanış

### Kontroller:
- **← → ↑ ↓**: Oyuncuyu hareket ettir
- **Mouse Sol Tıklama (veya OK)**: Atış yap
- **M**: Manuel hedefleme modunu aç/kapat
- **W A S D**: Manuel modda nişangahı hareket ettir
- **F**: Manuel modda nişangahın olduğu yere ateş et
- **SPACE**: Oyunu durdur/devam ettir
- **R**: Oyunu sıfırla
- **ESC**: Çıkış

### Oyun Amacı:
Hedefi mümkün olduğunca çok kez vur. Oyun arttıkça:
1. AI daha düşük hız kazanır
2. Kaçınma hareketleri daha güçlü hale gelir
3. Daha karmaşık stratejiler uygulanır
4. Hedef öğrendiği açılardan daha çok kaçar

## 📁 Proje Yapısı

```
oyun-makineogrenmesi/
├── README.md              # Bu dosya
├── requirements.txt       # Python bağımlılıkları
├── main.py               # Oyunu başlatmak için
├── train.py              # Toplanan veriyle ML modellerini eğitir
├── src/
│   ├── config.py         # Oyun konfigürasyonu
│   ├── player_stats.py   # Oyuncu istatistikleri ve analiz
│   ├── ai_target.py      # Adaptif AI hedef sistemi
│   ├── data_logger.py    # Her atışı CSV'ye kaydeder
│   ├── model_select.py   # Oyunda kullanılacak modeli seçer
│   └── game.py           # Ana oyun dosyası
├── data/                 # training_shots.csv (oyun oynarken oluşur, repoda yok)
└── models/               # Eğitilmiş modeller ve metrics.json
```

## 🚀 Başlangıç

### Gereksinimler:
- Python 3.9+
- pygame, numpy, scikit-learn, joblib (sürümler `requirements.txt` içinde)

### Kurulum:

1. Bağımlılıkları yükle:
```bash
pip install -r requirements.txt
```

2. Oyunu çalıştır:
```bash
python main.py
```

## 🤖 Makine Öğrenmesi: İsabet Tahmini

Kural tabanlı adaptif AI'nin yanında, hedef bir sınıflandırma modeliyle de oyuncuya karşı savunma yapar: her atış anında model **"bu atış isabet eder mi?"** olasılığını tahmin eder. Tahmin yüksekse (> 0.5) hedef kaçma moduna geçer ve kaçınma gücü artar.

### Akış

1. **Veri toplama:** Oyun her atışı `data/training_shots.csv` dosyasına yazar (oyuncu/nişan konumu, açı, mesafe, hedefin konumu ve hızı, zorluk seviyesi, sonuç: `hit` / `miss`).
   > Not: Oyun her açılışta bu dosyayı sıfırlar, yani dosya her zaman son oturumun verisini içerir.
2. **Eğitim:** Bir oturum oynadıktan sonra:
   ```bash
   python train.py
   ```
   13 sayısal özellik üzerinde dört model eğitilir ve karşılaştırılır:
   - Logistic Regression
   - Random Forest
   - SVM (RBF kernel)
   - Polinom özellikler (derece 2) + Logistic Regression

   Modeller `models/` klasörüne kaydedilir, metrikler `models/metrics.json` dosyasına yazılır ve F1 skoru en yüksek olan `best_model.joblib` olarak kopyalanır.
3. **Oyunda kullanım:** Oyun açılışta modeli yükler. Hangi modelin yükleneceği [config.py](src/config.py) içindeki `FORCE_MODEL` ile seçilir; `None` yapılırsa `best_model.joblib` kullanılır.
4. **Oyun içi eğitim:** Her 10 atışta bir, o oturumun isabetli atışları ve rastgele üretilen sentetik ıskalar ile küçük bir Random Forest yeniden eğitilir (`models/online_rf.joblib`). Böylece model oyun sırasında da oyuncuya uyum sağlar.

### Sonuçlar

Repodaki modeller az sayıda atışla eğitildi (test seti: 52 atış). Atışların ~%85'i ıskalama:

| Model | Accuracy | Precision | Recall | F1 | ROC AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.56 | 0.17 | 0.57 | **0.26** | 0.55 |
| Random Forest | 0.85 | 0.00 | 0.00 | 0.00 | 0.55 |
| SVM (RBF) | 0.60 | 0.15 | 0.43 | 0.22 | 0.54 |
| Polinom + Logistic | 0.63 | 0.13 | 0.29 | 0.17 | 0.45 |

**Yorum:** Sonuçlar ön çalışma niteliğinde ve modeller henüz anlamlı bir tahmin gücüne sahip değil:

- **Veri çok az ve dengesiz.** Atışların büyük kısmı ıskalama; Random Forest'ın %85 accuracy'si sadece her atışa "ıska" demesinden geliyor (precision ve recall 0). Bu yüzden ana metrik olarak accuracy yerine F1 kullanıldı.
- **AUC değerleri 0.5'e yakın**, yani modeller isabet ile ıskayı rastgele tahminden pek iyi ayıramıyor.
- **İyileştirme için:** Birden fazla oturumun verisini biriktirmek (şu an her açılışta sıfırlanıyor), hedefin atış sonrası hareketini özellik olarak eklemek ve çapraz doğrulama ile değerlendirmek.

## 🧮 AI Öğrenme Matematikselliği

### Zorluk Seviyesi Hesaplaması:

```
difficulty_new = difficulty_old + adaptation_speed  (if hit_pct > 0.65)
difficulty_new = difficulty_old - adaptation_speed  (if hit_pct < 0.35)
```

Limitler:
- MIN_DIFFICULTY = 0.3
- MAX_DIFFICULTY = 1.0
- ADAPTATION_SPEED = 0.05

### Açı Öğrenmesi:

```
learned_angles[angle] += learning_rate  (for hits)
learned_angles[angle] *= 0.95           (decay - unutma)
```

### Kaçınma Gücü:
```
evasion_strength = 0.1 + 0.6 * difficulty
```

Örnek:
- Zorluk 0.3 → Kaçınma gücü = 0.28
- Zorluk 0.7 → Kaçınma gücü = 0.52
- Zorluk 1.0 → Kaçınma gücü = 0.7

## 📈 Performans İzleme

Oyun süresi boyunca aşağıdaki metrikler izlenir:

- **İsabet Yüzdesi**: Son 30 atışta başarı oranı
- **Toplam Atış**: Yapılan toplam atış sayısı
- **Atış Sıklığı**: Saniye başına atış sayısı
- **Hareketli Açılar**: En çok kullanılan atış açıları

Tüm bu metrikler AI'nin uyum sağlamasını etkiler.

## 🎯 Gelişim Süreci

Oyun oynamaya başladığınızda:

1. **İlk 30 Saniye**: AI basit dolaşma yapıyor, hedef kolay
2. **1-2 Dakika**: İsabet oranını yaklaşık %50 civarında tutmaya çalış
3. **2-5 Dakika**: AI kaçma stratejilerini öğrenmeye başlıyor
4. **5+ Dakika**: AI karmaşık stratejiler (fake dodge, sprint) kullanıyor

## 🔬 Kodu Özelleştirme

[config.py](src/config.py) dosyasında aşağıdaki parametreleri değiştirebilirsin:

- `DIFFICULTY_THRESHOLD`: Zorluk seviyesi artma eşiği
- `ADAPTATION_SPEED`: AI'nin ne kadar hızlı uyum sağladığı
- `AI_LEARNING_RATE`: Açı öğrenme hızı

## 📝 Notlar

Bu oyun, adaptif zorluk seviyesi kullanan modern oyunların nasıl çalıştığını gösterir. Fortnite, Counter-Strike gibi oyunlarda benzer sistemler vardır.

## 📚 Kaynaklar

- Reinforcement Learning konseptleri
- Adaptive AI davranışları
- Dynamic difficulty adjustment

---

**Eğlenceli oyun oynaman dilerim! 🎮**
