"""
Oyuncu İstatistikleri ve Analiz Sistemi
Oyuncunun atış açıları, zamanlaması ve isabet oranını izler
"""

import math
from collections import deque
from config import INITIAL_SHOTS_TO_TRACK


class PlayerStats:
    """Oyuncu performansını izleyen ve analiz eden sınıf"""
    
    def __init__(self):
        # Son atışların açıları (dereceler)
        self.shot_angles = deque(maxlen=INITIAL_SHOTS_TO_TRACK)
        
        # Son atışların başarı durumu (True/False)
        self.shot_hits = deque(maxlen=INITIAL_SHOTS_TO_TRACK)
        
        # Atış zamanlaması (frames arası)
        self.shot_intervals = deque(maxlen=INITIAL_SHOTS_TO_TRACK)
        
        # Son atış zamanı
        self.last_shot_time = None
        
        # Toplam istatistikler
        self.total_shots = 0
        self.total_hits = 0
        
        # Hedef konumu bilgisi (AI eğitimi için)
        self.target_positions_at_shot = deque(maxlen=INITIAL_SHOTS_TO_TRACK)
    
    def record_shot(self, player_pos, target_pos, current_time):
        """Bir atışı kaydet"""
        self.total_shots += 1
        
        # Atış açısını hesapla
        dx = target_pos[0] - player_pos[0]
        dy = target_pos[1] - player_pos[1]
        angle = math.degrees(math.atan2(dy, dx))
        self.shot_angles.append(angle)
        
        # Atış aralığını hesapla
        if self.last_shot_time is not None:
            interval = current_time - self.last_shot_time
            self.shot_intervals.append(interval)
        
        self.last_shot_time = current_time
        self.target_positions_at_shot.append(target_pos)
    
    def record_hit(self):
        """Başarılı bir atışı kaydet"""
        self.total_hits += 1
        self.shot_hits.append(True)
    
    def record_miss(self):
        """Başarısız bir atışı kaydet"""
        self.shot_hits.append(False)
    
    def get_hit_percentage(self):
        """İsabet yüzdesini hesapla"""
        if self.total_shots == 0:
            return 0.0
        return self.total_hits / self.total_shots
    
    def get_recent_hit_percentage(self):
        """Son atışlardaki isabet yüzdesini hesapla"""
        if len(self.shot_hits) == 0:
            return 0.0
        hits = sum(1 for h in self.shot_hits if h)
        return hits / len(self.shot_hits)
    
    def get_average_shot_interval(self):
        """Ortalama atış aralığını hesapla"""
        if len(self.shot_intervals) == 0:
            return 0.0
        return sum(self.shot_intervals) / len(self.shot_intervals)
    
    def get_dominant_angle_range(self):
        """Oyuncunun en çok attığı açı aralığını bul"""
        if len(self.shot_angles) == 0:
            return (0, 360)
        
        # Açıları 45 derece aralıklarla grupla
        angles_normalized = [(a % 360) for a in self.shot_angles]
        
        # En çok kullanılan açı aralığını bul
        ranges = {}
        for angle in angles_normalized:
            bucket = (int(angle / 45) * 45) % 360
            ranges[bucket] = ranges.get(bucket, 0) + 1
        
        if ranges:
            dominant_bucket = max(ranges, key=ranges.get)
            return (dominant_bucket, (dominant_bucket + 45) % 360)
        return (0, 360)
    
    def get_shooting_frequency(self):
        """Atış sıklığını hesapla (saniyede kaç atış)"""
        avg_interval = self.get_average_shot_interval()
        if avg_interval <= 0:
            return 0.0
        return 60.0 / avg_interval  # 60 frame = 1 saniye varsayılı
    
    def get_adaptation_profile(self):
        """AI adaptasyonu için oyuncu profilini oluştur"""
        return {
            'hit_percentage': self.get_recent_hit_percentage(),
            'shot_frequency': self.get_shooting_frequency(),
            'dominant_angles': self.get_dominant_angle_range(),
            'total_shots': self.total_shots,
            'avg_shot_interval': self.get_average_shot_interval(),
        }
