# BAŞLARKEN - Arcade Tarzı Adaptif AI Nişan Alma Oyunu

## 🎮 Proje Özeti

Bu proje, oyuncunun performansına dinamik olarak uyum sağlayan adaptif yapay zeka kullanan bir arcade tarzı nişan alma oyunudur. 

**Ana Özellikler:**
- ✅ Oyuncunun davranışını öğrenen AI
- ✅ Dinamik zorluk seviyesi (0.0 - 1.0 arası)
- ✅ 4 farklı AI strateji sistemi
- ✅ Makine öğrenmesi temelli açı öğrenmesi
- ✅ Gerçek zamanlı istatistik takibi

---

## 📁 Proje Dosyaları

```
oyun-makineogrenmesi/
├── main.py                    # Ana başlangıç dosyası
├── test_ai.py                 # AI sisteminin test dosyası (çalışır!)
├── terminal_game.py           # Terminal sürümü (pygame gerektirmez)
├── requirements.txt           # Bağımlılıklar
├── README.md                  # Oyun kılavuzu
├── TECHNICAL.md               # Teknik dokümantasyon
├── BAŞLARKEN.md              # Bu dosya
└── src/
    ├── config.py              # Konfigürasyon sabitleri
    ├── player_stats.py        # Oyuncu istatistikleri sistemi
    ├── ai_target.py           # Adaptif AI hedef sistemi
    └── game.py                # Pygame tabanlı ana oyun
```

---

## 🚀 Hızlı Başlangıç

### 1. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 2. AI Sistemini Test Et (Pygame gerektirmez)

```bash
python test_ai.py
```

Bu komut:
- ✓ Oyuncu istatistikleri sistemini test eder
- ✓ Zorluk seviyesi algoritmalarını doğrular
- ✓ Açı öğrenme mekanizmasını gösterir

### 3. Oyunu Başlat

```bash
python main.py
```

**Not:** Pygame derlemesi 2-5 dakika sürebilir (ilk kurulumda).

---

## 🎯 AI Öğrenme Mekanizması

### Temel Konsept

Hedef yapay zekası, oyuncunun davranışını analiz ederek kendi stratejisini dinamik olarak değiştirir:

```
Oyuncu Performansı
        ↓
    Analiz
        ↓
    Zorluk Ayarla
        ↓
    Strateji Değiştir
        ↓
    Hedef Davranışı Güncelle
```

### Analiz Edilen Metrikler

1. **İsabet Yüzdesi** ← Temel zorluk göstergesi
2. **Atış Sıklığı** ← Oyuncunun hızını anlamak
3. **Atış Açıları** ← Tercih edilen açıları öğrenmek
4. **Tepki Süresi** ← Oyuncunun dikkatin analiz etmek

### Zorluk Seviyeleri

| Seviye | Zorluk | Strateji | Hız | Açıklama |
|--------|--------|----------|-----|----------|
| **1** | 0.0-0.3 | Wander | 2-3 | Çok kolay, tahmin edilebilir |
| **2** | 0.3-0.6 | Evade | 3-5 | Orta, kaçma başlıyor |
| **3** | 0.6-0.85 | Fake Dodge | 5-7 | Zor, aldatıcı hareket |
| **4** | 0.85-1.0 | Sprint | 7-8 | Çok zor, maksimum zorluk |

### Strateji Sistemleri

**1. Wander (Dolaşma)**
```
Rastgele yöne hareket et
↓ Çok Basit, Tahmin Edilebilir
```

**2. Evade (Kaçma)**
```
Oyuncudan kaç + Yan hareketler
↓ Daha Zorlayıcı, Etkili
```

**3. Fake Dodge (Sahte Hareket)**
```
Beklenmeyen yöne git → Aniden dön → Evade
↓ Çok Zor, Oyuncuyu Aldatıcı
```

**4. Sprint (Hızlı Kaçış)**
```
Maksimum hızda oyuncudan kaç
↓ Maksimum Zorluk, İnsan Benzeri
```

---

## 🧠 Makine Öğrenmesi Bileşenleri

### 1. Açı Öğrenimi

Hedef, oyuncunun sık atış yaptığı açıları öğrenir:

```python
# Örnek Senaryo:
Oyuncu 45° açıdan 80% başarıyla atış yapıyor
    ↓
AI bu açıyı learned_angles[45] = 0.8 olarak kaydeder
    ↓
45° açıdan daha çok kaçmaya çalışır
```

