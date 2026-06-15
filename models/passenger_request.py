from dataclasses import dataclass
from models.enums import PassengerType

@dataclass
class PassengerRequest:
    """Represents a request for a passenger to be spawned in the scenario."""
    id: int
    spawn_floor: int
    destination: int
    spawn_time: float
    spawn_side: str = "LEFT"
    passenger_type: PassengerType = PassengerType.NORMAL
    status: str = "PENDING"
    walking_progress: float = 0.0
