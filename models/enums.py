"""Enumerations shared across the Smart Elevator domain model.

Keeping these in one place avoids circular imports between the model
entities and lets the simulation, algorithms, and views reference a single
canonical set of states and actions.
"""

from __future__ import annotations

from enum import Enum, auto


class Direction(Enum):
    """Direction of elevator motion or a passenger's required travel."""

    UP = 1
    DOWN = -1
    IDLE = 0

    @classmethod
    def between(cls, origin: int, destination: int) -> "Direction":
        """Return the direction required to travel from ``origin`` to ``destination``."""
        if destination > origin:
            return cls.UP
        if destination < origin:
            return cls.DOWN
        return cls.IDLE


class ElevatorAction(Enum):
    """The atomic actions the elevator can take in one simulation step.

    ``STOP`` is a combined *serve* action: passengers whose destination is the
    current floor alight, then waiting passengers board up to capacity.
    """

    MOVE_UP = auto()
    MOVE_DOWN = auto()
    STOP = auto()
    IDLE = auto()


class GameMode(Enum):
    """The three ways the game can be played."""

    MANUAL = auto()
    AI = auto()
    COMPARE = auto()


class PassengerStatus(Enum):
    """Lifecycle status of a passenger."""

    WAITING = auto()
    ONBOARD = auto()
    DELIVERED = auto()
