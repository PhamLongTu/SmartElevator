"""The :class:`Request` entity.

A request models a *hall call* -- the abstract "someone at floor X wants to go
to floor Y" demand signal -- decoupled from the passenger's identity and live
status. This mirrors how real elevator controllers treat hall calls separately
from car occupants and keeps call-handling logic independent of passenger
bookkeeping.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction


@dataclass
class Request:
    """A call for elevator service from ``origin`` to ``destination``.

    Attributes:
        id: Unique identifier for the request.
        origin: Floor the call originates from.
        destination: Floor the caller wants to reach.
        request_tick: Simulation tick the request was made.
        served: Whether the request has been fully satisfied.
        direction: Cached travel direction, derived from origin/destination.
    """

    id: int
    origin: int
    destination: int
    request_time: float = 0.0
    served: bool = False
    direction: Direction = field(init=False)

    def __post_init__(self) -> None:
        if self.origin == self.destination:
            raise ValueError(
                f"Request {self.id}: origin and destination must differ "
                f"(both were {self.origin})."
            )
        self.direction = Direction.between(self.origin, self.destination)

    def direction_of(self) -> Direction:
        """Return the travel direction implied by this request."""
        return self.direction

    def mark_served(self, time: float) -> None:
        """Mark the request as served."""
        self.served = True
