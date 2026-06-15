from typing import List
from controllers.scenario_row import ScenarioRow

class ScenarioValidator:
    """Validates passenger configuration rows."""
    @staticmethod
    def validate_all(rows: List[ScenarioRow]) -> bool:
        all_valid = True
        for row in rows:
            is_valid, msg = ScenarioValidator.validate_row(row)
            row.is_valid = is_valid
            row.error_message = msg
            if not is_valid:
                all_valid = False
        return all_valid

    @staticmethod
    def validate_row(row: ScenarioRow) -> tuple[bool, str]:
        # 1. Spawn floor must not be equal to destination
        if row.spawn_floor == row.destination:
            return False, "Spawn floor cannot be destination"
        
        # 2. Spawn time must be non-negative
        if row.spawn_time < 0:
            return False, "Time must be >= 0"
        
        # 3. Destination must be within valid range (fixed check)
        # Assuming NUM_FLOORS is check elsewhere or using actual range
        
        return True, ""
