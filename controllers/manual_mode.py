"""Manual Mode controller.

The player drives the elevator directly. Key presses are queued by the GUI (or
a test) and consumed one per update, so Manual Mode advances the *same*
:class:`~simulation.simulation_engine.SimulationEngine` through the *same*
:meth:`SimulationEngine.apply` path as AI Mode -- the only difference is that
the action source is the player's input instead of a planner.

Controls (via :class:`~controllers.input_handler.InputHandler`):
    * ``W`` -> move up
    * ``S`` -> move down
    * ``Space`` -> open door (drop off arrivals, then pick up waiting passengers)

Passenger pickup/dropoff is handled by the engine's ``STOP`` action, so the
real-time statistics (waiting time, distance, satisfaction) and the score are
tracked automatically through the shared base controller.
"""

from __future__ import annotations

from collections import deque

from controllers.input_handler import InputHandler
from controllers.mode_controller import ModeController
from models.enums import ElevatorAction, GameMode
from simulation.simulation_engine import SimulationEngine
from statistics.score_manager import ScoreManager


class ManualMode(ModeController):
    """Player-controlled elevator mode."""

    mode = GameMode.MANUAL

    def __init__(
        self,
        engine: SimulationEngine,
        score: ScoreManager | None = None,
        input_handler: InputHandler | None = None,
    ) -> None:
        super().__init__(engine, score)
        self.input = input_handler or InputHandler()
        # Pending player actions, consumed one per update tick.
        self._queue: deque[ElevatorAction] = deque()

    # ------------------------------------------------------------------
    # Input intake (called by the GUI / tests)
    # ------------------------------------------------------------------
    def press_key(self, key: str) -> bool:
        """Queue an action from a character key. Returns True if it was bound."""
        action = self.input.translate(key)
        if action is None:
            return False
        self._queue.append(action)
        return True

    def queue_action(self, action: ElevatorAction) -> None:
        """Queue an explicit action (e.g. from a Pygame key event)."""
        self._queue.append(action)

    # ------------------------------------------------------------------
    # ModeController contract
    # ------------------------------------------------------------------
    def next_action(self) -> ElevatorAction | None:
        """Pop the next queued player action, or IDLE if the queue is empty."""
        if self._queue:
            return self._queue.popleft()
        
        # In version 2, we must IDLE to advance simulation time (passenger walking/spawning)
        # even if no key is pressed.
        if not self.engine.is_finished():
            return ElevatorAction.IDLE
        return None
