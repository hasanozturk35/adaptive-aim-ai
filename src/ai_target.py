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
        # Idle means stay still unless a projectile enters the reactive radius
        self.strategy_state = "idle"      # idle, wander, evade, fake_dodge, sprint
        self.strategy_timer = 0
        self.strategy_cooldown = 0
        # If True, use learned policy (deterministic evasion) instead of random wandering
        self.learned_policy_enabled = False
        
        # Ani yön değişimi
        self.fake_dodge_timer = 0
        self.fake_dodge_active = False
        
        # Sprint modu
        self.sprint_timer = 0
        self.is_sprinting = False

        # Edge-stuck protection
        self.edge_frames = 0
        # Only react/move when a projectile enters this radius (pixels)
        self.projectile_trigger_radius = max(120, TARGET_SIZE * 6)
        # last frame where an incoming projectile was detected
        self.last_incoming_frame = -999999
        # Optional learned evade model (set by game after training)
        self.evade_model = None
        self.evade_scaler = None
        self.evade_bins_n = None
        
        # İstatistik takibi
        self.frames_since_last_adaptation = 0
        self.dodge_success_count = 0
        # Öğrenilen vurulma konumları: list of {'x','y','weight'}
        self.hit_locations = []
        
    def update(self, player_pos, player_stats, frame, projectiles=None):
        """Hedefi güncelle ve AI kararlarını al"""
        
        # Zorluk seviyesini oyuncu performansına göre ayarla
        self._adapt_difficulty(player_stats)
        
        # Check incoming projectiles first (only react to projectiles within
        # the target's reactive radius)
        if projectiles is not None:
            self._detect_and_respond_projectiles(projectiles, frame, player_pos)

        # Davranış stratejisini belirle
        self._update_strategy(player_pos, frame)
        
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
        # Hit konumlarından da öğren
        self._decay_hit_locations()

    def record_hit_location(self, x, y):
        """Record a location where the target was hit; aggregate nearby hits."""
        try:
            x = float(x)
            y = float(y)
        except Exception:
            return

        # Merge with existing close location
        merged = False
        for loc in self.hit_locations:
            dx = loc['x'] - x
            dy = loc['y'] - y
            if (dx*dx + dy*dy) < (60*60):
                loc['weight'] += 1.0
                # update centroid a bit
                loc['x'] = (loc['x'] * 0.7) + (x * 0.3)
                loc['y'] = (loc['y'] * 0.7) + (y * 0.3)
                merged = True
                break
        if not merged:
            self.hit_locations.append({'x': x, 'y': y, 'weight': 1.0})

    def _decay_hit_locations(self):
        """Decay hit location weights over time and remove tiny ones."""
        new_locs = []
        for loc in self.hit_locations:
            loc['weight'] *= 0.995
            if loc['weight'] >= 0.05:
                new_locs.append(loc)
        self.hit_locations = new_locs
    
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
    
    def _update_strategy(self, player_pos, frame):
        """Decide which strategy to use.

        The target should remain idle (no movement) unless an incoming
        projectile was detected recently (within a few frames). When a
        projectile enters the reactive radius it is handled in
        _detect_and_respond_projectiles which sets `strategy_state='evade'`.
        Here we keep the default idle state otherwise, only allowing evasive
        behavior when `last_incoming_frame` is recent.
        """
        # If a projectile was detected very recently, keep the evade state
        # active for a short window so the target can fully respond.
        recent_window = 12
        if (frame - self.last_incoming_frame) <= recent_window:
            # let existing strategy (likely set by detection) run out its timer
            return

        # No recent incoming projectile: stay idle (no intentional movement)
        # but allow other systems (edge nudges) to move the target if stuck.
        if self.strategy_state != 'idle':
            self.strategy_state = 'idle'
            self.strategy_timer = 0
            self.strategy_cooldown = 0
    
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

        # If we're too close to screen edges for a while, push toward center
        margin = self.size * 2
        near_edge = (self.x < margin or self.x > SCREEN_WIDTH - margin or
                     self.y < margin or self.y > SCREEN_HEIGHT - margin)
        if near_edge:
            self.edge_frames += 1
        else:
            self.edge_frames = 0

        if self.edge_frames > 20:
            # nudge toward center and boost speed briefly
            cx = SCREEN_WIDTH / 2
            cy = SCREEN_HEIGHT / 2
            dx = cx - self.x
            dy = cy - self.y
            d = math.hypot(dx, dy) or 1.0
            self.velocity_x = (dx / d) * max(self.speed, TARGET_MAX_SPEED)
            self.velocity_y = (dy / d) * max(self.speed, TARGET_MAX_SPEED)
            self.edge_frames = 0
    
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
        
        # Öğrenilen açılardan ve vurulma konumlarından daha çok kaç
        if dist > 0:
            # Evasion vektörü (temel)
            ex = (dx / dist) * self.evasion_strength
            ey = (dy / dist) * self.evasion_strength

            # If there are learned hit locations, compute repulsion from them
            if len(self.hit_locations) > 0:
                rx, ry = 0.0, 0.0
                total_w = 0.0
                for loc in self.hit_locations:
                    lx, ly, w = loc['x'], loc['y'], loc['weight']
                    ddx = self.x - lx
                    ddy = self.y - ly
                    distl = math.hypot(ddx, ddy) + 1e-6
                    # weight influence decreases with distance
                    influence = w / (1.0 + distl / 120.0)
                    rx += (ddx / distl) * influence
                    ry += (ddy / distl) * influence
                    total_w += influence
                if total_w > 0:
                    rx /= total_w
                    ry /= total_w
                    # blend repulsion into evasion vector
                    ex += rx * (0.8 + 0.6 * self.evasion_strength)
                    ey += ry * (0.8 + 0.6 * self.evasion_strength)

            # Rastgeleliği azalt: learned policy varsa daha az rastgelelik
            rand_scale = 1.0 - min(0.7, self.evasion_strength)
            side_angle = random.uniform(-math.pi/4 * rand_scale, math.pi/4 * rand_scale)
            sx = math.cos(side_angle) * (1 - self.evasion_strength) * 0.6
            sy = math.sin(side_angle) * (1 - self.evasion_strength) * 0.6

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

    def _detect_and_respond_projectiles(self, projectiles, frame, player_pos):
        """Detect incoming projectiles and bias strategy toward evasion.

        projectiles: iterable of dicts with keys 'x','y','vx','vy'.
        """
        try:
            incoming = []
            for p in projectiles:
                px, py = p.get('x'), p.get('y')
                vx, vy = p.get('vx', 0.0), p.get('vy', 0.0)
                if px is None or py is None:
                    continue
                # vector from projectile to target
                dx = self.x - px
                dy = self.y - py
                dist = math.hypot(dx, dy)
                if dist <= 0:
                    continue

                speed = math.hypot(vx, vy) or 1.0

                # If projectile is not generally moving toward the target, skip
                dot = (dx * vx + dy * vy)
                if dot <= 0:
                    continue

                # Predict closest approach assuming projectile continues straight
                # t* = -v . (p - T) / |v|^2  (time in frames)
                v_norm_sq = vx * vx + vy * vy
                if v_norm_sq <= 1e-8:
                    continue
                t_star = -((px - self.x) * vx + (py - self.y) * vy) / v_norm_sq
                # ignore if closest approach already happened
                if t_star < 0:
                    continue

                # if projectile has 'life' (frames left) and closest approach is after it expires, skip
                life = p.get('life')
                try:
                    if life is not None and float(t_star) > float(life):
                        continue
                except Exception:
                    pass

                # compute closest approach point and distance
                cx = px + vx * t_star
                cy = py + vy * t_star
                closest_dist = math.hypot(self.x - cx, self.y - cy)

                # compute distance to infinite line using cross product formula:
                # d = |(C - P) x v| / |v|
                C_Px = self.x - px
                C_Py = self.y - py
                vnorm = math.hypot(vx, vy) or 1.0
                # 2D cross product magnitude = |x1*y2 - y1*x2|
                cross = abs(C_Px * vy - C_Py * vx)
                d_line = cross / vnorm

                # If projectile would miss the target even when target remains stationary,
                # then it's not a real threat and we can ignore it.
                # Use character width (`self.size`) as the critical threshold.
                hit_margin = self.size
                if d_line > hit_margin:
                    continue

                # Also only react if it is within reactive radius now or will be soon
                if dist <= self.projectile_trigger_radius or t_star <= 30:
                    incoming.append((p, closest_dist, speed, dot, t_star))
            if len(incoming) == 0:
                return

            # Aggregate influence from incoming projectiles
            # If we have an evade model, use it to decide a direction for the
            # most threatening incoming projectile; otherwise fall back to
            # aggregating repulsion as before.
            rx, ry = 0.0, 0.0
            total_w = 0.0

            # pick most threatening projectile (closest)
            incoming_sorted = sorted(incoming, key=lambda t: t[1])
            chosen_tuple = incoming_sorted[0]
            # unpack chosen tuple -> (p, closest_dist, speed, dot, t_star)
            chosen = chosen_tuple[0]
            chosen_closest = chosen_tuple[1]
            chosen_speed = chosen_tuple[2]
            chosen_dot = chosen_tuple[3]
            chosen_tstar = chosen_tuple[4]

            used_model = False
            try:
                if hasattr(self, 'evade_model') and self.evade_model is not None and self.evade_scaler is not None:
                    # Build feature vector expected by the model
                    FEATURE_COLS = [
                        'player_x','player_y','aim_x','aim_y','aim_dx','aim_dy',
                        'aim_angle_deg','aim_distance','target_x_at_shot','target_y_at_shot',
                        'target_speed','target_difficulty','manual_aim_mode'
                    ]
                    fv = []
                    for c in FEATURE_COLS:
                        if c == 'player_x':
                            fv.append(float(player_pos[0]))
                        elif c == 'player_y':
                            fv.append(float(player_pos[1]))
                        else:
                            fv.append(float(chosen.get(c, 0.0)))
                    X = None
                    try:
                        X = self.evade_scaler.transform([fv])
                    except Exception:
                        X = [fv]
                    pred = None
                    try:
                        pred = int(self.evade_model.predict(X)[0])
                    except Exception:
                        pred = None
                    if pred is not None and self.evade_bins_n:
                        ang = ((pred + 0.5) / float(self.evade_bins_n)) * 360.0
                        rad = math.radians(ang)
                        rx = math.cos(rad)
                        ry = math.sin(rad)
                        # annotate chosen projectiles for logging
                        try:
                            chosen['evade_angle_deg'] = float(ang)
                        except Exception:
                            pass
                        used_model = True
            except Exception:
                used_model = False

            if not used_model:
                # fallback: compute a perpendicular dodge to the most threatening projectile
                try:
                    p = chosen
                    vx, vy = p.get('vx', 0.0), p.get('vy', 0.0)
                    px, py = p.get('x'), p.get('y')
                    # impact point (closest approach) using chosen_tstar
                    tstar = float(chosen_tstar)
                    cx = px + vx * tstar
                    cy = py + vy * tstar

                    # perpendicular directions to velocity
                    perp1 = (-vy, vx)
                    perp2 = (vy, -vx)

                    # choose perpendicular that moves target away from impact point
                    to_target = (self.x - cx, self.y - cy)
                    d1 = perp1[0] * to_target[0] + perp1[1] * to_target[1]
                    d2 = perp2[0] * to_target[0] + perp2[1] * to_target[1]
                    chosen_perp = perp1 if d1 >= d2 else perp2

                    # normalize
                    pn = math.hypot(chosen_perp[0], chosen_perp[1]) or 1.0
                    rx = chosen_perp[0] / pn
                    ry = chosen_perp[1] / pn
                except Exception:
                    rx, ry = 0.0, 0.0

            bias_strength = min(1.5, 0.5 + 0.5 * len(incoming))
            self.velocity_x += rx * bias_strength * (1.0 + self.evasion_strength)
            self.velocity_y += ry * bias_strength * (1.0 + self.evasion_strength)
            # set evade state and timers
            self.strategy_state = 'evade'
            self.strategy_timer = max(self.strategy_timer, 30)
            self.strategy_cooldown = max(self.strategy_cooldown, 20)
            # increase evasion strength temporarily
            self.evasion_strength = min(1.0, self.evasion_strength + 0.2)
            # record last incoming frame so the strategy logic knows why we moved
            try:
                self.last_incoming_frame = int(frame)
            except Exception:
                self.last_incoming_frame = frame
        except Exception:
            pass
    
    def _constrain_to_screen(self):
        """Ekran içinde tut: kenarlarda kısa süre kalmasına izin ver, ama sıkışırsa
        yumuşak bir itme ile içeri al.
        """

        margin = self.size
        pushed = False

        # X ekseni sınırlandırma ve yumuşak itme
        if self.x < margin:
            self.x = margin
            # ensure it moves inward
            self.velocity_x = abs(self.velocity_x) + 0.3 * self.speed + random.uniform(-0.2, 0.2)
            pushed = True
        elif self.x > SCREEN_WIDTH - margin:
            self.x = SCREEN_WIDTH - margin
            self.velocity_x = -abs(self.velocity_x) - 0.3 * self.speed + random.uniform(-0.2, 0.2)
            pushed = True

        # Y ekseni sınırlandırma ve yumuşak itme
        if self.y < margin:
            self.y = margin
            self.velocity_y = abs(self.velocity_y) + 0.3 * self.speed + random.uniform(-0.2, 0.2)
            pushed = True
        elif self.y > SCREEN_HEIGHT - margin:
            self.y = SCREEN_HEIGHT - margin
            self.velocity_y = -abs(self.velocity_y) - 0.3 * self.speed + random.uniform(-0.2, 0.2)
            pushed = True

        # Eğer birkaç frame boyunca kenarda kaldıysa, kuvvetli bir itme ile merkeze çek
        if pushed and self.edge_frames > 10:
            cx = SCREEN_WIDTH / 2.0
            cy = SCREEN_HEIGHT / 2.0
            dx = cx - self.x
            dy = cy - self.y
            d = math.hypot(dx, dy) or 1.0
            # stronger nudge toward center
            # if we have hit location learning, be more forceful to escape corners
            factor = self.speed * (2.0 if self.learned_policy_enabled else 1.5)
            self.velocity_x = (dx / d) * factor
            self.velocity_y = (dy / d) * factor
            # reset edge counter so we don't repeatedly nudge
            self.edge_frames = 0

        # If stuck near a corner or edge continuously, pick a new direction away
        margin = self.size * 3
        near_left = self.x <= margin
        near_right = self.x >= SCREEN_WIDTH - margin
        near_top = self.y <= margin
        near_bottom = self.y >= SCREEN_HEIGHT - margin
        if (near_left or near_right or near_top or near_bottom) and self.edge_frames > 5:
            # compute a safe direction: toward center with some random offset
            cx = SCREEN_WIDTH / 2.0
            cy = SCREEN_HEIGHT / 2.0
            dx = cx - self.x
            dy = cy - self.y
            ang = math.atan2(dy, dx)
            # offset angle to avoid repeating same path
            ang += random.uniform(-math.pi / 4, math.pi / 4)
            self.velocity_x = math.cos(ang) * self.speed * 1.5
            self.velocity_y = math.sin(ang) * self.speed * 1.5
            self.edge_frames = 0
    
    def get_difficulty_info(self):
        """Zorluk bilgisini döndür"""
        return {
            'level': self.difficulty,
            'strategy': self.strategy_state,
            'speed': self.speed,
            'evasion_strength': self.evasion_strength,
        }
