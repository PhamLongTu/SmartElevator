"""Thực thể :class:`Building` (Tòa nhà).

Tòa nhà nắm giữ thế giới thực tại: các hàng đợi hành khách đang chờ theo từng tầng và một 
thang máy duy nhất. Nó là cầu nối từ thế giới thời gian thực có thể thay đổi sang 
:class:`State` (Trạng thái) tìm kiếm bất biến thông qua :meth:`Building.to_state`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.elevator import Elevator
from models.passenger import Passenger
from models.state import State
from utils.settings import NUM_FLOORS


@dataclass
class Building:
    """Một tòa nhà nhiều tầng chứa một thang máy và các hành khách đang chờ.

    Thuộc tính:
        num_floors: Tổng số tầng.
        elevator: Cabin thang máy duy nhất.
        waiting: Ánh xạ chỉ số tầng -> danh sách các hành khách đang chờ ở đó.
    """

    num_floors: int = NUM_FLOORS
    elevator: Elevator = field(default_factory=Elevator)
    waiting: dict[int, list[Passenger]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Đảm bảo mọi tầng đều có một hàng đợi chờ (có thể trống).
        for floor in range(self.num_floors):
            self.waiting.setdefault(floor, [])
        # Giữ giới hạn của thang máy đồng bộ với chiều cao tòa nhà.
        self.elevator.num_floors = self.num_floors

    def add_passenger(self, passenger: Passenger) -> None:
        """Đăng ký một hành khách vào hàng đợi chờ tại tầng xuất phát của họ."""
        if not 0 <= passenger.origin_floor < self.num_floors:
            raise ValueError(
                f"Passenger {passenger.id} origin {passenger.origin_floor} "
                f"out of bounds [0, {self.num_floors - 1}]."
            )
        self.waiting[passenger.origin_floor].append(passenger)

    def waiting_at(self, floor: int) -> list[Passenger]:
        """Trả về danh sách hành khách đang chờ tại ``floor`` (tầng)."""
        return self.waiting[floor]

    def remove_waiting(self, floor: int, passenger: Passenger) -> None:
        """Xóa một hành khách cụ thể khỏi hàng đợi chờ của một tầng (khi họ lên thang)."""
        self.waiting[floor].remove(passenger)

    def all_served(self) -> bool:
        """Kiểm tra xem tất cả hành khách đã được phục vụ chưa (điều kiện kết thúc)."""
        if self.elevator.onboard:
            return False
        return self.num_waiting() == 0

    def num_waiting(self) -> int:
        """Tổng số hành khách hiện đang chờ trên tất cả các tầng."""
        return sum(len(queue) for queue in self.waiting.values())

    def update_time(self, dt: float) -> None:
        """Cập nhật bộ đếm thời gian cho tất cả hành khách trong tòa nhà và thang máy."""
        # Cập nhật hành khách đang chờ
        for queue in self.waiting.values():
            for p in queue:
                p.update_time(dt)
        
        # Cập nhật hành khách đang ở trong thang máy
        for p in self.elevator.onboard:
            p.update_time(dt)

    def to_state(self, current_time: float, score: int = 0) -> State:
        """Tạo một bản chụp :class:`State` bất biến chuẩn để lập kế hoạch."""
        # Đang ở trong thang: (đích, loại, thời gian sinh)
        onboard = tuple(
            (p.dest_floor, p.passenger_type, p.spawn_time)
            for p in self.elevator.onboard
        )
        # Đang chờ: tầng -> bộ (đích, loại, thời gian sinh)
        waiting_by_floor = tuple(
            tuple((p.dest_floor, p.passenger_type, p.spawn_time) for p in self.waiting[f])
            for f in range(self.num_floors)
        )
        
        return State.create(
            current_time=current_time,
            elevator_floor=self.elevator.current_floor,
            onboard=onboard,
            waiting_by_floor=waiting_by_floor,
            score=score
            # Lưu ý: các chỉ số delivered/angry/left thường được quản lý bởi engine/stats,
            # nhưng việc lập kế hoạch AI thường bắt đầu từ counts=0 hoặc các chỉ số hiện tại đã biết.
        )
