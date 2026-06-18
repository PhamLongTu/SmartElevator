"""Lớp nền cho các controller chế độ chơi."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.enums import ElevatorAction, GameMode
from simulation.simulation_engine import SimulationEngine, StepResult
from statistics.score_manager import ScoreManager


class ModeController(ABC):
    """Bộ điều khiển chung quanh ``SimulationEngine``."""

    mode: GameMode = GameMode.MANUAL

    def __init__(
        self,
        engine: SimulationEngine,
        score: ScoreManager | None = None,
    ) -> None:
        self.engine = engine
        self.score = score or ScoreManager()
        self.engine.mode = self.mode

    @abstractmethod
    def next_action(self) -> ElevatorAction | None:
        """Trả về hành động kế tiếp hoặc ``None`` nếu không làm gì."""
        raise NotImplementedError

    def update(self) -> StepResult | None:
        """Thực thi một hành động và cập nhật điểm."""
        if self.engine.is_finished():
            return None

        action = self.next_action()
        if action is None:
            return None

        result = self.engine.apply(action)
        self.score.update(self.engine.stats)
        return result

    @property
    def finished(self) -> bool:
        """Cho biết mô phỏng đã hoàn tất chưa."""
        return self.engine.is_finished()
