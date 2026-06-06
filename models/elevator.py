"""The :class:`Elevator` entity.

The elevator is a mutable runtime entity that owns its position, motion
direction, and the passengers currently aboard. It enforces the two hard
invariants of the building rules: floor bounds and the capacity limit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction
from models.passenger import Passenger
from utils.settings import ELEVATOR_CAPACITY, GROUND_FLOOR, NUM_FLOORS


@dataclass
class Elevator:
    """The single elevator cab.

    Attributes:
        current_floor: The floor the cab is currently at (0-indexed).
        direction: The current motion direction.
        capacity: Maximum simultaneous occupants.
        onboard: Passengers currently inside the cab.
    """

    current_floor: int = GROUND_FLOOR
    direction: Direction = Direction.IDLE
    capacity: int = ELEVATOR_CAPACITY
    onboard: list[Passenger] = field(default_factory=list)

    @property
    def occupancy(self) -> int:
        """Number of passengers currently aboard."""
        return len(self.onboard)

    def is_full(self) -> bool:
        """Whether the cab has reached capacity."""
        return self.occupancy >= self.capacity

    def can_board(self) -> bool:
        """Whether there is room for at least one more passenger."""
        return self.occupancy < self.capacity

    def move(self, direction: Direction) -> None:
        """Move the cab one floor in ``direction``, respecting building bounds.

        Raises:
            ValueError: If the move would leave the building.
        """
        target = self.current_floor + direction.value
        if not 0 <= target < NUM_FLOORS:
            raise ValueError(
                f"Cannot move {direction.name} from floor {self.current_floor}: "
                f"target {target} is out of bounds [0, {NUM_FLOORS - 1}]."
            )
        self.current_floor = target
        self.direction = direction

    def board(self, passenger: Passenger, tick: int) -> bool:
        """Board a single passenger if capacity allows.

        Returns:
            ``True`` if the passenger boarded, ``False`` if the cab was full.
        """
        if not self.can_board():
            return False
        passenger.board(tick)
        self.onboard.append(passenger)
        return True

    def alight(self, floor: int, tick: int) -> list[Passenger]:
        """Remove and return all passengers whose destination is ``floor``."""
        leaving = [p for p in self.onboard if p.dest_floor == floor]
        if leaving:
            self.onboard = [p for p in self.onboard if p.dest_floor != floor]
            for passenger in leaving:
                passenger.alight(tick)
        return leaving
