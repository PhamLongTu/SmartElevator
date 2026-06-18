"""Các enum dùng chung trong mô hình Smart Elevator."""

from __future__ import annotations

from enum import Enum, auto


class Direction(Enum):
    """Hướng di chuyển của thang hoặc hành khách."""

    UP = 1
    DOWN = -1
    IDLE = 0

    @classmethod
    def between(cls, origin: int, destination: int) -> "Direction":
        """Trả về hướng cần đi từ ``origin`` đến ``destination``."""
        if destination > origin:
            return cls.UP
        if destination < origin:
            return cls.DOWN
        return cls.IDLE


class ElevatorAction(Enum):
    """Các hành động cơ bản của thang trong một bước mô phỏng."""

    MOVE_UP = auto()
    MOVE_DOWN = auto()
    STOP = auto()
    IDLE = auto()


class GameMode(Enum):
    """Các chế độ chơi của game."""

    MANUAL = auto()
    AI = auto()
    COMPARE = auto()


class PassengerType(Enum):
    """Loại hành khách, dùng để xác định thưởng và deadline."""

    NORMAL = auto()
    URGENT = auto()


class PassengerStatus(Enum):
    """Trạng thái vòng đời của hành khách."""

    WAITING = auto()
    ONBOARD = auto()
    DELIVERED = auto()
    LEFT = auto()
    ANGRY = auto()
