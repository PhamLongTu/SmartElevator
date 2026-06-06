"""Base class for game mode controllers.

Both Manual and AI modes drive the *same* :class:`~simulation.simulation_engine
.SimulationEngine` through the *same* :meth:`SimulationEngine.apply` entry
point -- they differ only in **where the next action comes from**. This base
captures that shared contract so the two modes stay interchangeable (and a
Compare mode can run one of each side by side).

A subclass implements :meth:`next_action`, returning the elevator action to
apply on this update (or ``None`` to idle). The base handles applying it,
updating the live score, and exposing completion.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.enums import ElevatorAction, GameMode
from simulation.simulation_engine import SimulationEngine, StepResult
from statistics.score_manager import ScoreManager


class ModeController(ABC):
    """Common driver around a SimulationEngine for any game mode.

    Args:
        engine: The simulation engine this mode drives.
        score: Optional score manager; one is created if omitted.
    """

    #: The game mode this controller implements.
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
        """Return the next action to apply, or ``None`` to do nothing."""
        raise NotImplementedError

    def update(self) -> StepResult | None:
        """Advance the simulation by one action from :meth:`next_action`.

        Returns the :class:`StepResult`, or ``None`` if no action was taken
        (e.g. idle, or the game is already finished).
        """
        if self.engine.is_finished():
            return None

        action = self.next_action()
        if action is None:
            return None

        result = self.engine.apply(action)
        # Keep the live score in sync with the latest statistics.
        self.score.update(self.engine.stats)
        return result

    @property
    def finished(self) -> bool:
        """Whether the underlying simulation is complete."""
        return self.engine.is_finished()
