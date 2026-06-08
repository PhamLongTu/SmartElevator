"""Hill Climbing (local search) for the Smart Elevator problem.

Hill climbing follows a single trajectory from the initial state, repeatedly
moving to the neighbour (successor) that most reduces the heuristic ``h``
(estimated cost-to-go). It is fast and memory-light but **incomplete and
non-optimal**: it can stall in a local minimum or on a plateau where no
neighbour improves ``h`` even though the goal is not yet reached.

Two standard mitigations are included:

* **Sideways moves** -- a bounded number of equal-``h`` moves to cross plateaus.
* **Random restarts** -- re-run the climb from the initial state with randomized
  tie-breaking among equally-good neighbours. (We restart from the start rather
  than a random state because the resulting plan must be an executable
  trajectory; the elevator cannot teleport.)

Because a run may not reach the goal, callers must check
:attr:`SearchResult.success` before executing the returned plan.

Features:
    * Neighbour generation via ``State.successors``.
    * Local optimization by greedily minimizing ``h``.
    * Sideways-move and restart controls; reproducible via ``seed``.
    * Statistics collection (expanded/generated nodes, plan cost).
"""

from __future__ import annotations

import random

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.enums import ElevatorAction
from models.state import State


class HillClimbing(SearchAlgorithm):
    """Steepest-descent hill climbing minimizing a heuristic.

    Args:
        heuristic: Heuristic name or callable estimating cost-to-go. Defaults
            to ``"span"``.
        max_sideways: Maximum consecutive equal-``h`` (plateau) moves allowed
            before giving up on a climb.
        max_restarts: Number of additional restarts (with randomized
            tie-breaking) attempted if a climb fails to reach the goal.
        max_steps: Hard cap on moves per climb, guarding against pathological
            loops.
        seed: RNG seed for reproducible tie-breaking / restarts.
    """

    name = "Hill Climbing"

    def __init__(
        self,
        heuristic: str | Heuristic = "span",
        max_sideways: int = 20,
        max_restarts: int = 10,
        max_steps: int = 1000,
        seed: int = 0,
    ) -> None:
        if isinstance(heuristic, str):
            self._heuristic: Heuristic = get_heuristic(heuristic)
            self.heuristic_name = heuristic
        else:
            self._heuristic = heuristic
            self.heuristic_name = getattr(heuristic, "__name__", "custom")
        self.max_sideways = max_sideways
        self.max_restarts = max_restarts
        self.max_steps = max_steps
        self.seed = seed

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()
        rng = random.Random(self.seed)

        best_partial: list[ElevatorAction] = []
        best_partial_h = float("inf")
        best_partial_cost = 0.0

        for attempt in range(self.max_restarts + 1):
            outcome = self._climb(initial_state, rng, result)
            reached, path, cost, final_h = outcome

            if reached:
                result.path = path
                result.cost = cost
                result.success = True
                return result

            # Remember the closest-to-goal partial trajectory for reporting.
            if final_h < best_partial_h:
                best_partial_h = final_h
                best_partial = path
                best_partial_cost = cost

        # No restart reached the goal: report the best partial (success=False).
        result.path = best_partial
        result.cost = best_partial_cost
        result.success = False
        return result

    def _climb(
        self,
        initial_state: State,
        rng: random.Random,
        result: SearchResult,
    ) -> tuple[bool, list[ElevatorAction], float, float]:
        """Run one hill-climb. Returns (reached_goal, path, cost, final_h)."""
        current = initial_state
        current_h = self._heuristic(current)
        path: list[ElevatorAction] = []
        cost = 0.0
        sideways_used = 0
        visited: set[State] = {current}

        for _ in range(self.max_steps):
            if current.is_goal() or self._check_budget(result.nodes_expanded):
                return current.is_goal(), path, cost, 0.0 if current.is_goal() else current_h

            result.nodes_expanded += 1

            # Neighbour generation.
            neighbours = current.successors()
            result.nodes_generated += len(neighbours)

            # Evaluate neighbours we have not already visited this climb.
            scored: list[tuple[float, ElevatorAction, State, float]] = []
            for action, next_state, step_cost in neighbours:
                if next_state in visited:
                    continue
                scored.append(
                    (self._heuristic(next_state), action, next_state, step_cost)
                )

            if not scored:
                # Dead end: every neighbour already visited.
                return False, path, cost, current_h

            # Find the best (lowest-h) neighbours; randomize ties for restarts.
            best_h = min(item[0] for item in scored)
            best_choices = [item for item in scored if item[0] == best_h]
            chosen_h, action, next_state, step_cost = rng.choice(best_choices)

            if chosen_h < current_h:
                # Strict improvement: take it, reset the sideways budget.
                sideways_used = 0
            elif chosen_h == current_h and sideways_used < self.max_sideways:
                # Plateau: allow a bounded sideways move.
                sideways_used += 1
            else:
                # Local minimum (no improving neighbour): stop this climb.
                return False, path, cost, current_h

            current = next_state
            current_h = chosen_h
            path.append(action)
            cost += step_cost
            visited.add(next_state)

        # Step budget exhausted without reaching the goal.
        return False, path, cost, current_h
