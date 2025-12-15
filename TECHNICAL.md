# Adaptif AI Nişan Alma Oyunu - Teknik Dokümantasyon

## 📋 Sistem Mimarisi

Oyun dört ana bileşenden oluşur:

### 1. Oyuncu İstatistikleri Sistemi (`player_stats.py`)

```python
class PlayerStats:
    - shot_angles: Atılan açılar (dereceler)
    - shot_hits: Vurma/ısbetsiz durumları
    - shot_intervals: Atışlar arasındaki zaman
    - learned_angles_to_avoid: AI öğrenilen açılar
    
    Metotlar:
    - record_shot(): Atışı kaydet
    - record_hit()/record_miss(): Sonucu kaydet
    - get_hit_percentage(): İsabet yüzdesini hesapla
    - get_dominant_angle_range(): En sık atılan açı aralığını bul
    - get_shooting_frequency(): Atış sıklığını hesapla (atış/sn)
    - get_adaptation_profile(): AI adaptasyonu için veri paketi
```

**Veri Depolama:**
- `deque(maxlen=30)` kullanarak son 30 atışı takip eder
- Eski veriler otomatik olarak silinir
- Hafif bellek kullanımı

---

### 2. Adaptif AI Hedef Sistemi (`ai_target.py`)

```python
class AdaptiveAITarget:
    # Konum ve Hareket
    - x, y: Hedef konumu
    - velocity_x, velocity_y: Hareket vektörü
    - speed: Mevcut hız (2-8 arası)
    
    # AI Parametreleri
    - difficulty: Zorluk seviyesi (0.0-1.0)
    - evasion_strength: Kaçınma gücü
    - strategy_randomness: Stratejin rastgeleliği
    - learned_angles_to_avoid: Öğrenilen tehlikeli açılar
    
    # Strateji Yönetimi
    - strategy_state: 'wander', 'evade', 'fake_dodge', 'sprint'
    - strategy_timer: Mevcut strateji ne kadar süre devam edecek
```

**AI Döngüsü:**
```
1. Oyuncu istatistiklerini analiz et
   └─ İsabet yüzdesine göre zorluk ayarla
   
2. Öğrenilen açıları güncelle
   └─ Başarılı atışları daha ağır say (3x)
   └─ Eski değerleri decay et (95% kalıcılık)
   
3. Strateji seç
   └─ Zorluk seviyesine göre strateji seçimini ağırlandır
   
4. Hareketi uygula
   └─ Seçilen stratejiye ait hareket komutunu çalıştır
   └─ Hızı ve yönü parametrelere göre ayarla
   
5. Sınır kontrolü
   └─ Hedefi ekran içinde tut
```

---

## 🚀 Geliştirme İçin Fikirler

1. **Sinir Ağları (Neural Network):** 
   - Basit ML yerine derin öğrenme
   - OpenAI Gym ortamı

2. **Çok Aşamalı Strateji:**
   - Daha fazla strateji türü
   - Stratejiler arası geçişler

3. **Oyuncu Profili:**
   - Agresif vs Pasif oyuncuları tanı
   - Profil-spesifik adaptasyon

4. **İstatistik Analizi:**
   - Oyuncu davranışı trendleri
   - Predictive AI adaptasyonu

5. **Ağ Destekli Multiplayer:**
   - P2P senkronizasyonu
   - Global zorluk sıralaması
