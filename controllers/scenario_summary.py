from typing import Dict, List
from controllers.scenario_row import ScenarioRow
from models.enums import PassengerType


class ScenarioSummary:
    """Tính thống kê tóm tắt và độ khó của scenario."""

    @staticmethod
    def calculate(rows: List[ScenarioRow]) -> Dict:
        total = len(rows)
        normal = sum(1 for r in rows if r.passenger_type == PassengerType.NORMAL)
        urgent = sum(1 for r in rows if r.passenger_type == PassengerType.URGENT)
        avg_spawn_time = sum(r.spawn_time for r in rows) / total if total else 0
        avg_dist = sum(abs(r.destination - r.spawn_floor) for r in rows) / total if total else 0

        difficulty_score = (urgent * 2) + (avg_dist * 0.5) - (avg_spawn_time * 0.1)

        if difficulty_score < 10:
            difficulty = "Easy"
        elif difficulty_score < 20:
            difficulty = "Medium"
        elif difficulty_score < 30:
            difficulty = "Hard"
        else:
            difficulty = "Extreme"

        max_time = max(r.spawn_time for r in rows) if rows else 1
        density = total / max_time if max_time > 0 else total

        return {
            "total": total,
            "normal": normal,
            "urgent": urgent,
            "avg_spawn_time": avg_spawn_time,
            "avg_dist": avg_dist,
            "difficulty": difficulty,
            "density": density
        }