### 2. Adaptif Hız Ayarlaması

```python
zorluk = 0.5 ise,
hız = 2.0 + (8.0 - 2.0) × 0.5 = 5.0
```

### 3. Strateji Seçimi

```python
Eğer zorluk < 0.3:
    Sadece Wander (%100)
    
Eğer 0.3 <= zorluk < 0.6:
    Wander %70, Evade %30
    
Eğer 0.6 <= zorluk < 0.85:
    Evade %40, Fake Dodge %35, Sprint %25
    
Eğer zorluk >= 0.85:
    Evade %30, Fake Dodge %40, Sprint %30
```

---

## 📊 Oyun İstatistikleri

Oyun süresi boyunca takip edilen metrikler:

```python
{
    'hit_percentage': 0.65,           # 65% İsabet Oranı
    'shot_frequency': 2.5,            # 2.5 atış/saniye
    'dominant_angles': (45, 90),      # 45°-90° aralığında atış
    'total_shots': 150,               # 150 toplam atış
    'avg_shot_interval': 24.0,        # Ortalama 24 frame arası
}
```

Bu veriler AI'nin uyum sağlamasını yönlendirir.

---

## 🎮 Oynanış Talimatları

### Kontroller:
```
← → ↑ ↓   : Oyuncuyu hareket ettir
MOUSE TIK  : Atış yap
SPACE      : Oyunu durdur/devam ettir
R          : Oyunu sıfırla
ESC        : Çıkış
```

### Oyun Amacı:
Hedefi mümkün olduğunca çok vur! Başarıldıkça zorluk seviyesi otomatik olarak artar.

**Başarı Seviyeleri:**
- 📍 %70+ İsabet → Çok Başarılı ⭐⭐⭐
- 📍 %50-70% İsabet → Başarılı ⭐⭐
- 📍 %30-50% İsabet → Normal ⭐
- 📍 <%30% İsabet → Zor Yer 😅

---

## 🧪 Test Sonuçları

AI Sistemi Başarıyla Test Edildi:

```
✓ Oyuncu İstatistikleri Sistemi
  - Atış açıları doğru hesaplanıyor
  - İsabet yüzdesi doğru izleniyor
  - Atış sıklığı doğru ölçülüyor
  
✓ Zorluk Seviyesi Algoritması
  - %80 başarı → zorluk artar ✓
  - %30 başarı → zorluk azalır ✓
  - Limitler doğru uygulanıyor ✓
  
✓ Açı Öğrenme Mekanizması
  - Başarılı açılar ağırlandırılıyor ✓
  - Decay (unutma) doğru çalışıyor ✓
```

---

## 🔧 Konfigürasyon

[src/config.py](src/config.py) dosyasında ayarlanabilir:

```python
# Zorluk Sistemi
DIFFICULTY_THRESHOLD = 0.6      # Zorluk artma eşiği
ADAPTATION_SPEED = 0.05         # Adaptasyon hızı
MIN_DIFFICULTY = 0.3            # Minimum zorluk
MAX_DIFFICULTY = 1.0            # Maksimum zorluk

# AI Öğrenme
AI_LEARNING_RATE = 0.1          # Açı öğrenme hızı

# Hedef Özellikleri
TARGET_MIN_SPEED = 2.0          # Minimum hız
TARGET_MAX_SPEED = 8.0          # Maksimum hız
```

**Zorluk seviyesini test etmek istiyorsanız:**
```python
MIN_DIFFICULTY = 0.8            # Başlangıçta zor
MAX_DIFFICULTY = 0.9            # Maksimum zorluk sınırı
ADAPTATION_SPEED = 0.1          # Daha hızlı adaptasyon
```

---

## 📈 Gelişme Süreci

Tipik oyun oturumu:

```
0-1 dakika:   AI basit dolaşıyor, hedef çok kolay
              Zorluk: 0.1 - 0.2
              
1-3 dakika:   Oyuncu başarılı olmaya başlıyor
              AI kaçmaya başlıyor
              Zorluk: 0.3 - 0.5
              
3-7 dakika:   Oyuncu ve AI arasında dengeli bir savaş
              AI sahte hareketler öğreniyor
              Zorluk: 0.6 - 0.8
              
7+ dakika:    AI oyuncunun davranışını tam öğrenmiş
              Maksimum zorluk seviyesine ulaştı
              Zorluk: 0.9 - 1.0 (Sabit)
```

