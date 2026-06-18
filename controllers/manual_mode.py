"""Controller cho chế độ thủ công."""

from __future__ import annotations

from collections import deque

from controllers.input_handler import InputHandler
from controllers.mode_controller import ModeController
from models.enums import ElevatorAction, GameMode
from simulation.simulation_engine import SimulationEngine
from statistics.score_manager import ScoreManager


class ManualMode(ModeController):
    """Chế độ thang máy do người chơi điều khiển."""

    mode = GameMode.MANUAL

    def __init__(
        self,
        engine: SimulationEngine,
        score: ScoreManager | None = None,
        input_handler: InputHandler | None = None,
    ) -> None:
        super().__init__(engine, score)
        self.input = input_handler or InputHandler()
        self._queue: deque[ElevatorAction] = deque()

    def press_key(self, key: str) -> bool:
        """Thêm hành động từ phím dạng chuỗi vào hàng đợi."""
        action = self.input.translate(key)
        if action is None:
            return False
        self._queue.append(action)
        return True

    def queue_action(self, action: ElevatorAction) -> None:
        """Thêm trực tiếp một hành động vào hàng đợi."""
        self._queue.append(action)

    def next_action(self) -> ElevatorAction | None:
        """Lấy hành động tiếp theo của người chơi."""
        if self._queue:
            return self._queue.popleft()
        
        if not self.engine.is_finished():
            return ElevatorAction.IDLE
        return None
