"""
Adaptif AI Hedef Sistemi
Oyuncunun performansına göre davranış şekli değişen hedef
"""

import math
import random
import numpy as np
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_SIZE, TARGET_MIN_SPEED,
    TARGET_MAX_SPEED, AI_LEARNING_RATE, ADAPTATION_SPEED,
    MIN_DIFFICULTY, MAX_DIFFICULTY
)


class AdaptiveAITarget:
    """
    Oyuncunun davranışını öğrenen ve uyum sağlayan hedef
    
    Öğrenme mekanizması:
    - Oyuncunun atış açılarını takip eder
    - Oyuncunun atış sıklığını öğrenir
    - İsabet oranına göre kaçınma davranışını ayarlar
    - Zamanla daha karmaşık stratejiler geliştirir
    """
    
    def __init__(self, x, y):
        # Konum
        self.x = x
        self.y = y
        self.size = TARGET_SIZE
        
        # Hareket
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = TARGET_MIN_SPEED
        
        # Zorluk seviyesi (0-1 arası)
        # 0 = çok kolay, 1 = çok zor
        self.difficulty = 0.1
        
        # AI davranış parametreleri
        self.evasion_strength = 0.1     # Kaçınma gücü
        self.strategy_randomness = 0.5  # Strateji rastgeleliği
        self.direction_change_frequency = 0.05
        
        # Öğrenilen stratejiler
        self.learned_angles_to_avoid = {}  # Açı -> kaçış derecesi
        self.strategy_state = "wander"      # wander, evade, fake_dodge, sprint
        self.strategy_timer = 0
        self.strategy_cooldown = 0
        
        # Ani yön değişimi
        self.fake_dodge_timer = 0
        self.fake_dodge_active = False
        
        # Sprint modu
        self.sprint_timer = 0
        self.is_sprinting = False
        
        # İstatistik takibi
        self.frames_since_last_adaptation = 0
        self.dodge_success_count = 0
        
    def update(self, player_pos, player_stats, frame):
        """Hedefi güncelle ve AI kararlarını al"""
        
        # Zorluk seviyesini oyuncu performansına göre ayarla
        self._adapt_difficulty(player_stats)
        
        # Davranış stratejisini belirle
        self._update_strategy(player_pos)
        
        # Hareket komutunu çalıştır
        self._execute_movement(player_pos)

        # Konumu güncelle
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Ekran kenarlarından wrap (diğer tarafa geçiş)
        self._constrain_to_screen()
        
        # Zamanıcıları azalt
        self.strategy_timer -= 1
        self.strategy_cooldown -= 1
        self.fake_dodge_timer -= 1
        self.sprint_timer -= 1
        self.frames_since_last_adaptation += 1
    
    def _adapt_difficulty(self, player_stats):
        """Oyuncu performansına göre zorluk seviyesini ayarla"""
        
        # Son atışlardaki başarı oranına bak
        recent_hit_pct = player_stats.get_recent_hit_percentage()
        
        # Zorluk dinamik olarak ayarla
        if recent_hit_pct > 0.65:
            # Oyuncu çok başarılı, zorlaştır
            self.difficulty = min(MAX_DIFFICULTY, 
                                 self.difficulty + ADAPTATION_SPEED)
        elif recent_hit_pct < 0.35:
            # Oyuncu çok başarısız, kolaylaştır
            self.difficulty = max(MIN_DIFFICULTY,
                                 self.difficulty - ADAPTATION_SPEED)
        
        # Zorluk seviyesine göre parametreleri ayarla
        self._update_difficulty_parameters()
        
        # Öğrenilen açılardan kaçmayı öğren
        self._learn_from_player_angles(player_stats)
    
    def _update_difficulty_parameters(self):
        """Zorluk seviyesine göre davranış parametrelerini güncelle"""
        
        # Hız
        self.speed = TARGET_MIN_SPEED + (TARGET_MAX_SPEED - TARGET_MIN_SPEED) * self.difficulty
        
        # Kaçınma gücü
        self.evasion_strength = 0.1 + 0.6 * self.difficulty
        
        # Strateji rastgeleliği (başlangıçta yüksek, zorlaştıkça düşük)
        self.strategy_randomness = 0.7 - 0.5 * self.difficulty
        
        # Yön değişimi sıklığı
        self.direction_change_frequency = 0.02 + 0.15 * self.difficulty
    
    def _learn_from_player_angles(self, player_stats):
        """Oyuncunun atış açılarını öğren ve onlardan kaçmayı ögret"""
        
        if len(player_stats.shot_angles) == 0:
            return
        
        # Son atışların açılarını al
        recent_angles = list(player_stats.shot_angles)[-10:]
        
        # Başarılı atışların açılarını daha ağır say
        successful_shots = []
        for i, angle in enumerate(recent_angles):
            if i < len(player_stats.shot_hits) and player_stats.shot_hits[i]:
                # Başarılı atış
                for _ in range(3):  # 3 kat daha ağır
                    successful_shots.append(angle)
            else:
                successful_shots.append(angle)
        
        # Öğrenilen açıları güncelle
        for angle in successful_shots:
            normalized_angle = int(angle % 360)
            if normalized_angle not in self.learned_angles_to_avoid:
                self.learned_angles_to_avoid[normalized_angle] = 0
            self.learned_angles_to_avoid[normalized_angle] += AI_LEARNING_RATE
        
        # Eski açıları unutmak için azalt
        for angle in self.learned_angles_to_avoid:
            self.learned_angles_to_avoid[angle] *= 0.95
    
    def _update_strategy(self, player_pos):
        """Hangi stratejiyi kullanacağını belirle"""
        
        if self.strategy_cooldown > 0:
            return
        
        # Zorluk seviyesine göre strateji seçme olasılığı
        if random.random() < self.direction_change_frequency:
            strategy_choice = random.random()
            
            if self.difficulty < 0.3:
                # Düşük zorluk: sadece dolaş
                self.strategy_state = "wander"
            
            elif self.difficulty < 0.6:
                # Orta zorluk: kaçın veya dolaş
                if strategy_choice < 0.7:
                    self.strategy_state = "wander"
                else:
                    self.strategy_state = "evade"
                    self.strategy_timer = random.randint(30, 60)
            
            else:
                # Yüksek zorluk: karmaşık stratejiler
                if strategy_choice < 0.4:
                    self.strategy_state = "evade"
                    self.strategy_timer = random.randint(40, 80)
                elif strategy_choice < 0.7:
                    self.strategy_state = "fake_dodge"
                    self.strategy_timer = random.randint(20, 40)
                else:
                    self.strategy_state = "sprint"
                    self.strategy_timer = random.randint(30, 60)
            
            self.strategy_cooldown = self.strategy_timer + 20
    
    def _execute_movement(self, player_pos):
        """Seçilen stratejiyi çalıştır"""
        
        vx, vy = 0, 0
        
        if self.strategy_state == "wander":
            # Basit rastgele dolaşma
            vx, vy = self._wander_movement()
        
        elif self.strategy_state == "evade":
            # Oyuncudan kaç
            vx, vy = self._evade_movement(player_pos)
        
        elif self.strategy_state == "fake_dodge":
            # Sahte hareket yap
            vx, vy = self._fake_dodge_movement(player_pos)
        
        elif self.strategy_state == "sprint":
            # Hızla kaç
            vx, vy = self._sprint_movement(player_pos)
        
        # Hızı normalized birim vektör haline getir ve hızla çarp
        if vx != 0 or vy != 0:
            length = math.sqrt(vx**2 + vy**2)
            if length > 0:
                vx = (vx / length) * self.speed
                vy = (vy / length) * self.speed
        
        self.velocity_x = vx
        self.velocity_y = vy
    
    def _wander_movement(self):
        """Basit dolaşma hareketi"""
        # Rastgele yöne git
        angle = random.uniform(0, 2 * math.pi)
        return (math.cos(angle), math.sin(angle))
    
    def _evade_movement(self, player_pos):
        """Oyuncudan kaçma hareketi"""
        
        # Oyuncudan olan yönü hesapla
        dx = self.x - player_pos[0]
        dy = self.y - player_pos[1]
        
        # Eğer çok yakınsa daha hızlı kaç
        dist = math.sqrt(dx**2 + dy**2)
        if dist < 200:
            self.evasion_strength = min(1.0, self.evasion_strength + 0.05)
        
        # Öğrenilen açılardan daha çok kaç
        if dist > 0:
            # Evasion vektörü
            ex = (dx / dist) * self.evasion_strength
            ey = (dy / dist) * self.evasion_strength
            
            # Rastgele yan hareket ekle
            side_angle = random.uniform(-math.pi/2, math.pi/2)
            sx = math.cos(side_angle) * (1 - self.evasion_strength)
            sy = math.sin(side_angle) * (1 - self.evasion_strength)
            
            return (ex + sx, ey + sy)
        
        return self._wander_movement()
    
    def _fake_dodge_movement(self, player_pos):
        """Sahte hareket (oyuncuyu aldatma)"""
        
        if not self.fake_dodge_active:
            # Başka yöne git
            self.fake_dodge_active = True
            self.fake_dodge_timer = random.randint(10, 20)
            
            # Oyuncunun beklediği yerin tersi
            dx = self.x - player_pos[0]
            dy = self.y - player_pos[1]
            
            # Yan yöne hızlı hareket
            angle = random.uniform(-math.pi, math.pi)
            return (math.cos(angle), math.sin(angle))
        
        elif self.fake_dodge_timer <= 0:
            # Yönü aniden değiştir
            self.fake_dodge_active = False
            return self._evade_movement(player_pos)
        
        else:
            # Devam et
            return (self.velocity_x, self.velocity_y) if (self.velocity_x or self.velocity_y) else (1, 0)
    
    def _sprint_movement(self, player_pos):
        """Hızlı kaçış hareketi"""
        
        # Oyuncudan olan yönü hesapla
        dx = self.x - player_pos[0]
        dy = self.y - player_pos[1]
        
        # Normaliz et
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            return (dx / dist, dy / dist)
        
        return self._wander_movement()
    
    def _constrain_to_screen(self):
        """Ekran kenarlarında wrap: hedef diğer tarafa geçsin (sıkışma olmasın)."""

        # Allow target to move slightly beyond its size before wrapping so behavior feels natural
        margin = self.size

        if self.x < -margin:
            self.x = SCREEN_WIDTH + margin
        elif self.x > SCREEN_WIDTH + margin:
            self.x = -margin

        if self.y < -margin:
            self.y = SCREEN_HEIGHT + margin
        elif self.y > SCREEN_HEIGHT + margin:
            self.y = -margin
    
    def get_difficulty_info(self):
        """Zorluk bilgisini döndür"""
        return {
            'level': self.difficulty,
            'strategy': self.strategy_state,
            'speed': self.speed,
            'evasion_strength': self.evasion_strength,
        }
