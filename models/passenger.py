"""The :class:`Passenger` entity.

A passenger is a mutable runtime entity that tracks one rider's identity and
personal timeline (waiting, in-vehicle, delivered). It is the source of truth
for per-passenger metrics such as waiting time and journey time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction, PassengerStatus, PassengerType


@dataclass
class Passenger:
    """One individual rider travelling from ``origin_floor`` to ``dest_floor``.

    In Version 2, passengers have deadlines based on their type. If delivered
    within the limit, a reward is earned. Otherwise, they become ANGRY or leave
    the floor entirely (status LEFT).

    Attributes:
        id: Unique identifier for the passenger.
        origin_floor: Floor where the passenger starts and waits.
        dest_floor: Floor the passenger wants to reach.
        spawn_time: Simulation time at which the passenger appeared.
        spawn_side: Which side of the floor the passenger spawned on (LEFT/RIGHT).
        passenger_type: Normal or Urgent, determining reward and deadline.
        status: Lifecycle status (WAITING, ONBOARD, DELIVERED, LEFT, ANGRY).
        pickup_time: Time the passenger boarded the elevator, or ``None``.
        arrival_time: Time the passenger was delivered, or ``None``.
        current_wait_time: Accumulated time spent waiting at the floor.
        ride_time: Accumulated time spent inside the elevator cab.
    """

    id: int
    origin_floor: int
    dest_floor: int
    spawn_time: float = 0.0
    spawn_side: str = "LEFT"
    passenger_type: PassengerType = PassengerType.NORMAL
    status: PassengerStatus = PassengerStatus.WAITING
    pickup_time: float | None = None
    arrival_time: float | None = None

    # Trackers for real-time accumulation
    current_wait_time: float = 0.0
    ride_time: float = 0.0

    def __post_init__(self) -> None:
        if self.origin_floor == self.dest_floor:
            raise ValueError(
                f"Passenger {self.id}: origin and destination must differ "
                f"(both were {self.origin_floor})."
            )

    @property
    def max_wait_time(self) -> float:
        """The total time budget allowed before the passenger is lost/angry."""
        return 30.0 if self.passenger_type == PassengerType.NORMAL else 16.0

    @property
    def reward(self) -> int:
        """Base reward for successful delivery."""
        return 100 if self.passenger_type == PassengerType.NORMAL else 200

    @property
    def remaining_time(self) -> float:
        """Remaining time before the deadline expires."""
        return max(0.0, self.max_wait_time - (self.current_wait_time + self.ride_time))

    @property
    def is_expired(self) -> bool:
        """Whether the passenger's deadline has been exceeded."""
        return (self.current_wait_time + self.ride_time) >= self.max_wait_time

    @property
    def direction(self) -> Direction:
        """Direction the passenger needs to travel."""
        return Direction.between(self.origin_floor, self.dest_floor)

    def board(self, time: float) -> None:
        """Mark the passenger as boarded at the given simulation time."""
        if self.status != PassengerStatus.WAITING:
            return
        self.status = PassengerStatus.ONBOARD
        self.pickup_time = time

    def alight(self, time: float) -> None:
        """Mark the passenger as delivered at the given simulation time."""
        if self.status not in (PassengerStatus.ONBOARD, PassengerStatus.ANGRY):
            return
        self.status = PassengerStatus.DELIVERED
        self.arrival_time = time

    def update_time(self, dt: float) -> None:
        """Advance the passenger's internal timers and update status if expired."""
        if self.status == PassengerStatus.WAITING:
            self.current_wait_time += dt
            if self.is_expired:
                self.status = PassengerStatus.LEFT
        elif self.status == PassengerStatus.ONBOARD:
            self.ride_time += dt
            if self.is_expired:
                self.status = PassengerStatus.ANGRY
        elif self.status == PassengerStatus.ANGRY:
            self.ride_time += dt

    def total_system_time(self) -> float:
        """Total time spent in the system (waiting + riding)."""
        return self.current_wait_time + self.ride_time
