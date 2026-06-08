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
    """AI-controlled elevator mode with Reactive Re-planning.
    
    In Version 2, the AI re-evaluates its plan every step to accommodate 
    dynamic passenger arrivals and expiring deadlines.
    """

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

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------
    def plan(self) -> SearchResult:
        """Run the search from the *current* life state."""
        # Use current score in state so AI understands current penalty state
        initial = self.engine.snapshot()
        # Create a temporary stats manager so we don't pollute the engine stats with search attempts
        # unless search_quality tracking is needed.
        self.result = self.algorithm.solve(initial, stats=self.engine.stats)
        
        if self.result.success:
            self._plan = deque(self.result.path)
            self._total_actions = len(self.result.path)
            self._planned = True
        else:
            self._plan = deque()
            self._planned = False
            
        return self.result

    # ------------------------------------------------------------------
    # ModeController contract
    # ------------------------------------------------------------------
    def next_action(self) -> ElevatorAction | None:
        """Return the next action. Re-plans if reactive mode is on."""
        if self.is_reactive or not self._planned:
            self.plan()
            
        if self._plan:
            return self._plan.popleft()
        return None

    # ------------------------------------------------------------------
    # Data for the view layer
    # ------------------------------------------------------------------
    @property
    def progress(self) -> tuple[int, int]:
        """A simplified progress indicator for dynamic environments."""
        if not self._planned:
            return 0, 1
        done = self._total_actions - len(self._plan)
        return done, max(self._total_actions, 1)

    def planned_floor_sequence(self) -> list[int]:
        """Floors the cab will occupy over the *current* plan."""
        # Ensure we have a plan
        if not self._planned:
            self.plan()
            
        floor = self.engine.building.elevator.current_floor
        sequence = [floor]
        if self.result and self.result.success:
            for action in self.result.path:
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
