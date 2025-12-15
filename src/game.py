"""
Ana Oyun Dosyası
Arcade tarzı adaptif AI'lı nişan alma oyunu
"""

import pygame # type: ignore
import math
import sys
from config import *
from player_stats import PlayerStats
from ai_target import AdaptiveAITarget


class TargetingGame:
    """Ana oyun sınıfı"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Adaptif AI Nişan Alma Oyunu")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Oyun durumu
        self.running = True
        self.game_paused = False
        self.frame = 0
        
        # Oyuncu
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 50
        
        # Hedef
        self.target = AdaptiveAITarget(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 3
        )
        
        # Oyuncu istatistikleri
        self.player_stats = PlayerStats()
        
        # Atış efektleri
        self.projectiles = []
        self.explosions = []
        
        # Görsel feeback
        self.hit_flash = 0
        self.miss_flash = 0
    
    def handle_events(self):
        """Olayları işle"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.game_paused = not self.game_paused
                elif event.key == pygame.K_r:
                    self.reset_game()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Atış yap — fare tıklanan yere doğrudan ateş et (kilit yok)
                if not self.game_paused:
                    # event.pos is (x, y)
                    self.player_shoot(event.pos)
    
    def player_shoot(self, aim_pos=None):
        """Oyuncu ateş et. Eğer `aim_pos` verilmişse fareye doğru ateş et; aksi halde hedefe kilitlenir."""

        # Hedef pozisyonu (fare tıklaması veya mevcut hedef)
        if aim_pos is not None:
            aim_x, aim_y = aim_pos
        else:
            aim_x, aim_y = self.target.x, self.target.y

        # Atışı kaydet (hedef olarak tıklanan pozisyonu kaydet)
        self.player_stats.record_shot(
            (self.player_x, self.player_y),
            (aim_x, aim_y),
            self.frame
        )

        # Tıklanan konuma yönlendirilmiş bir ışın oluştur
        dx = aim_x - self.player_x
        dy = aim_y - self.player_y
        dist = math.hypot(dx, dy)

        if dist > 0:
            # Hızı normalize et
            speed = 15
            vx = (dx / dist) * speed
            vy = (dy / dist) * speed

            # Atışı ekle
            self.projectiles.append({
                'x': self.player_x,
                'y': self.player_y,
                'vx': vx,
                'vy': vy,
                'life': 200  # Kaç frame sürer
            })
    
    def update(self):
        """Oyunu güncelle"""
        if self.game_paused:
            return
        
        self.frame += 1
        
        # Hedefi güncelle
        self.target.update(
            (self.player_x, self.player_y),
            self.player_stats,
            self.frame
        )
        
        # Atışları güncelle
        self._update_projectiles()
        
        # Ekran kontrolü
        self._update_screen_controls()
        
        # Flash efektlerini azalt
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.miss_flash > 0:
            self.miss_flash -= 1
    
    def _update_projectiles(self):
        """Atışları ve çarpışmaları güncelle"""
        
        to_remove = []
        
        for i, proj in enumerate(self.projectiles):
            # Konumu güncelle
            proj['x'] += proj['vx']
            proj['y'] += proj['vy']
            proj['life'] -= 1
            
            # Ömrü bittiyse sil
            if proj['life'] <= 0:
                to_remove.append(i)
                continue
            
            # Hedefle çarpışma kontrolü
            dx = proj['x'] - self.target.x
            dy = proj['y'] - self.target.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < TARGET_SIZE + 5:
                # Vuruldu!
                self.player_stats.record_hit()
                self.hit_flash = 10
                
                # Patlama efekti
                self._create_explosion(proj['x'], proj['y'])
                
                # Hedef konumunu rastgele değiştir
                self.target.x = SCREEN_WIDTH * 0.2 + (SCREEN_WIDTH * 0.6 * (self.frame % 1000) / 1000)
                self.target.y = SCREEN_HEIGHT * 0.2 + (SCREEN_HEIGHT * 0.4 * ((self.frame + 500) % 1000) / 1000)
                
                to_remove.append(i)
            
            # Ekran dışına çıktıysa sil
            elif (proj['x'] < 0 or proj['x'] > SCREEN_WIDTH or
                  proj['y'] < 0 or proj['y'] > SCREEN_HEIGHT):
                self.player_stats.record_miss()
                self.miss_flash = 5
                to_remove.append(i)
        
        # Ölenleri sil
        for i in reversed(to_remove):
            if i < len(self.projectiles):
                self.projectiles.pop(i)
    
    def _create_explosion(self, x, y):
        """Patlama efekti oluştur"""
        for _ in range(8):
            angle = ((_ / 8) * 2 * math.pi)
            self.explosions.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * 3,
                'vy': math.sin(angle) * 3,
                'life': 15
            })
    
    def _update_screen_controls(self):
        """Oyuncu kontrollerini işle"""
        keys = pygame.key.get_pressed()
        # Serbest hareket: kenarlarda wrap (diğer tarafa geçiş)
        if keys[pygame.K_LEFT]:
            self.player_x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.player_x += PLAYER_SPEED
        if keys[pygame.K_UP]:
            self.player_y -= PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.player_y += PLAYER_SPEED

        # Wrap X
        if self.player_x < -PLAYER_SIZE:
            self.player_x = SCREEN_WIDTH + PLAYER_SIZE
        elif self.player_x > SCREEN_WIDTH + PLAYER_SIZE:
            self.player_x = -PLAYER_SIZE

        # Wrap Y
        if self.player_y < -PLAYER_SIZE:
            self.player_y = SCREEN_HEIGHT + PLAYER_SIZE
        elif self.player_y > SCREEN_HEIGHT + PLAYER_SIZE:
            self.player_y = -PLAYER_SIZE
    
    def render(self):
        """Oyunu çiz"""
        self.screen.fill(BLACK)
        
        # Arka plan ızgarası çiz
        self._draw_grid()
        
        # Oyuncuyu çiz
        self._draw_player()
        
        # Hedefi çiz
        self._draw_target()
        
        # Atışları çiz
        self._draw_projectiles()
        
        # Patlama efektlerini çiz
        self._draw_explosions()
        
        # UI'ı çiz
        self._draw_ui()
        
        pygame.display.flip()
    
    def _draw_grid(self):
        """Arka plan ızgarası çiz"""
        grid_size = 50
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y), 1)
    
    def _draw_player(self):
        """Oyuncuyu çiz"""
        pygame.draw.circle(self.screen, PLAYER_COLOR, 
                          (int(self.player_x), int(self.player_y)), PLAYER_SIZE)
        
        # Oyuncu etrafında hedefi işaret eden çizgi
        dx = self.target.x - self.player_x
        dy = self.target.y - self.player_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            end_x = self.player_x + (dx / dist) * 150
            end_y = self.player_y + (dy / dist) * 150
            pygame.draw.line(self.screen, GREEN, 
                           (self.player_x, self.player_y),
                           (end_x, end_y), 1)
    
    def _draw_target(self):
        """Hedefi çiz"""
        color = TARGET_COLOR
        
        # Vurulmuş efekti
        if self.hit_flash > 0:
            color = YELLOW
        
        pygame.draw.circle(self.screen, color,
                          (int(self.target.x), int(self.target.y)), 
                          TARGET_SIZE)
        
        # Hedef etrafında halkalar (strateji göstergesi)
        if self.target.strategy_state != "wander":
            ring_color = (100, 100, 255) if self.target.strategy_state == "evade" else \
                        (200, 100, 255) if self.target.strategy_state == "fake_dodge" else \
                        (255, 100, 50)
            pygame.draw.circle(self.screen, ring_color,
                              (int(self.target.x), int(self.target.y)), 
                              TARGET_SIZE + 10, 2)
    
    def _draw_projectiles(self):
        """Atışları çiz"""
        for proj in self.projectiles:
            pygame.draw.circle(self.screen, YELLOW,
                              (int(proj['x']), int(proj['y'])), 3)
    
    def _draw_explosions(self):
        """Patlama efektlerini çiz"""
        to_remove = []
        
        for i, exp in enumerate(self.explosions):
            exp['x'] += exp['vx']
            exp['y'] += exp['vy']
            exp['life'] -= 1
            
            if exp['life'] <= 0:
                to_remove.append(i)
                continue
            
            size = max(1, 5 - (exp['life'] // 3))
            pygame.draw.circle(self.screen, YELLOW,
                              (int(exp['x']), int(exp['y'])), size)
        
        for i in reversed(to_remove):
            if i < len(self.explosions):
                self.explosions.pop(i)
    
    def _draw_ui(self):
        """UI bilgilerini çiz"""
        # İstatistikler
        hit_pct = self.player_stats.get_recent_hit_percentage() * 100
        total_shots = self.player_stats.total_shots
        
        # Zorluk bilgisi
        difficulty = self.target.difficulty
        
        # Metinleri oluştur
        stats_text = [
            f"Isabet: {hit_pct:.1f}% ({self.player_stats.total_hits}/{total_shots})",
            f"Zorluk: {difficulty:.2f}",
            f"Strateji: {self.target.strategy_state.upper()}",
            f"Hız: {self.target.speed:.1f}",
        ]
        
        # Sağ üst köşede çiz
        y_offset = 10
        for text in stats_text:
            surface = self.small_font.render(text, True, WHITE)
            self.screen.blit(surface, (10, y_offset))
            y_offset += 30
        
        # Oyuncu profili
        profile = self.player_stats.get_adaptation_profile()
        profile_text = [
            f"Atış Sıklığı: {profile['shot_frequency']:.2f} atış/sn",
            f"Hareketli Açılar: {profile['dominant_angles'][0]:.0f}-{profile['dominant_angles'][1]:.0f}°",
        ]
        
        y_offset = 10
        for text in profile_text:
            surface = self.small_font.render(text, True, GRAY)
            self.screen.blit(surface, (SCREEN_WIDTH - 400, y_offset))
            y_offset += 30
        
        # Kontrol talimatları
        controls = [
            "OK: Atış Et | Yönler: Hareket | SPACE: Durdur | ESC: Çık | R: Yenile"
        ]
        
        for i, text in enumerate(controls):
            surface = self.small_font.render(text, True, GRAY)
            self.screen.blit(surface, (10, SCREEN_HEIGHT - 35 + (i * 30)))
        
        # Duraklatıldı mesajı
        if self.game_paused:
            pause_text = self.font.render("DURAKLATILDI", True, YELLOW)
            text_rect = pause_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            )
            pygame.draw.rect(self.screen, BLACK, text_rect.inflate(20, 20))
            self.screen.blit(pause_text, text_rect)
    
    def reset_game(self):
        """Oyunu sıfırla"""
        self.frame = 0
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 50
        self.target = AdaptiveAITarget(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
        self.player_stats = PlayerStats()
        self.projectiles = []
        self.explosions = []
        self.hit_flash = 0
        self.miss_flash = 0
    
    def run(self):
        """Oyun döngüsünü çalıştır"""
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


def main():
    """Ana fonksiyon"""
    game = TargetingGame()
    game.run()


if __name__ == "__main__":
    main()
