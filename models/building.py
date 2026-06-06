"""The :class:`Building` entity.

The building holds the live world: the per-floor waiting queues and the single
elevator. It is the bridge from the mutable runtime world to the immutable
search :class:`State` via :meth:`Building.to_state`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.elevator import Elevator
from models.passenger import Passenger
from models.state import State
from utils.settings import NUM_FLOORS


@dataclass
class Building:
    """A multi-floor building containing one elevator and waiting passengers.

    Attributes:
        num_floors: Total number of floors.
        elevator: The single elevator cab.
        waiting: Mapping of floor index -> list of passengers waiting there.
    """

    num_floors: int = NUM_FLOORS
    elevator: Elevator = field(default_factory=Elevator)
    waiting: dict[int, list[Passenger]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure every floor has a (possibly empty) waiting queue.
        for floor in range(self.num_floors):
            self.waiting.setdefault(floor, [])

    def add_passenger(self, passenger: Passenger) -> None:
        """Register a passenger into the waiting queue at their origin floor."""
        if not 0 <= passenger.origin_floor < self.num_floors:
            raise ValueError(
                f"Passenger {passenger.id} origin {passenger.origin_floor} "
                f"out of bounds [0, {self.num_floors - 1}]."
            )
        self.waiting[passenger.origin_floor].append(passenger)

    def waiting_at(self, floor: int) -> list[Passenger]:
        """Return the list of passengers waiting at ``floor``."""
        return self.waiting[floor]

    def remove_waiting(self, floor: int, passenger: Passenger) -> None:
        """Remove a specific passenger from a floor's waiting queue (on boarding)."""
        self.waiting[floor].remove(passenger)

    def all_served(self) -> bool:
        """Whether no passengers remain waiting or onboard (goal condition)."""
        if self.elevator.onboard:
            return False
        return all(len(queue) == 0 for queue in self.waiting.values())

    def to_state(self) -> State:
        """Produce a canonical immutable :class:`State` snapshot for planning."""
        onboard_dests = tuple(p.dest_floor for p in self.elevator.onboard)
        waiting_by_floor = tuple(
            tuple(p.dest_floor for p in self.waiting[floor])
            for floor in range(self.num_floors)
        )
        return State.create(
            elevator_floor=self.elevator.current_floor,
            onboard_dests=onboard_dests,
            waiting_by_floor=waiting_by_floor,
        )
