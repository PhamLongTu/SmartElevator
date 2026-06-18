"""Thực thể :class:`Passenger` trong mô phỏng."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import Direction, PassengerStatus, PassengerType


@dataclass
class Passenger:
    """Một hành khách đi từ ``origin_floor`` đến ``dest_floor``."""

    id: int
    origin_floor: int
    dest_floor: int
    spawn_time: float = 0.0
    spawn_side: str = "LEFT"
    passenger_type: PassengerType = PassengerType.NORMAL
    status: PassengerStatus = PassengerStatus.WAITING
    pickup_time: float | None = None
    arrival_time: float | None = None
    destination_known: bool = False

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
        """Thời gian tối đa trước khi hành khách rời đi hoặc tức giận."""
        return 30.0 if self.passenger_type == PassengerType.NORMAL else 16.0

    @property
    def known_dest_floor(self) -> int:
        """Trả về tầng đích nếu đã biết, ngược lại là -1."""
        return self.dest_floor if self.destination_known else -1

    @property
    def reward(self) -> int:
        """Điểm thưởng cơ bản khi đưa khách tới nơi."""
        return 100 if self.passenger_type == PassengerType.NORMAL else 200

    @property
    def remaining_time(self) -> float:
        """Thời gian còn lại trước deadline."""
        return max(0.0, self.max_wait_time - (self.current_wait_time + self.ride_time))

    @property
    def is_expired(self) -> bool:
        """Cho biết hành khách đã quá deadline hay chưa."""
        return (self.current_wait_time + self.ride_time) >= self.max_wait_time

    @property
    def direction(self) -> Direction:
        """Hướng hành khách cần di chuyển."""
        return Direction.between(self.origin_floor, self.dest_floor)

    def board(self, time: float) -> None:
        """Đánh dấu hành khách đã vào thang tại thời điểm mô phỏng cho trước."""
        if self.status != PassengerStatus.WAITING:
            return
        self.status = PassengerStatus.ONBOARD
        self.pickup_time = time
        self.destination_known = True

    def alight(self, time: float) -> None:
        """Đánh dấu hành khách đã tới nơi tại thời điểm mô phỏng cho trước."""
        if self.status not in (PassengerStatus.ONBOARD, PassengerStatus.ANGRY):
            return
        self.status = PassengerStatus.DELIVERED
        self.arrival_time = time

    def update_time(self, dt: float) -> None:
        """Cập nhật bộ đếm thời gian và trạng thái deadline của hành khách."""
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
        """Tổng thời gian trong hệ thống, gồm chờ và đi thang."""
        return self.current_wait_time + self.ride_time
