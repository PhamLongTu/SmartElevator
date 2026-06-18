"""Thuật toán Greedy Best-First Search.

Greedy chọn node có heuristic ``h`` nhỏ nhất và bỏ qua chi phí đã đi ``g``. Vì
vậy thuật toán thường nhanh, có hướng tới mục tiêu rõ, nhưng không đảm bảo tối
ưu như UCS hoặc A*.
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class GreedyBestFirst(SearchAlgorithm):
    """Tìm kiếm tham lam theo heuristic được chọn."""

    name = "Greedy"

    def __init__(self, heuristic: str | Heuristic = "greedy") -> None:
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

        counter = itertools.count()
        root = SearchNode(state=initial_state, h=self._heuristic(initial_state))

        frontier: list[tuple[float, int, SearchNode]] = [
            (root.h, next(counter), root)
        ]
        visited: set[tuple] = {initial_state.planning_key()}

        best_node = root

        while frontier:
            if self._check_budget(result.nodes_expanded):
                result.path = best_node.reconstruct_path()
                result.cost = best_node.g
                return result

            _, _, node = heapq.heappop(frontier)
            if node.h < best_node.h:
                best_node = node

            result.nodes_expanded += 1

            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                key = next_state.planning_key()
                if key in visited:
                    continue
                visited.add(key)
                child = SearchNode(
                    state=next_state,
                    parent=node,
                    action=action,
                    g=node.g + step_cost,
                    h=self._heuristic(next_state),
                )
                heapq.heappush(frontier, (child.h, next(counter), child))

        return result