---

## 🤖 Yapay Zeka Nasıl Çalışıyor?

### Her Frame'de (1/60 saniye):

1. **Oyuncu İstatistiklerini Analiz Et**
   ```
   Recent hit % = Son 30 atışta başarı oranı
   ```

2. **Zorluk Seviyesini Ayarla**
   ```
   Eğer recent_hit > 0.65:
       difficulty += 0.05 (maksimum 1.0)
   Eğer recent_hit < 0.35:
       difficulty -= 0.05 (minimum 0.3)
   ```

3. **Parametreleri Güncelle**
   ```
   hız = 2.0 + 6.0 × difficulty
   kaçınma_gücü = 0.1 + 0.6 × difficulty
   ```

4. **Strateji Seç**
   ```
   Zorluk seviyesine göre 4 stratejiden birini seç
   Daha yüksek zorluk = Daha karmaşık strateji
   ```

5. **Hareketi Uygula**
   ```
   Seçilen strateji tipine ait hareket komutunu çalıştır
   Hedef konumunu güncelle
   ```

### AI'nin Öğrendikleri:

- ✓ Oyuncunun atış açılarını
- ✓ Oyuncunun atış sıklığını
- ✓ Oyuncunun hızını
- ✓ Oyuncunun başarı oranını

### AI'nin Uyum Sağladığı:

- ✓ Hız (2.0 → 8.0)
- ✓ Kaçınma gücü (0.1 → 0.7)
- ✓ Strateji seçimi
- ✓ Yön değişim sıklığı

---

## 🐛 Sorun Giderme

### Pygame Kurulumu Sorunu

Eğer `ModuleNotFoundError: No module named 'pygame'` hatası alıyorsanız:

```bash
# Tekrar kurmayı dene
pip install pygame --upgrade

# Veya binary sürüm kur
pip install pygame --only-binary :all:
```

### Alternative: Terminal Sürümü

Pygame kurulumu başarısız olursa, terminal sürümünü kullanabilirsiniz:

```bash
python terminal_game.py
```

---

## 📚 Öğrenilen Konseptler

Bu proje aşağıdaki bilgisayar bilimleri konseptlerini uygular:

1. **Makine Öğrenmesi**
   - İstatistik tabanlı öğrenme
   - Patlama/çürüme mekanizmaları

2. **Adaptif Algoritmalar**
   - Dinamik parametre ayarlaması
   - Pozitif geri bildirim döngüleri

3. **Veri Analitikleri**
   - Zaman serisi analizi
   - Örüntü tanıma

4. **Oyun Tasarımı**
   - Dinamik zorluk sistemi
   - Strateji seçimi

5. **İnsan-Bilgisayar Etkileşimi**
   - Oyuncu davranışı tahmini
   - Eğlence seviyesi optimizasyonu

---

## 🎯 İleri Geliştirmeler

Projeyi genişletmek istiyorsanız:

1. **Sinir Ağları Ekle**
   ```python
   import tensorflow as tf
   # Derin öğrenme modeli eğit
   ```

2. **Multiplayer Modu**
   ```python
   # Ağ üzerinden P2P senkronizasyonu
   ```

3. **Daha Fazla Strateji**
   ```python
   strategies = ['wander', 'evade', 'fake_dodge', 'sprint',
                 'circle', 'zigzag', 'unpredictable']
   ```

4. **Görsel İyileştirmeler**
   ```python
   # Parçacık efektleri
   # Sahne geçişleri
   # Müzik ve ses
   ```

---

## 📞 Destek

Herhangi bir sorun olursa:
- AI test dosyasını çalıştırarak sistem temellerini kontrol et
- Konfigürasyon değerlerini kontrol et
- Terminal sürümünü dene

---

## 📄 Lisans

Bu proje eğitim amaçlıdır. Özgürce değiştirebilir ve kişisel projelerinizde kullanabilirsiniz.

---

**Eğlenceli oyun oynaman dileriz! 🎮✨**

---

## Hızlı Referans

```bash
# Test et
python test_ai.py

# Oyunu başlat
python main.py

# Terminal sürümü (Pygame yok)
python terminal_game.py

# Bağımlılıkları yükle
pip install -r requirements.txt
```

Daha fazla bilgi için [README.md](README.md) ve [TECHNICAL.md](TECHNICAL.md) dosyalarına bakabilirsin.
