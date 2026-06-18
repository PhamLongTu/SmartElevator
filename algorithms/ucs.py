"""Thuật toán Uniform-Cost Search cho bài toán Thang máy Thông minh.

UCS luôn mở rộng node có chi phí tích lũy ``g`` nhỏ nhất. Với chi phí cạnh
không âm, UCS tìm được kế hoạch có tổng chi phí nhỏ nhất trong state hiện tại.
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class UCS(SearchAlgorithm):
    """Tìm kiếm theo chi phí thấp nhất trên không gian trạng thái thang máy."""

    name = "UCS"

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        root = SearchNode(state=initial_state)
        counter = itertools.count()

        frontier: list[tuple[float, int, SearchNode]] = [(0.0, next(counter), root)]

        best_g: dict[tuple, float] = {initial_state.planning_key(): 0.0}

        while frontier:
            if self._check_budget(result.nodes_expanded):
                return result

            g, _, node = heapq.heappop(frontier)

            if g > best_g.get(node.state.planning_key(), float("inf")):
                continue

            result.nodes_expanded += 1

            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                new_g = node.g + step_cost

                key = next_state.planning_key()
                if new_g < best_g.get(key, float("inf")):
                    best_g[key] = new_g
                    child = SearchNode(
                        state=next_state,
                        parent=node,
                        action=action,
                        g=new_g,
                    )
                    heapq.heappush(frontier, (new_g, next(counter), child))

        return result
