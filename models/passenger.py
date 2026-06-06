"""The :class:`Passenger` entity.

A passenger is a mutable runtime entity that tracks one rider's identity and
personal timeline (waiting, in-vehicle, delivered). It is the source of truth
for per-passenger metrics such as waiting time and journey time.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.enums import Direction, PassengerStatus


@dataclass
class Passenger:
    """One individual rider travelling from ``origin_floor`` to ``dest_floor``.

    Attributes:
        id: Unique identifier for the passenger.
        origin_floor: Floor where the passenger starts and waits.
        dest_floor: Floor the passenger wants to reach.
        spawn_tick: Simulation tick at which the passenger appeared.
        status: Current lifecycle status (WAITING / ONBOARD / DELIVERED).
        pickup_tick: Tick the passenger boarded the elevator, or ``None``.
        arrival_tick: Tick the passenger was delivered, or ``None``.
    """

    id: int
    origin_floor: int
    dest_floor: int
    spawn_tick: int = 0
    status: PassengerStatus = PassengerStatus.WAITING
    pickup_tick: int | None = None
    arrival_tick: int | None = None

    def __post_init__(self) -> None:
        if self.origin_floor == self.dest_floor:
            raise ValueError(
                f"Passenger {self.id}: origin and destination must differ "
                f"(both were {self.origin_floor})."
            )

    @property
    def direction(self) -> Direction:
        """Direction the passenger needs to travel."""
        return Direction.between(self.origin_floor, self.dest_floor)

    def board(self, tick: int) -> None:
        """Mark the passenger as boarded at the given simulation tick."""
        self.status = PassengerStatus.ONBOARD
        self.pickup_tick = tick

    def alight(self, tick: int) -> None:
        """Mark the passenger as delivered at the given simulation tick."""
        self.status = PassengerStatus.DELIVERED
        self.arrival_tick = tick

    def waiting_time(self) -> int | None:
        """Ticks spent waiting before pickup, or ``None`` if not yet picked up."""
        if self.pickup_tick is None:
            return None
        return self.pickup_tick - self.spawn_tick

    def journey_time(self) -> int | None:
        """Total ticks in the system (spawn to delivery), or ``None`` if undelivered."""
        if self.arrival_tick is None:
            return None
        return self.arrival_tick - self.spawn_tick
