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
├── src/
│   ├── config.py         # Oyun konfigürasyonu
│   ├── player_stats.py   # Oyuncu istatistikleri ve analiz
│   ├── ai_target.py      # Adaptif AI hedef sistemi
│   └── game.py           # Ana oyun dosyası
└── main.py               # Oyunu başlatmak için
```

## 🚀 Başlangıç

### Gereksinimler:
- Python 3.8+
- pygame
- numpy

### Kurulum:

1. Bağımlılıkları yükle:
```bash
pip install -r requirements.txt
```

2. Oyunu çalıştır:
```bash
python main.py
```

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
