"""Bộ gom thống kê cho một lượt chạy.

Lớp này lưu cả chỉ số tìm kiếm (expanded/generated/runtime/plan cost) và chỉ số
vận hành (quãng đường, thời gian chờ, giao khách, hài lòng).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from time import perf_counter
from typing import ClassVar

from models.passenger import Passenger


@dataclass
class StatisticsManager:
    """Cộng dồn các chỉ số của một lượt chơi hoặc một lượt benchmark."""

    nodes_expanded: int = 0
    nodes_generated: int = 0
    planning_time: float = 0.0
    solution_cost: float = 0.0

    total_distance: int = 0
    total_wait: float = 0.0
    total_journey: float = 0.0
    delivered_count: int = 0
    urgent_delivered_count: int = 0
    left_count: int = 0
    angry_count: int = 0
    _satisfaction_sum: float = 0.0

    satisfaction_tau: float = 10.0

    _timer_start: float | None = field(default=None, repr=False)

    def record_expansion(self) -> None:
        """Ghi nhận một node được mở rộng."""
        self.nodes_expanded += 1

    def record_generation(self, count: int = 1) -> None:
        """Ghi nhận số node con được sinh ra."""
        self.nodes_generated += count

    def start_timer(self) -> None:
        """Bắt đầu đo thời gian planning."""
        self._timer_start = perf_counter()

    def stop_timer(self) -> None:
        """Dừng đo và cộng thời gian planning."""
        if self._timer_start is not None:
            self.planning_time += (perf_counter() - self._timer_start) * 1000.0
            self._timer_start = None

    def record_move(self, floors: int = 1) -> None:
        """Ghi nhận số tầng thang đã di chuyển."""
        self.total_distance += floors

    def record_pickup(self, passenger: Passenger) -> None:
        """Ghi nhận thời gian chờ khi khách lên thang."""
        self.total_wait += passenger.current_wait_time

    def record_delivery(self, passenger: Passenger) -> None:
        """Ghi nhận thời gian trong hệ thống và mức hài lòng khi giao khách."""
        from models.enums import PassengerType
        journey = passenger.total_system_time()
        self.total_journey += journey
        self._satisfaction_sum += math.exp(-journey / self.satisfaction_tau)
        self.delivered_count += 1
        
        if passenger.passenger_type == PassengerType.URGENT:
            self.urgent_delivered_count += 1
        if passenger.is_expired:
            self.angry_count += 1

    def record_failure(self, passenger: Passenger) -> None:
        """Ghi nhận khách rời hệ thống trước khi được phục vụ."""
        from models.enums import PassengerStatus
        if passenger.status == PassengerStatus.LEFT:
            self.left_count += 1

    @property
    def average_waiting_time(self) -> float:
        """Thời gian chờ trung bình."""
        denom = self.delivered_count + self.left_count
        return self.total_wait / denom if denom else 0.0

    @property
    def average_journey_time(self) -> float:
        """Thời gian hành trình trung bình của khách đã giao."""
        return self.total_journey / self.delivered_count if self.delivered_count else 0.0

    @property
    def satisfaction_score(self) -> float:
        """Mức hài lòng trung bình trong khoảng 0..1."""
        return self._satisfaction_sum / self.delivered_count if self.delivered_count else 0.0

    def summary(self) -> dict[str, float]:
        """Trả về các chỉ số ở dạng dict phẳng."""
        return {
            "nodes_expanded": self.nodes_expanded,
            "nodes_generated": self.nodes_generated,
            "planning_time_ms": round(self.planning_time, 3),
            "solution_cost": self.solution_cost,
            "total_distance": self.total_distance,
            "average_waiting_time": round(self.average_waiting_time, 3),
            "average_journey_time": round(self.average_journey_time, 3),
            "satisfaction_score": round(self.satisfaction_score, 4),
            "delivered_count": self.delivered_count,
            "urgent_delivered": self.urgent_delivered_count,
            "left_count": self.left_count,
            "angry_count": self.angry_count,
        }

    def report(self, title: str = "Statistics Report") -> str:
        """Trả về báo cáo dạng văn bản."""
        lines = [
            f"=== {title} ===",
            "-- Search quality (planning) --",
            f"  Runtime           : {self.planning_time:.3f} ms",
            f"  Expanded nodes    : {self.nodes_expanded}",
            f"  Generated nodes   : {self.nodes_generated}",
            f"  Plan cost total   : {self.solution_cost:.1f}",
            "-- Outcome (execution) --",
            f"  Travel distance   : {self.total_distance} floors",
            f"  Avg waiting time  : {self.average_waiting_time:.2f} units",
            f"  Avg journey time  : {self.average_journey_time:.2f} units",
            f"  Satisfaction      : {self.satisfaction_score * 100:.1f}%",
            f"  Delivered         : {self.delivered_count} (Urgent: {self.urgent_delivered_count})",
            f"  Failures          : {self.left_count} Left, {self.angry_count} Angry",
        ]
        return "\n".join(lines)

    ROW_HEADERS: ClassVar[tuple[str, ...]] = (
        "Label",
        "Runtime(ms)",
        "Expanded",
        "Cost",
        "Distance",
        "AvgWait",
        "UrgDeliv",
        "Fail(L/A)",
    )

    def as_row(self, label: str = "") -> tuple[str, ...]:
        """Trả về một dòng thống kê theo ``ROW_HEADERS``."""
        return (
            label,
            f"{self.planning_time:.2f}",
            str(self.nodes_expanded),
            f"{self.solution_cost:.1f}",
            str(self.total_distance),
            f"{self.average_waiting_time:.2f}",
            str(self.urgent_delivered_count),
            f"{self.left_count}/{self.angry_count}",
        )

    @classmethod
    def comparison_table(
        cls, rows: dict[str, "StatisticsManager"]
    ) -> str:
        """Tạo bảng văn bản để so sánh nhiều lượt chạy."""
        table_rows = [cls.ROW_HEADERS]
        table_rows.extend(stats.as_row(label) for label, stats in rows.items())

        widths = [
            max(len(row[i]) for row in table_rows)
            for i in range(len(cls.ROW_HEADERS))
        ]
        sep = "-+-".join("-" * w for w in widths)

        def fmt(row: tuple[str, ...]) -> str:
            return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

        out = [fmt(table_rows[0]), sep]
        out.extend(fmt(row) for row in table_rows[1:])
        return "\n".join(out)

    def reset(self) -> None:
        """Xóa toàn bộ chỉ số để bắt đầu lượt mới."""
        self.nodes_expanded = 0
        self.nodes_generated = 0
        self.planning_time = 0.0
        self.solution_cost = 0.0
        self.total_distance = 0
        self.total_wait = 0.0
        self.total_journey = 0.0
        self.delivered_count = 0
        self.urgent_delivered_count = 0
        self.left_count = 0
        self.angry_count = 0
        self._satisfaction_sum = 0.0
        self._timer_start = None
