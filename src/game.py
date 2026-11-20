"""
Ana Oyun Dosyası
Arcade tarzı adaptif AI'lı nişan alma oyunu
"""

import pygame # type: ignore
import math
import sys
import os
import glob
import json
import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from config import *
from player_stats import PlayerStats
from ai_target import AdaptiveAITarget
from data_logger import DataLogger
from model_select import select_model_path


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
        # Data logger for training dataset
        self.data_logger = DataLogger()
        # reset dataset now as requested by the user
        try:
            self.data_logger.reset_dataset()
            print("Training dataset reset: {}".format(self.data_logger.filepath))
        except Exception:
            pass
        self.shot_counter = 0
        # pending_shots: shot_id -> shot_info dict until result
        self.pending_shots = {}
        # shot history for UI (last N shots)
        self.shot_history = []  # list of dicts with keys: result, predicted_hit_prob, frame_shot, time_to_result_frames
        # ML model (loaded from models/) to predict hit probability
        self.ml_model = None
        self.ml_scaler = None
        self.ml_poly = None
        self.ml_model_name = None
        self.ml_model_metric = None
        self._load_best_model()

        # Online learning from hits: store positive examples and scaler
        self.positive_examples = []  # raw feature vectors
        self.positive_examples_scaled = None  # numpy array
        self.pos_scaler = StandardScaler()
        self.learned_policy_enabled = False
        # retrain trigger: retrain every N shots fired
        self.shots_since_retrain = 0
        self.retrain_every_n_shots = 10
        
        # Atış efektleri
        self.projectiles = []
        self.explosions = []
        
        # Görsel feeback
        self.hit_flash = 0
        self.miss_flash = 0
        # center message for instant result feedback
        self.center_msg = None
        self.center_msg_timer = 0
        # Aim hit cooldown to avoid repeating aim-hits every frame
        self.aim_hit_cooldown = 0
        # Manuel hedefleme: ortadaki ateş noktasını sabitleyip taşımak için
        self.manual_aim_mode = False
        # Başlangıçta aim noktası oyuncunun hedef çizgisi sonu civarında
        self.manual_aim_x = SCREEN_WIDTH // 2
        self.manual_aim_y = SCREEN_HEIGHT // 3
        self.manual_aim_speed = 8
        # UI / HUD settings
        self.settings = {
            'show_minimap': True,
            'show_shot_history': True,
            'show_predictions': True,
            'show_center_messages': True,
            'grid_opacity': 80,
        }
        # backup timer: every 30 seconds
        self.last_backup_frame = 0
        self.backup_interval_frames = FPS * 30
    
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
                elif event.key == pygame.K_m:
                    # Manuel hedefleme modu açık/kapalı
                    self.manual_aim_mode = not self.manual_aim_mode
                elif event.key == pygame.K_f:
                    # Manuel aim ile ateş et (eğer mod açıksa)
                    if not self.game_paused and self.manual_aim_mode:
                        self.player_shoot((self.manual_aim_x, self.manual_aim_y))
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Atış yap — fare tıklanan yere doğrudan ateş et (kilit yok)
                if not self.game_paused:
                    # event.pos is (x, y)
                    self.player_shoot(event.pos)
    
    def player_shoot(self, aim_pos=None):
        """Oyuncu ateş et. Eğer `aim_pos` verilmişse fareye doğru ateş et; aksi halde hedefe kilitlenir."""

        # Hedef pozisyonu (fare tıklaması, manuel aim veya mevcut hedef)
        if aim_pos is not None:
            aim_x, aim_y = aim_pos
        elif self.manual_aim_mode:
            aim_x, aim_y = self.manual_aim_x, self.manual_aim_y
        else:
            aim_x, aim_y = self.target.x, self.target.y

        # Atışı kaydet (hedef olarak tıklanan pozisyonu kaydet)
        self.player_stats.record_shot(
            (self.player_x, self.player_y),
            (aim_x, aim_y),
            self.frame
        )

        # Oluşan atış için ID oluştur ve özellikleri kaydet (CSV için)
        shot_id = self.shot_counter
        self.shot_counter += 1
        dx = aim_x - self.player_x
        dy = aim_y - self.player_y
        aim_dist = math.hypot(dx, dy)
        aim_angle = math.degrees(math.atan2(dy, dx)) if aim_dist > 0 else 0.0

        shot_info = {
            "shot_id": shot_id,
            "frame_shot": self.frame,
            "player_x": float(self.player_x),
            "player_y": float(self.player_y),
            "aim_x": float(aim_x),
            "aim_y": float(aim_y),
            "aim_dx": float(dx),
            "aim_dy": float(dy),
            "aim_angle_deg": float(aim_angle),
            "aim_distance": float(aim_dist),
            "target_x_at_shot": float(self.target.x),
            "target_y_at_shot": float(self.target.y),
            "target_speed": float(self.target.speed),
            "target_difficulty": float(self.target.difficulty),
            "target_strategy_state": self.target.strategy_state,
            "manual_aim_mode": bool(self.manual_aim_mode),
        }

        # Basit heuristic: yakın mesafe ve açıya göre hızlı kaçış tetikle
        try:
            target_ang = math.degrees(math.atan2(self.target.y - self.player_y, self.target.x - self.player_x))
            aim_ang = shot_info.get('aim_angle_deg', 0.0)
            diff = abs(((aim_ang - target_ang + 180) % 360) - 180)
            if shot_info.get('aim_distance', 9999.0) < 150 and diff < 15:
                self.target.evasion_strength = min(1.0, self.target.evasion_strength + 0.8)
                if self.settings.get('show_center_messages', True):
                    self.center_msg = ('HEURISTIC', (255, 200, 0))
                    self.center_msg_timer = 20
        except Exception:
            pass

        # If we have a trained model, predict hit probability and use it to influence target
        prob = None
        # Prefer online learned positives if available
        if len(self.positive_examples) > 0:
            try:
                feats = [
                    shot_info[c] for c in [
                        "player_x","player_y","aim_x","aim_y","aim_dx","aim_dy",
                        "aim_angle_deg","aim_distance","target_x_at_shot","target_y_at_shot",
                        "target_speed","target_difficulty","manual_aim_mode"
                    ]
                ]
                prob = self._predict_from_positives(feats)
                if prob is not None:
                    shot_info['predicted_hit_prob'] = float(prob)
                    # Use prediction to make target more evasive if predicted hit probability is high
                    try:
                        self.target.evasion_strength = min(1.0, self.target.evasion_strength + 0.5 * prob)
                        if prob > 0.5:
                            self.target.strategy_state = 'evade'
                            self.target.strategy_timer = max(self.target.strategy_timer, 10)
                    except Exception:
                        pass
            except Exception:
                prob = None
        elif self.ml_model is not None:
            try:
                feats = [
                    shot_info[c] for c in [
                        "player_x","player_y","aim_x","aim_y","aim_dx","aim_dy",
                        "aim_angle_deg","aim_distance","target_x_at_shot","target_y_at_shot",
                        "target_speed","target_difficulty","manual_aim_mode"
                    ]
                ]
                prob = self._predict_hit_prob(feats)
                shot_info['predicted_hit_prob'] = float(prob)
                # Use prediction to make target more evasive if predicted hit probability is high
                try:
                    # increase evasion a bit proportional to predicted hit prob
                    self.target.evasion_strength = min(1.0, self.target.evasion_strength + 0.5 * prob)
                    if prob > 0.5:
                        self.target.strategy_state = 'evade'
                        self.target.strategy_timer = max(self.target.strategy_timer, 10)
                except Exception:
                    pass
            except Exception:
                pass

        # Store pending shot until hit/miss resolved
        self.pending_shots[shot_id] = shot_info

        # increment retrain counter and trigger online retrain periodically
        try:
            self.shots_since_retrain += 1
            if self.shots_since_retrain >= self.retrain_every_n_shots:
                self.shots_since_retrain = 0
                try:
                    self._retrain_online_from_csv()
                except Exception:
                    pass
        except Exception:
            pass

        # Tıklanan konuma yönlendirilmiş bir ışın oluştur
        dx = aim_x - self.player_x
        dy = aim_y - self.player_y
        dist = math.hypot(dx, dy)

        if dist > 0:
            # Hızı normalize et
            speed = 15
            vx = (dx / dist) * speed
            vy = (dy / dist) * speed

            # Atışı ekle - include shot features so AI can use them later
            proj = {
                'x': self.player_x,
                'y': self.player_y,
                'vx': vx,
                'vy': vy,
                'life': 200,  # Kaç frame sürer
                'shot_id': shot_id,
                # original aim/shot features
                'aim_x': float(aim_x),
                'aim_y': float(aim_y),
                'aim_dx': float(dx),
                'aim_dy': float(dy),
                'aim_angle_deg': float(aim_angle),
                'aim_distance': float(aim_dist),
                'target_x_at_shot': float(self.target.x),
                'target_y_at_shot': float(self.target.y),
                'target_speed': float(self.target.speed),
                'target_difficulty': float(self.target.difficulty),
                'manual_aim_mode': float(bool(self.manual_aim_mode)),
            }
            self.projectiles.append(proj)
    
    def update(self):
        """Oyunu güncelle"""
        if self.game_paused:
            return
        self.frame += 1

        # --- Detect player's green aim line intersection with target ---
        # Compute the visual aim line end point (same as in _draw_player)
        # If manual aim mode is active, use manual aim point instead of target
        aim_target_x = self.manual_aim_x if self.manual_aim_mode else self.target.x
        aim_target_y = self.manual_aim_y if self.manual_aim_mode else self.target.y
        dx = aim_target_x - self.player_x
        dy = aim_target_y - self.player_y
        dist = math.hypot(dx, dy)
        if dist > 0:
            aim_len = 150
            end_x = self.player_x + (dx / dist) * aim_len
            end_y = self.player_y + (dy / dist) * aim_len

            # compute distance from target center to segment (player -> end)
            px, py = self.player_x, self.player_y
            sx, sy = end_x - px, end_y - py
            seg_len_sq = sx * sx + sy * sy
            t = 0.0
            if seg_len_sq > 0:
                t = ((self.target.x - px) * sx + (self.target.y - py) * sy) / seg_len_sq
                t = max(0.0, min(1.0, t))
            closest_x = px + sx * t
            closest_y = py + sy * t
            ddx = self.target.x - closest_x
            ddy = self.target.y - closest_y
            dist_to_line = math.hypot(ddx, ddy)

            # If the aim line is close, make the target go into evade mode
            if dist_to_line <= TARGET_SIZE + 60:
                # encourage evade behavior
                self.target.strategy_state = "evade"
                self.target.strategy_timer = max(self.target.strategy_timer, 20)
                self.target.evasion_strength = min(1.0, self.target.evasion_strength + 0.35)

            # If the aim line actually touches the target, count it as a hit (with cooldown)
            if dist_to_line <= TARGET_SIZE + 2 and self.frame > self.aim_hit_cooldown:
                self.player_stats.record_hit()
                self.hit_flash = 10
                self._create_explosion(self.target.x, self.target.y)
                # move target to a new safe location
                self.target.x = SCREEN_WIDTH * 0.2 + (SCREEN_WIDTH * 0.6 * (self.frame % 1000) / 1000)
                self.target.y = SCREEN_HEIGHT * 0.2 + (SCREEN_HEIGHT * 0.4 * ((self.frame + 500) % 1000) / 1000)
                self.aim_hit_cooldown = self.frame + 30
                # If we have a recently created pending shot, mark it as hit
                # Use latest pending shot (highest id)
                if len(self.pending_shots) > 0:
                    latest_sid = max(self.pending_shots.keys())
                    info = self.pending_shots.pop(latest_sid)
                    written = self.data_logger.finalize_and_write(info, 'hit', self.frame)
                    # update shot history UI
                    try:
                        self.shot_history.append({
                            'result': 'hit',
                            'predicted': written.get('predicted_hit_prob'),
                            'frame_shot': written.get('frame_shot'),
                            'time_to_result_frames': written.get('time_to_result_frames')
                        })
                        self.shot_history = self.shot_history[-5:]
                    except Exception:
                        pass
                    if self.settings.get('show_center_messages', True):
                        self.center_msg = ('HIT', (50, 255, 50))
                        self.center_msg_timer = 30
                    # online learn from this hit
                    try:
                        self._add_positive_example(written)
                    except Exception:
                        pass

        # Hedefi güncelle
        self.target.update(
            (self.player_x, self.player_y),
            self.player_stats,
            self.frame,
            projectiles=self.projectiles
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

                # Eğer bu projeye ait bir shot_id varsa kaydı finalize et
                sid = proj.get('shot_id')
                if sid is not None and sid in self.pending_shots:
                    info = self.pending_shots.pop(sid)
                    # include any evade direction recorded on the projectile
                    try:
                        info['evade_angle_deg'] = proj.get('evade_angle_deg')
                    except Exception:
                        pass
                    written = self.data_logger.finalize_and_write(info, 'hit', self.frame)
                    try:
                        self.shot_history.append({
                            'result': 'hit',
                            'predicted': written.get('predicted_hit_prob'),
                            'frame_shot': written.get('frame_shot'),
                            'time_to_result_frames': written.get('time_to_result_frames')
                        })
                        self.shot_history = self.shot_history[-5:]
                    except Exception:
                        pass
                    if self.settings.get('show_center_messages', True):
                        self.center_msg = ('HIT', (50, 255, 50))
                        self.center_msg_timer = 30

                        # online learn from this hit
                        try:
                            self._add_positive_example(written)
                        except Exception:
                            pass

                to_remove.append(i)
            
            # Ekran dışına çıktıysa sil
            elif (proj['x'] < 0 or proj['x'] > SCREEN_WIDTH or
                  proj['y'] < 0 or proj['y'] > SCREEN_HEIGHT):
                self.player_stats.record_miss()
                self.miss_flash = 5
                # finalize as miss if shot_id present
                sid = proj.get('shot_id')
                if sid is not None and sid in self.pending_shots:
                    info = self.pending_shots.pop(sid)
                    try:
                        info['evade_angle_deg'] = proj.get('evade_angle_deg')
                    except Exception:
                        pass
                    written = self.data_logger.finalize_and_write(info, 'miss', self.frame)
                    try:
                        self.shot_history.append({
                            'result': 'miss',
                            'predicted': written.get('predicted_hit_prob'),
                            'frame_shot': written.get('frame_shot'),
                            'time_to_result_frames': written.get('time_to_result_frames')
                        })
                        self.shot_history = self.shot_history[-5:]
                    except Exception:
                        pass
                    if self.settings.get('show_center_messages', True):
                        self.center_msg = ('MISS', (255, 50, 50))
                        self.center_msg_timer = 20
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

    def _load_best_model(self):
        """Load the model selected by `select_model_path()` or FORCE_MODEL.

        Uses `src/model_select.select_model_path()` to determine which file to
        load. Sets `self.ml_model`, `self.ml_scaler`, `self.ml_poly` and
        `self.ml_model_name`/`ml_model_metric` (if available from metrics.json).
        """
        try:
            model_path = select_model_path()
            if not model_path or not os.path.exists(model_path):
                print("No ML model found to load.")
                return

            model_dict = joblib.load(model_path)
            self.ml_model = model_dict.get('model')
            self.ml_scaler = model_dict.get('scaler')
            self.ml_poly = model_dict.get('poly', None)

            # display name (basename)
            self.ml_model_name = os.path.basename(model_path)

            # try to load metrics.json to show the primary metric (f1)
            try:
                model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
                metrics_path = os.path.join(model_dir, 'metrics.json')
                if os.path.exists(metrics_path):
                    with open(metrics_path, 'r', encoding='utf-8') as mf:
                        metrics = json.load(mf)
                    # metrics keys are filenames
                    m = metrics.get(self.ml_model_name)
                    if m is not None:
                        self.ml_model_metric = float(m.get('f1', 0.0))
                    else:
                        # if best_model.json exists, try to read it
                        best_json = os.path.join(model_dir, 'best_model.json')
                        if os.path.exists(best_json):
                            with open(best_json, 'r', encoding='utf-8') as bf:
                                bi = json.load(bf)
                            if bi.get('best_file') == self.ml_model_name:
                                self.ml_model_metric = float(bi.get('f1', 0.0))
            except Exception:
                self.ml_model_metric = None

            print(f"Loaded ML model from {model_path} (name={self.ml_model_name})")
        except Exception as e:
            print("Error loading ML model:", e)
            self.ml_model = None
            self.ml_scaler = None
            self.ml_poly = None

    def _predict_hit_prob(self, features):
        """Predict hit probability for given feature list (order must match training FEATURE_COLS)."""
        try:
            import numpy as _np
            X = _np.array(features).reshape(1, -1)
            # apply scaler if present
            if self.ml_scaler is not None:
                Xs = self.ml_scaler.transform(X)
            else:
                Xs = X
            # polynomial transform if present
            if self.ml_poly is not None:
                Xs = self.ml_poly.transform(Xs)
            # predict
            if hasattr(self.ml_model, 'predict_proba'):
                prob = float(self.ml_model.predict_proba(Xs)[0, 1])
                return max(0.0, min(1.0, prob))
            elif hasattr(self.ml_model, 'decision_function'):
                val = float(self.ml_model.decision_function(Xs))
                # map to (0,1) via logistic
                p = 1.0 / (1.0 + _np.exp(-val))
                return float(max(0.0, min(1.0, p)))
            else:
                pred = float(self.ml_model.predict(Xs)[0])
                return 1.0 if pred > 0.5 else 0.0
        except Exception:
            return None

    def _predict_from_positives(self, features):
        """Compute a similarity-based probability against stored positive examples.

        Returns a float in [0,1] or None if not possible.
        """
        try:
            X = np.array(features).reshape(1, -1)
            # scale using pos_scaler if it has been fit
            try:
                Xs = self.pos_scaler.transform(X)
            except Exception:
                Xs = X

            if self.positive_examples_scaled is None or len(self.positive_examples) == 0:
                return None

            # compute euclidean distances to positive examples
            dists = np.linalg.norm(self.positive_examples_scaled - Xs, axis=1)
            min_d = float(np.min(dists))
            # robust sigma: median distance or fallback
            sigma = float(max(0.5, np.median(dists)))
            # Gaussian kernel -> probability
            prob = float(np.exp(-(min_d**2) / (2.0 * (sigma**2))))
            return max(0.0, min(1.0, prob))
        except Exception:
            return None

    def _retrain_online_from_csv(self):
        """Retrain a simple RandomForest using hits from CSV and synthetic negatives.

        This trains an online RandomForest saved to models/online_rf.joblib and
        updates `self.ml_model`/`self.ml_scaler` so the game can use it immediately.
        Only rows with result=='hit' are used as positives; negatives are
        synthesized by sampling random aims/positions to balance the dataset.
        """
        try:
            import csv, os
            from sklearn.preprocessing import StandardScaler
            from sklearn.ensemble import RandomForestClassifier
            CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'training_shots.csv')
            if not os.path.exists(CSV_PATH):
                return
            rows = []
            with open(CSV_PATH, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)

            # take only hits
            hits = [r for r in rows if str(r.get('result','')).lower().strip() == 'hit']
            if len(hits) < 3:
                # not enough positive examples to train
                return

            FEATURE_COLS = [
                "player_x",
                "player_y",
                "aim_x",
                "aim_y",
                "aim_dx",
                "aim_dy",
                "aim_angle_deg",
                "aim_distance",
                "target_x_at_shot",
                "target_y_at_shot",
                "target_speed",
                "target_difficulty",
                "manual_aim_mode",
            ]

            X_pos = []
            for r in hits:
                try:
                    feats = [float(r.get(c, 0.0)) for c in FEATURE_COLS]
                except Exception:
                    continue
                X_pos.append(feats)

            X_pos = np.array(X_pos)
            n_pos = X_pos.shape[0]

            # create synthetic negatives by sampling random aim/player positions
            negs = []
            for _ in range(n_pos):
                px = float(np.random.uniform(0, SCREEN_WIDTH))
                py = float(np.random.uniform(0, SCREEN_HEIGHT))
                ax = float(np.random.uniform(0, SCREEN_WIDTH))
                ay = float(np.random.uniform(0, SCREEN_HEIGHT))
                dx = ax - px
                dy = ay - py
                dist = float(math.hypot(dx, dy))
                ang = float(math.degrees(math.atan2(dy, dx))) if dist > 0 else 0.0
                tx = float(np.random.uniform(0, SCREEN_WIDTH))
                ty = float(np.random.uniform(0, SCREEN_HEIGHT))
                ts = float(np.random.uniform(TARGET_MIN_SPEED, TARGET_MAX_SPEED))
                td = float(np.random.uniform(MIN_DIFFICULTY, MAX_DIFFICULTY))
                manual = 0.0
                negs.append([px, py, ax, ay, dx, dy, ang, dist, tx, ty, ts, td, manual])

            X_neg = np.array(negs)

            X = np.vstack([X_pos, X_neg])
            y = np.hstack([np.ones(n_pos), np.zeros(n_pos)])

            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)

            # Train a small RandomForest
            rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            rf.fit(Xs, y)

            # save and load into current game
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
            os.makedirs(model_dir, exist_ok=True)
            path = os.path.join(model_dir, 'online_rf.joblib')
            joblib.dump({'model': rf, 'scaler': scaler}, path)
            self.ml_model = rf
            self.ml_scaler = scaler
            # online RF is trained on raw scaled features; drop any poly transform from the loaded model
            self.ml_poly = None
            self.ml_model_name = 'online_rf.joblib'
            self.ml_model_metric = None
            print(f"Online retrain: trained RF with {n_pos} positives and saved to {path}")
            # Additionally, if there are recorded evade angles in CSV, train an
            # evade-direction classifier (discretized angles) so the AI can
            # predict which direction to run when similar shots occur.
            try:
                angle_rows = [r for r in rows if str(r.get('result','')).lower().strip() == 'hit' and r.get('evade_angle_deg')]
                if len(angle_rows) >= 3:
                    bins_n = 8
                    X_e = []
                    y_e = []
                    for r in angle_rows:
                        try:
                            feats = [float(r.get(c, 0.0)) for c in FEATURE_COLS]
                            ang = float(r.get('evade_angle_deg'))
                        except Exception:
                            continue
                        # convert angle (-180..180 or 0..360) to 0..360
                        ang = ang % 360
                        cls = int((ang / 360.0) * bins_n) % bins_n
                        X_e.append(feats)
                        y_e.append(cls)
                    if len(y_e) >= 3:
                        X_e = np.array(X_e)
                        y_e = np.array(y_e)
                        scaler_e = StandardScaler()
                        X_e_s = scaler_e.fit_transform(X_e)
                        clf = RandomForestClassifier(n_estimators=120, random_state=42, class_weight='balanced')
                        clf.fit(X_e_s, y_e)
                        evade_path = os.path.join(model_dir, 'online_evade.joblib')
                        joblib.dump({'model': clf, 'scaler': scaler_e, 'bins': bins_n}, evade_path)
                        # attach to running target so it can use immediately
                        try:
                            self.target.evade_model = clf
                            self.target.evade_scaler = scaler_e
                            self.target.evade_bins_n = bins_n
                            print(f"Trained evade model with {len(y_e)} samples -> {evade_path}")
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass

    def _add_positive_example(self, shot_info):
        """Add a hit example (features) to the online positives set and update scaler."""
        try:
            feats = [
                shot_info[c] for c in [
                    "player_x","player_y","aim_x","aim_y","aim_dx","aim_dy",
                    "aim_angle_deg","aim_distance","target_x_at_shot","target_y_at_shot",
                    "target_speed","target_difficulty","manual_aim_mode"
                ]
            ]
            arr = np.array(feats).reshape(1, -1)
            if len(self.positive_examples) == 0:
                # fit scaler first time
                try:
                    self.pos_scaler.fit(arr)
                except Exception:
                    pass
                self.positive_examples.append(feats)
                try:
                    self.positive_examples_scaled = np.array(self.pos_scaler.transform(arr))
                except Exception:
                    self.positive_examples_scaled = np.array(arr)
            else:
                # incremental update: use partial_fit on scaler if available
                try:
                    self.pos_scaler.partial_fit(arr)
                except Exception:
                    pass
                self.positive_examples.append(feats)
                try:
                    scaled_all = self.pos_scaler.transform(np.array(self.positive_examples))
                    self.positive_examples_scaled = scaled_all
                except Exception:
                    self.positive_examples_scaled = np.array(self.positive_examples)

            # enable learned policy in target
            try:
                self.learned_policy_enabled = True
                if hasattr(self.target, 'learned_policy_enabled'):
                    self.target.learned_policy_enabled = True
                # also pass hit location to target if available
                try:
                    hx = shot_info.get('target_x_at_shot') or shot_info.get('aim_x')
                    hy = shot_info.get('target_y_at_shot') or shot_info.get('aim_y')
                    if hx is not None and hy is not None and hasattr(self.target, 'record_hit_location'):
                        self.target.record_hit_location(hx, hy)
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass
    
    def _update_screen_controls(self):
        """Oyuncu kontrollerini işle"""
        keys = pygame.key.get_pressed()
        # Eğer manuel hedefleme aktifse, WASD ile aim noktasını hareket ettir
        if self.manual_aim_mode:
            if keys[pygame.K_a]:
                self.manual_aim_x -= self.manual_aim_speed
            if keys[pygame.K_d]:
                self.manual_aim_x += self.manual_aim_speed
            if keys[pygame.K_w]:
                self.manual_aim_y -= self.manual_aim_speed
            if keys[pygame.K_s]:
                self.manual_aim_y += self.manual_aim_speed
            # Clamp manual aim inside screen
            self.manual_aim_x = max(0, min(SCREEN_WIDTH, self.manual_aim_x))
            self.manual_aim_y = max(0, min(SCREEN_HEIGHT, self.manual_aim_y))
        else:
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
        # Eğer manuel aim modu açıksa, çizgiyi manuel aim noktasına çiz
        aim_x = self.manual_aim_x if self.manual_aim_mode else self.target.x
        aim_y = self.manual_aim_y if self.manual_aim_mode else self.target.y
        dx = aim_x - self.player_x
        dy = aim_y - self.player_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            end_x = self.player_x + (dx / dist) * 150
            end_y = self.player_y + (dy / dist) * 150
            pygame.draw.line(self.screen, GREEN, 
                           (self.player_x, self.player_y),
                           (end_x, end_y), 1)
        # Manuel aim modunda küçük hedef imleci çiz
        if self.manual_aim_mode:
            # draw translucent reticle
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 50, 160), (20, 20), 8, 2)
            pygame.draw.line(s, (255, 255, 50, 160), (20, 0), (20, 40), 1)
            pygame.draw.line(s, (255, 255, 50, 160), (0, 20), (40, 20), 1)
            self.screen.blit(s, (int(self.manual_aim_x) - 20, int(self.manual_aim_y) - 20))
        else:
            # draw small crosshair at center of screen for aiming
            cx, cy = int(self.player_x + (aim_x - self.player_x) * 0.6), int(self.player_y + (aim_y - self.player_y) * 0.6)
            s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.line(s, (50, 255, 50, 140), (25, 0), (25, 50), 2)
            pygame.draw.line(s, (50, 255, 50, 140), (0, 25), (50, 25), 2)
            pygame.draw.circle(s, (50, 255, 50, 80), (25, 25), 10, 1)
            self.screen.blit(s, (cx - 25, cy - 25))
    
    def _draw_target(self):
        """Hedefi çiz"""
        color = TARGET_COLOR

        # Vurulmuş efekti
        if self.hit_flash > 0:
            color = YELLOW

        # pulsate ring based on strategy_timer
        ring_extra = 0
        try:
            ring_extra = int(6 * (1 + math.sin(self.frame * 0.2))) if self.target.strategy_state == 'evade' else 2
        except Exception:
            ring_extra = 2

        pygame.draw.circle(self.screen, color,
                          (int(self.target.x), int(self.target.y)), 
                          TARGET_SIZE)

        # draw hit-probability bar above target if enabled
        if self.settings.get('show_predictions', True) and hasattr(self.target, 'predicted_hit_prob'):
            prob = getattr(self.target, 'predicted_hit_prob', None)
            if prob is not None:
                bw = 60
                bh = 8
                bx = int(self.target.x - bw/2)
                by = int(self.target.y - TARGET_SIZE - 16)
                pygame.draw.rect(self.screen, GRAY, (bx, by, bw, bh), 1)
                pygame.draw.rect(self.screen, (200,50,50), (bx+1, by+1, int((bw-2)*prob), bh-2))

        # Hedef etrafında halkalar (strateji göstergesi)
        if self.target.strategy_state != "wander":
            ring_color = (100, 100, 255) if self.target.strategy_state == "evade" else \
                        (200, 100, 255) if self.target.strategy_state == "fake_dodge" else \
                        (255, 100, 50)
            pygame.draw.circle(self.screen, ring_color,
                              (int(self.target.x), int(self.target.y)), 
                              TARGET_SIZE + 10 + ring_extra, 2)
    
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

    def _draw_minimap(self):
        """Çok basit minimap (sağ üst köşe)."""
        try:
            mw, mh = 160, 120
            mx = SCREEN_WIDTH - mw - 10
            my = 10
            pygame.draw.rect(self.screen, (30, 30, 30), (mx, my, mw, mh))
            pygame.draw.rect(self.screen, GRAY, (mx, my, mw, mh), 1)

            # scale world positions to minimap
            def to_minimap(px, py):
                sx = int(mx + (px / SCREEN_WIDTH) * mw)
                sy = int(my + (py / SCREEN_HEIGHT) * mh)
                return sx, sy

            # player
            px, py = to_minimap(self.player_x, self.player_y)
            pygame.draw.circle(self.screen, PLAYER_COLOR, (px, py), 4)

            # target
            tx, ty = to_minimap(self.target.x, self.target.y)
            pygame.draw.circle(self.screen, TARGET_COLOR, (tx, ty), 5)

            # recent shots
            for i, s in enumerate(reversed(self.shot_history[-10:])):
                # map shot aim position if exists
                try:
                    sx, sy = to_minimap(s.get('aim_x', self.player_x), s.get('aim_y', self.player_y))
                    col = (50, 200, 50) if s.get('result') == 'hit' else (200, 50, 50)
                    pygame.draw.circle(self.screen, col, (sx, sy), 2)
                except Exception:
                    continue
        except Exception:
            pass

    def _draw_shot_history(self):
        """Basit atış geçmişi paneli (alt sağ)."""
        try:
            w, h = 220, 110
            x = SCREEN_WIDTH - w - 10
            y = SCREEN_HEIGHT - h - 60
            pygame.draw.rect(self.screen, (18, 18, 18), (x, y, w, h))
            pygame.draw.rect(self.screen, GRAY, (x, y, w, h), 1)
            title = self.small_font.render("Shot History", True, WHITE)
            self.screen.blit(title, (x + 8, y + 6))

            for i, s in enumerate(reversed(self.shot_history[-5:])):
                ry = y + 30 + i * 18
                res = s.get('result', 'unknown')
                pred = s.get('predicted')
                col = (50, 200, 50) if res == 'hit' else (200, 50, 50)
                pygame.draw.circle(self.screen, col, (x + 12, ry + 6), 5)
                txt = f"{res.upper():4}  p={pred:.2f}" if pred is not None else f"{res.upper():4}  p=?"
                surf = self.small_font.render(txt, True, WHITE)
                self.screen.blit(surf, (x + 26, ry))
        except Exception:
            pass
    
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
            f"Manual Aim: {'ON' if self.manual_aim_mode else 'OFF'}",
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
            "OK: Atış Et | Yönler: Hareket | SPACE: Durdur | ESC: Çık | R: Yenile",
            "M: Manuel Aim Aç/Kapa | WASD: Aim Taşı (Manuel) | F: Manuel Ateş"
        ]
        
        for i, text in enumerate(controls):
            surface = self.small_font.render(text, True, GRAY)
            self.screen.blit(surface, (10, SCREEN_HEIGHT - 35 + (i * 30)))

        # Draw live model prediction on HUD
        if self.settings.get('show_predictions', True) and self.ml_model is not None:
            name = self.ml_model_name or 'model'
            if self.ml_model_metric is not None:
                pred_text = f"Model: {name}  F1={self.ml_model_metric:.3f}"
            else:
                pred_text = f"Model: {name}"
            # indicate if FORCE_MODEL is being used
            try:
                if FORCE_MODEL:
                    pred_text = f"Forced model: {name}"
            except Exception:
                pass
            # Draw highlighted background for visibility
            try:
                surf = self.small_font.render(pred_text, True, WHITE)
                pw, ph = surf.get_size()
                bx = SCREEN_WIDTH - pw - 22
                by = SCREEN_HEIGHT - ph - 18
                pygame.draw.rect(self.screen, (30, 30, 30), (bx - 6, by - 4, pw + 12, ph + 8))
                pygame.draw.rect(self.screen, (200, 180, 60), (bx - 6, by - 4, pw + 12, ph + 8), 2)
                self.screen.blit(surf, (bx, by))
            except Exception:
                pass

        # draw center message
        if self.center_msg_timer > 0 and self.center_msg is not None:
            txt, color = self.center_msg
            surf = self.font.render(txt, True, color)
            rw = surf.get_width()
            self.screen.blit(surf, ((SCREEN_WIDTH - rw) // 2, SCREEN_HEIGHT // 2 - 40))
            self.center_msg_timer -= 1
        else:
            self.center_msg = None

        # Draw minimap
        if self.settings.get('show_minimap', True):
            self._draw_minimap()

        # Draw shot history panel
        if self.settings.get('show_shot_history', True):
            self._draw_shot_history()
        
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
