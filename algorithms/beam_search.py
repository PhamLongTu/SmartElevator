"""Thuật toán Beam Search.

Beam Search mở rộng theo từng mức, sau đó chỉ giữ lại tối đa ``beam_width`` node
tốt nhất theo heuristic. Đây là biến thể giới hạn bộ nhớ, nhanh hơn tìm kiếm đầy
đủ nhưng không đảm bảo hoàn chỉnh hoặc tối ưu.
"""

from __future__ import annotations

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class BeamSearch(SearchAlgorithm):
    """Beam Search với độ rộng beam có thể cấu hình."""

    name = "Beam Search"

    def __init__(
        self,
        beam_width: int = 3,
        heuristic: str | Heuristic = "greedy",
        max_levels: int = 1000,
    ) -> None:
        if beam_width < 1:
            raise ValueError("beam_width must be >= 1.")
        self.beam_width = beam_width
        self.max_levels = max_levels
        if isinstance(heuristic, str):
            self._heuristic: Heuristic = get_heuristic(heuristic)
            self.heuristic_name = heuristic
        else:
            self._heuristic = heuristic
            self.heuristic_name = getattr(heuristic, "__name__", "custom")

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        if initial_state.is_goal():
            result.success = True
            return result

        root = SearchNode(state=initial_state, h=self._heuristic(initial_state))
        beam: list[SearchNode] = [root]
        visited: set[tuple] = {initial_state.planning_key()}

        for _ in range(self.max_levels):
            if not beam or self._check_budget(result.nodes_expanded):
                break

            candidates: list[SearchNode] = []
            for node in beam:
                result.nodes_expanded += 1

                for action, next_state, step_cost in node.state.successors():
                    result.nodes_generated += 1
                    key = next_state.planning_key()
                    if key in visited:
                        continue

                    child = SearchNode(
                        state=next_state,
                        parent=node,
                        action=action,
                        g=node.g + step_cost,
                        h=self._heuristic(next_state),
                    )

                    if next_state.is_goal():
                        result.path = child.reconstruct_path()
                        result.cost = child.g
                        result.success = True
                        return result

                    visited.add(key)
                    candidates.append(child)

            candidates.sort(key=lambda n: n.h)
            beam = candidates[: self.beam_width]

        if beam:
            best = min(beam, key=lambda n: n.h)
            result.path = best.reconstruct_path()
            result.cost = best.g
        result.success = False
        return result
