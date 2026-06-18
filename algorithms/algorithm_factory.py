"""Factory chọn thuật toán tìm kiếm theo tên.

Registry ánh xạ khóa ngắn như ``"astar"`` tới lớp thuật toán và thông tin hiển
thị dùng trong menu chọn thuật toán.
"""

from __future__ import annotations

from dataclasses import dataclass

from algorithms.astar import AStar
from algorithms.base_search import SearchAlgorithm
from algorithms.beam_search import BeamSearch
from algorithms.bfs import BFS
from algorithms.dfs import DFS
from algorithms.greedy import GreedyBestFirst
from algorithms.hill_climbing import HillClimbing
from algorithms.ucs import UCS


@dataclass(frozen=True)
class AlgorithmInfo:
    """Thông tin hiển thị của một thuật toán có thể chọn."""

    key: str
    display_name: str
    category: str
    factory: type[SearchAlgorithm]


class AlgorithmFactory:
    """Tạo thuật toán theo tên và liệt kê thuật toán có sẵn."""

    REGISTRY: dict[str, AlgorithmInfo] = {
        "bfs": AlgorithmInfo("bfs", "Breadth-First Search", "Uninformed", BFS),
        "dfs": AlgorithmInfo("dfs", "Depth-First Search", "Uninformed", DFS),
        "ucs": AlgorithmInfo("ucs", "Uniform-Cost Search", "Uninformed", UCS),
        "greedy": AlgorithmInfo("greedy", "Greedy Best-First", "Informed", GreedyBestFirst),
        "astar": AlgorithmInfo("astar", "A* Search", "Informed", AStar),
        "hill": AlgorithmInfo("hill", "Hill Climbing", "Local", HillClimbing),
        "beam": AlgorithmInfo("beam", "Beam Search", "Local", BeamSearch),
    }

    @classmethod
    def create(cls, name: str, **kwargs) -> SearchAlgorithm:
        """Khởi tạo thuật toán theo khóa trong registry."""
        key = name.lower()
        try:
            info = cls.REGISTRY[key]
        except KeyError as exc:
            valid = ", ".join(cls.REGISTRY)
            raise KeyError(f"Unknown algorithm {name!r}. Valid: {valid}.") from exc
        return info.factory(**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """Trả về danh sách khóa thuật toán theo thứ tự hiển thị."""
        return list(cls.REGISTRY)

    @classmethod
    def info(cls, name: str) -> AlgorithmInfo:
        """Trả về thông tin của một thuật toán."""
        return cls.REGISTRY[name.lower()]
