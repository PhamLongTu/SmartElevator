"""Controller cho chế độ AI.

AI lập kế hoạch từ trạng thái hiện tại, thực thi từng hành động qua cùng
``SimulationEngine.apply`` như chế độ thủ công, rồi re-plan khi cần.
"""

from __future__ import annotations

from collections import deque

from algorithms.algorithm_factory import AlgorithmFactory
from algorithms.base_search import SearchAlgorithm, SearchResult
from controllers.mode_controller import ModeController
from models.enums import ElevatorAction, GameMode
from simulation.simulation_engine import SimulationEngine
from statistics.score_manager import ScoreManager


class AIMode(ModeController):
    """Chế độ thang máy do AI điều khiển với reactive re-planning."""

    mode = GameMode.AI

    def __init__(
        self,
        engine: SimulationEngine,
        algorithm: SearchAlgorithm | str = "astar",
        score: ScoreManager | None = None,
        is_reactive: bool = True,
        **algorithm_kwargs,
    ) -> None:
        super().__init__(engine, score)
        if isinstance(algorithm, str):
            self.algorithm: SearchAlgorithm = AlgorithmFactory.create(
                algorithm, **algorithm_kwargs
            )
            self.algorithm_name = algorithm
        else:
            self.algorithm = algorithm
            self.algorithm_name = getattr(algorithm, "name", "custom")

        self.is_reactive = is_reactive
        self.result: SearchResult | None = None
        self._plan: deque[ElevatorAction] = deque()
        self._planned = False
        self._total_actions = 0

    def plan(self) -> SearchResult:
        """Chạy thuật toán tìm kiếm từ trạng thái hiện tại."""
        initial = self.engine.snapshot()
        self.result = self.algorithm.solve(initial, stats=self.engine.stats, 
                                          node_limit=2000, time_limit=0.15)
        
        if self.result.path:
            self._plan = deque(self.result.path)
            self._total_actions = len(self.result.path)
        else:
            self._plan = deque()
            
        self._planned = True
        return self.result

    def next_action(self) -> ElevatorAction | None:
        """Trả về hành động kế tiếp, re-plan khi hết plan hoặc có khách mới."""
        current_waiting = self.engine.building.num_waiting()
        
        if not hasattr(self, "_last_waiting_count"):
            self._last_waiting_count = current_waiting

        if not self._plan or not self._planned or (self.is_reactive and current_waiting != self._last_waiting_count):
            self.plan()
            self._last_waiting_count = current_waiting
            
        if self._plan:
            return self._plan.popleft()
            
        if not self.engine.is_finished():
            return ElevatorAction.IDLE
            
        return None

    @property
    def progress(self) -> tuple[int, int]:
        """Tiến độ thực thi plan hiện tại."""
        if not self._planned:
            return 0, 1
        done = self._total_actions - len(self._plan)
        return done, max(self._total_actions, 1)

    def planned_floor_sequence(self) -> list[int]:
        """Các tầng thang sẽ đi qua theo plan hiện tại."""
        if not self._planned:
            self.plan()
            
        floor = self.engine.building.elevator.current_floor
        sequence = [floor]
        if self._plan:
            for action in self._plan:
                if action is ElevatorAction.MOVE_UP:
                    floor += 1
                elif action is ElevatorAction.MOVE_DOWN:
                    floor -= 1
                sequence.append(floor)
        return sequence

    @property
    def solved(self) -> bool:
        return self.result is not None and self.result.success

    @property
    def final_score(self) -> int:
        return self.score.value
