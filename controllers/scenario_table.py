from typing import List
import random
from controllers.scenario_row import ScenarioRow
from models.enums import PassengerType
from utils.settings import NUM_FLOORS

class ScenarioTable:
    """Manages the 15-passenger configuration data."""
    def __init__(self):
        self.rows: List[ScenarioRow] = [ScenarioRow(i + 1) for i in range(15)]
        self.reset()

    def reset(self):
        for i, row in enumerate(self.rows):
            row.spawn_floor = 0
            row.spawn_side = "LEFT" if i % 2 == 0 else "RIGHT"
            row.destination = (i % 6) + 1
            row.spawn_time = i * 2 # Spread out every 2 seconds
            row.passenger_type = PassengerType.NORMAL
            row.is_valid = True
            row.error_message = ""

    def randomize(self, preset: str = "Medium"):
        # Presets: Easy, Medium, Hard, Stress Test
        max_time = 30
        urgent_prob = 0.2
        
        if preset == "Easy":
            max_time = 100
            urgent_prob = 0.1
        elif preset == "Hard":
            max_time = 40
            urgent_prob = 0.4
        elif preset == "Stress Test":
            max_time = 15
            urgent_prob = 0.6

        for i, row in enumerate(self.rows):
            row.spawn_floor = random.randint(0, NUM_FLOORS - 1)
            row.destination = random.randint(0, NUM_FLOORS - 1)
            while row.destination == row.spawn_floor:
                row.destination = random.randint(0, NUM_FLOORS - 1)
            
            row.spawn_side = random.choice(["LEFT", "RIGHT"])
            # Ensure at least one passenger has spawn_time = 0
            if i == 0:
                row.spawn_time = 0
            else:
                row.spawn_time = random.randint(0, max_time)
            row.passenger_type = PassengerType.URGENT if random.random() < urgent_prob else PassengerType.NORMAL

    def get_requests(self) -> List:
        return [row.to_request() for row in self.rows]

    def export_data(self) -> List[dict]:
        """Returns a list of dicts representing the rows."""
        return [{
            "spawn_floor": r.spawn_floor,
            "spawn_side": r.spawn_side,
            "destination": r.destination,
            "spawn_time": r.spawn_time,
            "passenger_type": r.passenger_type
        } for r in self.rows]

    def import_data(self, data: List[dict]):
        """Restores row state from a list of dicts."""
        if not data or len(data) != len(self.rows):
            return
        for i, d in enumerate(data):
            self.rows[i].spawn_floor = d["spawn_floor"]
            self.rows[i].spawn_side = d["spawn_side"]
            self.rows[i].destination = d["destination"]
            self.rows[i].spawn_time = d["spawn_time"]
            self.rows[i].passenger_type = d["passenger_type"]
