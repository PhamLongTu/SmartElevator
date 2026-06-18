"""Thuật toán Hill Climbing.

Hill Climbing đi theo một quỹ đạo duy nhất và chọn láng giềng làm heuristic tốt
nhất. Thuật toán nhanh và nhẹ bộ nhớ, nhưng dễ kẹt cực trị cục bộ nên không đảm
bảo tối ưu hoặc hoàn chỉnh.
"""

from __future__ import annotations

import random

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from models.enums import ElevatorAction
from models.state import State


class HillClimbing(SearchAlgorithm):
    """Hill Climbing theo hướng giảm heuristic mạnh nhất."""

    name = "Hill Climbing"

    def __init__(
        self,
        heuristic: str | Heuristic = "greedy",
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

            if final_h < best_partial_h:
                best_partial_h = final_h
                best_partial = path
                best_partial_cost = cost

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
        """Chạy một lần leo đồi và trả về trạng thái kết thúc."""
        current = initial_state
        current_h = self._heuristic(current)
        path: list[ElevatorAction] = []
        cost = 0.0
        sideways_used = 0
        visited: set[tuple] = {current.planning_key()}

        for _ in range(self.max_steps):
            if current.is_goal() or self._check_budget(result.nodes_expanded):
                return current.is_goal(), path, cost, 0.0 if current.is_goal() else current_h

            result.nodes_expanded += 1

            neighbours = current.successors()
            result.nodes_generated += len(neighbours)

            scored: list[tuple[float, ElevatorAction, State, float]] = []
            for action, next_state, step_cost in neighbours:
                if next_state.planning_key() in visited:
                    continue
                scored.append(
                    (self._heuristic(next_state), action, next_state, step_cost)
                )

            if not scored:
                return False, path, cost, current_h

            best_h = min(item[0] for item in scored)
            best_choices = [item for item in scored if item[0] == best_h]
            chosen_h, action, next_state, step_cost = rng.choice(best_choices)

            if chosen_h < current_h:
                sideways_used = 0
            elif chosen_h == current_h and sideways_used < self.max_sideways:
                sideways_used += 1
            else:
                # Thang máy đôi khi phải đi một bước tạm xấu hơn để tới điểm trả/đón khách.
                stop_choices = [
                    item for item in scored
                    if item[1] is ElevatorAction.STOP
                ]
                if stop_choices:
                    chosen_h, action, next_state, step_cost = min(
                        stop_choices, key=lambda item: item[0]
                    )
                sideways_used = self.max_sideways

            current = next_state
            current_h = chosen_h
            path.append(action)
            cost += step_cost
            visited.add(next_state.planning_key())

        return False, path, cost, current_h
