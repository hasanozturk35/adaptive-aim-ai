import csv
import os
from datetime import datetime
from typing import Optional


HEADER = [
    # which game launch the shot belongs to (old rows without it get "legacy")
    "session_id",
    "shot_id",
    "frame_shot",
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
    "target_strategy_state",
    "manual_aim_mode",
    "predicted_hit_prob",
    # angle (degrees) the target decided to evade toward when
    # the projectile was detected (None if not applicable)
    "evade_angle_deg",
    "result",
    "frame_result",
    "time_to_result_frames",
]


class DataLogger:
    """Basit CSV logger: her atış için özellikleri ve sonucu kaydeder.

    Dosya: data/training_shots.csv (append mode). Eğer klasör yoksa oluşturur.
    Her oyun açılışı ayrı bir `session_id` alır, böylece oturumlar ayırt edilebilir.
    """

    def __init__(self, filepath: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = filepath or os.path.join(data_dir, "training_shots.csv")
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._ensure_header()

    def _ensure_header(self):
        """Create file with header if missing; migrate files with an older header."""
        if not os.path.exists(self.filepath):
            self.reset_dataset()
            return
        with open(self.filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames == HEADER:
                return
            rows = list(reader)
        # older format: rewrite with the current header, keeping the data
        with open(self.filepath, "w", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HEADER, extrasaction='ignore')
            writer.writeheader()
            for r in rows:
                r = {k: v for k, v in r.items() if k is not None}
                r.setdefault("session_id", "legacy")
                writer.writerow(r)

    def reset_dataset(self):
        """Overwrite CSV with header only (clear previous data)."""
        with open(self.filepath, "w", newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(HEADER)

    def append_shot(self, row: dict):
        """Append a shot row to CSV. `row` must contain keys matching header."""
        row = dict(row)
        row["session_id"] = self.session_id
        row["manual_aim_mode"] = int(bool(row.get("manual_aim_mode")))
        with open(self.filepath, "a", newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HEADER, extrasaction='ignore')
            writer.writerow(row)

    def finalize_and_write(self, shot_info: dict, result: str, frame_result: int):
        """Complete shot_info with result/time and write to CSV."""
        shot_info = dict(shot_info)  # copy
        shot_info["result"] = result
        shot_info["frame_result"] = frame_result
        shot_info["time_to_result_frames"] = frame_result - shot_info.get("frame_shot", frame_result)
        self.append_shot(shot_info)
        return shot_info
