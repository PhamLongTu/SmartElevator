"""AI Mode controller.

The AI plans a full action sequence once (the scenario is static, so a single
plan suffices), then executes it one action per update -- driving the *same*
:class:`~simulation.simulation_engine.SimulationEngine` through the *same*
:meth:`SimulationEngine.apply` path as Manual Mode. This is what keeps the two
modes interchangeable and Compare Mode fair.

Feature data exposed for the (Pygame) view layer:
    * **Algorithm selection**: chosen via :class:`~algorithms.algorithm_factory
      .AlgorithmFactory` by name.
    * **Automatic simulation**: :meth:`next_action` pops the next planned action.
    * **Search visualization**: :attr:`result` (nodes expanded, cost, time) and
      :meth:`planned_floor_sequence` (the floors the cab will visit) give the
      view what it needs to animate the search/plan.
    * **Statistics display**: :attr:`result` and ``engine.stats``.
    * **Final score display**: :attr:`final_score` once the run completes.
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
    """AI-controlled elevator mode (plan-once, then auto-execute)."""

    mode = GameMode.AI

    def __init__(
        self,
        engine: SimulationEngine,
        algorithm: SearchAlgorithm | str = "astar",
        score: ScoreManager | None = None,
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

        self.result: SearchResult | None = None
        self._plan: deque[ElevatorAction] = deque()
        self._planned = False
        self._total_actions = 0

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def plan(self) -> SearchResult:
        """Run the search once from the current state and store the plan."""
        initial = self.engine.snapshot()
        self.result = self.algorithm.solve(initial, stats=self.engine.stats)
        self._plan = deque(self.result.path)
        self._total_actions = len(self.result.path)
        self._planned = True
        return self.result

    # ------------------------------------------------------------------
    # ModeController contract
    # ------------------------------------------------------------------
    def next_action(self) -> ElevatorAction | None:
        """Return the next planned action, planning lazily on first call."""
        if not self._planned:
            self.plan()
        if self._plan:
            return self._plan.popleft()
        return None

    # ------------------------------------------------------------------
    # Data for the view layer
    # ------------------------------------------------------------------
    @property
    def progress(self) -> tuple[int, int]:
        """``(actions_executed, total_actions)`` for a progress indicator."""
        done = self._total_actions - len(self._plan)
        return done, self._total_actions

    def planned_floor_sequence(self) -> list[int]:
        """Floors the cab will occupy over the plan (for search visualization).

        Derived purely from the planned actions, starting at the current cab
        floor. ``STOP`` keeps the floor unchanged.
        """
        if not self._planned:
            self.plan()
        floor = self.engine.building.elevator.current_floor
        sequence = [floor]
        for action in self.result.path if self.result else []:
            if action is ElevatorAction.MOVE_UP:
                floor += 1
            elif action is ElevatorAction.MOVE_DOWN:
                floor -= 1
            sequence.append(floor)
        return sequence

    @property
    def solved(self) -> bool:
        """Whether the AI produced a complete plan that reaches the goal."""
        return self.result is not None and self.result.success

    @property
    def final_score(self) -> int:
        """The current/final score (valid once the run completes)."""
        return self.score.value
