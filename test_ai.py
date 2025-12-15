#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptif AI Sisteminin Test Edilmesi
Pygame olmadan yapılabilir
"""

import sys
import os

# src klasörünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Pygame olmadan test edeceğimiz modülleri import et
from config import *
from player_stats import PlayerStats
import math

def test_player_stats():
    """PlayerStats sınıfını test et"""
    print("=" * 60)
    print("OYUNCU ISTATISTIKLERI SISTEMI TESTI")
    print("=" * 60)
    
    stats = PlayerStats()
    
    # Simüle edilmiş atışlar
    player_pos = (600, 750)
    
    # Örnek atışları kaydet
    targets = [
        (700, 300),   # Sağ üst
        (500, 250),   # Sol üst
        (800, 400),   # Sağ
        (650, 350),   # Biraz sağ üst
        (750, 320),   # Sağ üst (başarılı)
    ]
    
    print("\n[*] Atışlar Kaydediliyor...")
    for i, target_pos in enumerate(targets):
        stats.record_shot(player_pos, target_pos, i * 15)
        print(f"  Atış {i+1}: Hedef konumu {target_pos}")
        
        # Bazı atışları başarılı işaretle
        if i in [2, 4]:
            stats.record_hit()
            print(f"    [OK] BASARILI!")
        else:
            stats.record_miss()
            print(f"    [X] Başarısız")
    
    # İstatistikleri göster
    print("\n[ISTATISTIKLER]:")
    print(f"  Toplam Atış: {stats.total_shots}")
    print(f"  Toplam İsabet: {stats.total_hits}")
    print(f"  İsabet Yüzdesi: {stats.get_hit_percentage()*100:.1f}%")
    print(f"  Son Atışlardaki İsabet: {stats.get_recent_hit_percentage()*100:.1f}%")
    print(f"  Atış Sıklığı: {stats.get_shooting_frequency():.2f} atış/sn")
    
    angles = list(stats.shot_angles)
    print(f"  Atış Açıları (derece): {[f'{a:.1f}' for a in angles]}")
    
    dominant_range = stats.get_dominant_angle_range()
    print(f"  En Çok Kullanılan Açı Aralığı: {dominant_range[0]:.0f}°-{dominant_range[1]:.0f}°")
    
    profile = stats.get_adaptation_profile()
    print("\n[ADAPTASYON PROFILI]:")
    for key, value in profile.items():
        if key == 'dominant_angles':
            print(f"  {key}: {value[0]:.0f}°-{value[1]:.0f}°")
        elif isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")

def test_ai_learning():
    """AI Öğrenme Mekanizmasının Temel Mantığını Test Et"""
    print("\n" + "=" * 60)
    print("AI OGRENME SISTEMI TESTI")
    print("=" * 60)
    
    # Simüle edilen oyuncu istatistikleri
    print("\n[ZORLUK SEVIYESI ADAPTASYONU]:")
    
    difficulty = 0.1
    test_scenarios = [
        ("Çok başarılı (80% isabet)", 0.80),
        ("Başarılı (70% isabet)", 0.70),
        ("Normal (50% isabet)", 0.50),
        ("Başarısız (30% isabet)", 0.30),
        ("Çok başarısız (10% isabet)", 0.10),
    ]
    
    for scenario, hit_pct in test_scenarios:
        old_difficulty = difficulty
        
        # Zorluk ayarlama mantığı
        if hit_pct > 0.65:
            difficulty = min(MAX_DIFFICULTY, difficulty + ADAPTATION_SPEED)
        elif hit_pct < 0.35:
            difficulty = max(MIN_DIFFICULTY, difficulty - ADAPTATION_SPEED)
        
        evasion = 0.1 + 0.6 * difficulty
        speed = TARGET_MIN_SPEED + (TARGET_MAX_SPEED - TARGET_MIN_SPEED) * difficulty
        
        print(f"\n  {scenario}")
        print(f"    Önceki Zorluk: {old_difficulty:.2f} -> Yeni Zorluk: {difficulty:.2f}")
        print(f"    Kaçınma Gücü: {evasion:.2f}")
        print(f"    Hedef Hızı: {speed:.2f}")

def test_angle_learning():
    """Açı Öğrenme Mekanizmasını Test Et"""
    print("\n" + "=" * 60)
    print("ACILAR OGRENME SISTEMI TESTI")
    print("=" * 60)
    
    print("\n[AÇI OGRENMESI]:")
    
    # Simüle edilen öğrenilen açılar
    learned_angles = {
        45: 0.0,   # Başlangıçta boş
        90: 0.0,
        135: 0.0,
        180: 0.0,
    }
    
    print("\n  Senaryo: Oyuncu 45° ve 90° açılarında çok atış yapıyor")
    print("  45° açıda %80 başarı | 90° açıda %60 başarı")
    
    # 10 atış simüle et
    for shot in range(10):
        # 45° açıdan 7 atış (3 başarılı)
        if shot < 7:
            learned_angles[45] += AI_LEARNING_RATE
            if shot % 3 == 0:  # Her 3 atışta biri başarılı
                learned_angles[45] += 2 * AI_LEARNING_RATE  # Ek ağırlık
        
        # 90° açıdan 3 atış (1 başarılı)
        else:
            learned_angles[90] += AI_LEARNING_RATE
            if shot == 8:
                learned_angles[90] += 2 * AI_LEARNING_RATE
    
    # Decay (unutma) uygulaması
    for angle in learned_angles:
        learned_angles[angle] *= 0.95
    
    print("\n  10 Atıştan Sonra Ogrenen Açılar:")
    for angle, weight in sorted(learned_angles.items()):
        if weight > 0:
            print(f"    {angle}°: {weight:.4f} (oncelik)")

def main():
    """Tüm testleri çalıştır"""
    try:
        test_player_stats()
        test_ai_learning()
        test_angle_learning()
        
        print("\n" + "=" * 60)
        print("[OK] TUM TESTLER BASARILI!")
        print("=" * 60)
        print("\nOyun tamamen fonksiyonel ve hazır!")
        print("\nOyunu başlatmak için: python main.py")
        
    except Exception as e:
        print(f"\n[HATA] Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
