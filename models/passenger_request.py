from dataclasses import dataclass
from models.enums import PassengerType

@dataclass
class PassengerRequest:
    """Yêu cầu spawn một hành khách trong scenario."""
    id: int
    spawn_floor: int
    destination: int
    spawn_time: float
    spawn_side: str = "LEFT"
    passenger_type: PassengerType = PassengerType.NORMAL
    status: str = "PENDING"
    walking_progress: float = 0.0
