import json
from typing import List
from controllers.scenario_row import ScenarioRow
from models.enums import PassengerType

class ScenarioSerializer:
    """Handles Export/Import of scenarios to/from JSON."""
    @staticmethod
    def export_json(rows: List[ScenarioRow]) -> str:
        data = []
        for row in rows:
            data.append({
                "id": row.id,
                "spawn_floor": "G" if row.spawn_floor == 0 else f"F{row.spawn_floor}",
                "spawn_side": row.spawn_side,
                "destination": "G" if row.destination == 0 else f"F{row.destination}",
                "spawn_time": row.spawn_time,
                "passenger_type": row.passenger_type.name,
                "enabled": row.enabled
            })
        return json.dumps(data, indent=2)

    @staticmethod
    def import_json(rows: List[ScenarioRow], json_str: str) -> bool:
        try:
            data = json.loads(json_str)
            for i, p_data in enumerate(data):
                if i >= len(rows): break
                row = rows[i]
                
                # Parse floor strings like "G", "F1", "F2"
                row.spawn_floor = ScenarioSerializer._parse_floor(p_data["spawn_floor"])
                row.spawn_side = p_data["spawn_side"]
                row.destination = ScenarioSerializer._parse_floor(p_data["destination"])
                row.spawn_time = p_data["spawn_time"]
                row.passenger_type = PassengerType[p_data["passenger_type"]]
                row.enabled = p_data.get("enabled", True)  # Tương thích ngược
            return True
        except:
            return False

    @staticmethod
    def _parse_floor(floor_str: str) -> int:
        if floor_str == "G": return 0
        return int(floor_str[1:])
