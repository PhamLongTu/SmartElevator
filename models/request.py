"""Thực thể :class:`Request` đại diện cho một yêu cầu gọi thang."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction


@dataclass
class Request:
    """Yêu cầu phục vụ từ ``origin`` đến ``destination``."""

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
        """Trả về hướng di chuyển của request."""
        return self.direction

    def mark_served(self, time: float) -> None:
        """Đánh dấu request đã được phục vụ."""
        self.served = True
