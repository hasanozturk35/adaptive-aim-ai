import csv
import os
from typing import Optional


class DataLogger:
    """Basit CSV logger: her atış için özellikleri ve sonucu kaydeder.

    Dosya: data/training_shots.csv (append mode). Eğer klasör yoksa oluşturur.
    """

    def __init__(self, filepath: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.filepath = filepath or os.path.join(data_dir, "training_shots.csv")
        self._ensure_header()

    def _ensure_header(self):
        """Create file with header if missing."""
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                header = [
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
                writer.writerow(header)

    def reset_dataset(self):
        """Overwrite CSV with header only (clear previous data)."""
        with open(self.filepath, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = [
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
                "evade_angle_deg",
                "result",
                "frame_result",
                "time_to_result_frames",
            ]
            writer.writerow(header)

    def append_shot(self, row: dict):
        """Append a shot row to CSV. `row` must contain keys matching header."""
        with open(self.filepath, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                row.get("shot_id"),
                row.get("frame_shot"),
                row.get("player_x"),
                row.get("player_y"),
                row.get("aim_x"),
                row.get("aim_y"),
                row.get("aim_dx"),
                row.get("aim_dy"),
                row.get("aim_angle_deg"),
                row.get("aim_distance"),
                row.get("target_x_at_shot"),
                row.get("target_y_at_shot"),
                row.get("target_speed"),
                row.get("target_difficulty"),
                row.get("target_strategy_state"),
                int(bool(row.get("manual_aim_mode"))),
                row.get("predicted_hit_prob"),
                row.get("evade_angle_deg"),
                row.get("result"),
                row.get("frame_result"),
                row.get("time_to_result_frames"),
            ])

    def finalize_and_write(self, shot_info: dict, result: str, frame_result: int):
        """Complete shot_info with result/time and write to CSV."""
        shot_info = dict(shot_info)  # copy
        shot_info["result"] = result
        shot_info["frame_result"] = frame_result
        shot_info["time_to_result_frames"] = frame_result - shot_info.get("frame_shot", frame_result)
        self.append_shot(shot_info)
        return shot_info
