"""Thực thể :class:`Elevator` trong mô phỏng."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction
from models.passenger import Passenger
from utils.settings import ELEVATOR_CAPACITY, GROUND_FLOOR, NUM_FLOORS


@dataclass
class Elevator:
    """Cabin thang máy duy nhất trong tòa nhà."""

    current_floor: int = GROUND_FLOOR
    direction: Direction = Direction.IDLE
    capacity: int = ELEVATOR_CAPACITY
    onboard: list[Passenger] = field(default_factory=list)
    num_floors: int = NUM_FLOORS

    @property
    def occupancy(self) -> int:
        """Số hành khách đang ở trong thang."""
        return len(self.onboard)

    def is_full(self) -> bool:
        """Cho biết thang đã đầy hay chưa."""
        return self.occupancy >= self.capacity

    def can_board(self) -> bool:
        """Cho biết thang còn chỗ cho ít nhất một khách nữa hay không."""
        return self.occupancy < self.capacity

    def move(self, direction: Direction) -> None:
        """Di chuyển thang một tầng theo ``direction`` và giữ trong giới hạn tòa nhà."""
        target = self.current_floor + direction.value
        if not 0 <= target < self.num_floors:
            raise ValueError(
                f"Cannot move {direction.name} from floor {self.current_floor}: "
                f"target {target} is out of bounds [0, {self.num_floors - 1}]."
            )
        self.current_floor = target
        self.direction = direction

    def board(self, passenger: Passenger, tick: int) -> bool:
        """Cho một hành khách vào thang nếu còn sức chứa."""
        if not self.can_board():
            return False
        passenger.board(tick)
        self.onboard.append(passenger)
        return True

    def alight(self, floor: int, tick: int) -> list[Passenger]:
        """Cho các hành khách có đích là ``floor`` rời thang."""
        leaving = [p for p in self.onboard if p.dest_floor == floor]
        if leaving:
            self.onboard = [p for p in self.onboard if p.dest_floor != floor]
            for passenger in leaving:
                passenger.alight(tick)
        return leaving
