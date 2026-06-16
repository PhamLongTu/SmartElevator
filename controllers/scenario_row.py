from models.passenger_request import PassengerRequest
from models.enums import PassengerType

class ScenarioRow:
    """State for one row in the scenario configuration table."""
    def __init__(self, passenger_id: int):
        self.id = passenger_id
        self.spawn_floor = 0
        self.spawn_side = "LEFT"
        self.destination = 1
        self.spawn_time = 0
        self.passenger_type = PassengerType.NORMAL
        self.enabled = True  # Checkbox: có xuất hiện trong lượt chơi hay không
        self.is_valid = True
        self.error_message = ""

    def to_request(self) -> PassengerRequest:
        return PassengerRequest(
            id=self.id,
            spawn_floor=self.spawn_floor,
            spawn_side=self.spawn_side,
            destination=self.destination,
            spawn_time=float(self.spawn_time),
            passenger_type=self.passenger_type
        )
