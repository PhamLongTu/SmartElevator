"""Lớp nền cho các thuật toán tìm kiếm.

File này định nghĩa kết quả tìm kiếm, hợp đồng chung của thuật toán và hàm
``solve`` để đo thời gian, gắn tên thuật toán và cộng dồn thống kê.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter

from models.enums import ElevatorAction
from models.state import State
from statistics.statistics_manager import StatisticsManager


@dataclass
class SearchResult:
    """Kết quả của một lần tìm kiếm."""

    path: list[ElevatorAction] = field(default_factory=list)
    cost: float = 0.0
    success: bool = False
    nodes_expanded: int = 0
    nodes_generated: int = 0
    planning_time_ms: float = 0.0
    algorithm: str = ""

    @property
    def plan_length(self) -> int:
        """Số hành động trong kế hoạch."""
        return len(self.path)


class SearchAlgorithm(ABC):
    """Lớp cha cho mọi thuật toán tìm kiếm của thang máy."""

    name: str = "Search"

    def solve(
        self,
        initial_state: State,
        stats: StatisticsManager | None = None,
        node_limit: int = 10000,
        time_limit: float = 1.5,
    ) -> SearchResult:
        """Tìm kế hoạch từ trạng thái ban đầu và trả về kết quả kèm thống kê."""
        self._node_limit = node_limit
        self._time_limit = time_limit
        self._start_time = perf_counter()

        result = self._search(initial_state)
        result.planning_time_ms = (perf_counter() - self._start_time) * 1000.0
        result.algorithm = self.name

        if stats is not None:
            stats.nodes_expanded += result.nodes_expanded
            stats.nodes_generated += result.nodes_generated
            stats.planning_time += result.planning_time_ms
            stats.solution_cost += result.cost

        return result

    def _check_budget(self, expanded: int) -> bool:
        """Kiểm tra giới hạn node hoặc thời gian."""
        if expanded <= 0:
            return False
        if expanded >= self._node_limit:
            return True
        if (perf_counter() - self._start_time) >= self._time_limit:
            return True
        return False

    @abstractmethod
    def _search(self, initial_state: State) -> SearchResult:
        """Phần tìm kiếm lõi do từng thuật toán triển khai."""
        raise NotImplementedError
