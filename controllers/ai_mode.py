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
        # Decrease limits for live play to keep the UI smooth (60FPS)
        # 2000 nodes / 0.15s is usually enough for a good partial plan
        self.result = self.algorithm.solve(initial, stats=self.engine.stats, 
                                          node_limit=2000, time_limit=0.15)
        
        if self.result.path:
            self._plan = deque(self.result.path)
            self._total_actions = len(self.result.path)
        else:
            self._plan = deque()
            
        self._planned = True
        return self.result
            
        return self.result

    # ------------------------------------------------------------------
    # ModeController contract
    # ------------------------------------------------------------------
    def next_action(self) -> ElevatorAction | None:
        """Return the next action. Re-plans only if necessary or new passengers arrived."""
        current_waiting = self.engine.building.num_waiting()
        
        # Initialize last_waiting_count on first call
        if not hasattr(self, "_last_waiting_count"):
            self._last_waiting_count = current_waiting

        # Re-plan if plan is empty OR new passengers have arrived
        if not self._plan or not self._planned or (self.is_reactive and current_waiting != self._last_waiting_count):
            self.plan()
            self._last_waiting_count = current_waiting
            
        if self._plan:
            return self._plan.popleft()
            
        # --- Greedy Fallback ---
        # If search failed to find a path (even a partial one), force a greedy step.
        # if not self.engine.is_finished():
        #     state = self.engine.snapshot()
        #     targets = state.targets()
            
        #     # If full, only care about where people want to go, not new pickups
        #     if len(state.onboard) >= 4: # ELEVATOR_CAPACITY
        #         targets = {p[0] for p in state.onboard}
                
        #     if targets:
        #         f = state.elevator_floor
        #         best_t = min(targets, key=lambda t: abs(t - f))
        #         if best_t > f:
        #             return ElevatorAction.MOVE_UP
        #         elif best_t < f:
        #             return ElevatorAction.MOVE_DOWN
        #         else:
        #             return ElevatorAction.STOP
        
        # If we really have nothing to do but simulation is NOT finished 
        # (meaning more passengers are yet to spawn), we must IDLE to advance time.
        if not self.engine.is_finished():
            return ElevatorAction.IDLE
            
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
        if self.result and self.result.path:
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
