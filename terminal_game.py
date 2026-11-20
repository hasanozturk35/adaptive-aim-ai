#!/usr/bin/env python3
"""
Terminal Tabanlı Adaptif AI Nişan Alma Oyunu (Pygame gerektirmez)
Basit konsol versiyonu
"""

import sys
import os
import random
import math
import time
import threading

# emojiler, çıktı dosyaya/boruya yönlendirildiğinde Windows kod sayfasında (cp1254) çökmesin
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# src klasörünü path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import *
from player_stats import PlayerStats

class SimpleTerminalGame:
    """Basit terminal tabanlı oyun"""
    
    def __init__(self):
        self.target_x = 50
        self.target_y = 10
        self.player_x = 50
        self.player_y = 20
        
        self.difficulty = 0.1
        self.player_stats = PlayerStats()
        self.frame = 0
        self.running = True
        
        # AI durumu
        self.target_vx = 0
        self.target_vy = 0
        self.speed = TARGET_MIN_SPEED
        
    def move_target(self):
        """Hedefi AI kontrolüne göre hareket ettir"""
        recent_hit = self.player_stats.get_recent_hit_percentage()
        
        # Zorluk seviyesini ayarla
        if recent_hit > 0.65:
            self.difficulty = min(MAX_DIFFICULTY, self.difficulty + ADAPTATION_SPEED)
        elif recent_hit < 0.35:
            self.difficulty = max(MIN_DIFFICULTY, self.difficulty - ADAPTATION_SPEED)
        
        # Parametreleri güncelle
        self.speed = TARGET_MIN_SPEED + (TARGET_MAX_SPEED - TARGET_MIN_SPEED) * self.difficulty
        
        # Basit AI: oyuncudan kaç veya rastgele hareket et
        if self.difficulty < 0.3:
            # Düşük zorluk - rastgele
            self.target_vx = random.uniform(-1, 1)
            self.target_vy = random.uniform(-1, 1)
        else:
            # Yüksek zorluk - oyuncudan kaç
            dx = self.target_x - self.player_x
            dy = self.target_y - self.player_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > 0:
                self.target_vx = (dx / dist) * (1 - self.difficulty/2)
                self.target_vy = (dy / dist) * (1 - self.difficulty/2)
            else:
                self.target_vx = random.uniform(-1, 1)
                self.target_vy = random.uniform(-1, 1)
        
        # Hız uygula
        self.target_x += self.target_vx * self.speed / 5
        self.target_y += self.target_vy * self.speed / 5
        
        # Sınırları kontrol et
        self.target_x = max(1, min(99, self.target_x))
        self.target_y = max(1, min(22, self.target_y))
    
    def display(self):
        """Oyunu konsola çiz"""
        # Ekranı temizle
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Başlık
        print("=" * 100)
        print("🎮 ADAPTIF AI NIŞAN ALMA OYUNU (Terminal Sürümü)")
        print("=" * 100)
        
        # Oyun alanı (grid)
        grid = [['.' for _ in range(100)] for _ in range(24)]
        
        # Oyuncuyu ekle
        px = int(self.player_x) % 100
        py = int(self.player_y) % 24
        if 0 <= px < 100 and 0 <= py < 24:
            grid[py][px] = 'P'
        
        # Hedefi ekle
        tx = int(self.target_x) % 100
        ty = int(self.target_y) % 24
        if 0 <= tx < 100 and 0 <= ty < 24:
            grid[ty][tx] = 'T'
        
        # Grid'i yazdır
        for row in grid:
            print(''.join(row))
        
        # İstatistikler
        print("\n" + "-" * 100)
        print(f"Frame: {self.frame} | Zorluk: {self.difficulty:.2f} | Hız: {self.speed:.1f}")
        print(f"Oyuncu: ({self.player_x:.1f}, {self.player_y:.1f}) | Hedef: ({self.target_x:.1f}, {self.target_y:.1f})")
        
        hit_pct = self.player_stats.get_recent_hit_percentage() * 100
        print(f"İsabet: {hit_pct:.1f}% ({self.player_stats.total_hits}/{self.player_stats.total_shots})")
        print(f"Atış Sıklığı: {self.player_stats.get_shooting_frequency():.2f} atış/sn")
        
        print("\nKontroller:")
        print("  W/A/S/D: Hareket | SPACE: Atış | Q: Çıkış | R: Yenile")
        print("-" * 100)
    
    def simulate_shot(self):
        """Atış simülasyonu"""
        self.player_stats.record_shot(
            (self.player_x, self.player_y),
            (self.target_x, self.target_y),
            self.frame
        )
        
        # Vurma kontrolü (basit mesafe hesabı)
        dx = self.target_x - self.player_x
        dy = self.target_y - self.player_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 5:  # 5 birim içinde ise vur
            self.player_stats.record_hit()
            self.target_x = random.uniform(10, 90)
            self.target_y = random.uniform(2, 22)
            print("\n✓ VURULDU!")
        else:
            self.player_stats.record_miss()
            print("\n✗ Isabetsiz")
        
        time.sleep(0.5)
    
    def run(self):
        """Oyun döngüsü (basit versiyon)"""
        print("\n⚠️  TERMINAL SÜRÜMÜ BAŞLATILDI!")
        print("Pygame otomatik olarak yüklenirken bunu kullanabilirsiniz.")
        print("\nHer 30 frame'de hedef otomatik hareket eder.")
        print("SPACE tuşuna basarak atış yapabilirsiniz.\n")
        
        try:
            while self.running and self.frame < 300:
                self.display()
                
                # Her 30 frame'de hedefi hareket ettir
                if self.frame % 5 == 0:
                    self.move_target()
                
                self.frame += 1
                
                # Basit girdi kontrol (oyuncu 'a'ya basmışsa atış)
                user_input = input("Komut (space=atış, q=çık, r=yenile): ").lower()
                
                if user_input == 'q':
                    self.running = False
                elif user_input == ' ':
                    self.simulate_shot()
                elif user_input == 'r':
                    self.__init__()
                
                time.sleep(0.1)
        
        except (KeyboardInterrupt, EOFError):
            pass
        
        print("\n" + "=" * 100)
        print("Oyun sona erdi!")
        print(f"Son İsabet Yüzdesi: {self.player_stats.get_hit_percentage()*100:.1f}%")
        print("=" * 100)

def main():
    game = SimpleTerminalGame()
    game.run()

if __name__ == "__main__":
    main()
