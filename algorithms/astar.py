"""Thuật toán A* cho bài toán Thang máy Thông minh.

A* mở rộng trạng thái có ``f = g + h`` nhỏ nhất, trong đó ``g`` là chi phí đã đi
và ``h`` là ước lượng chi phí còn lại. Với heuristic ``span`` mặc định, thuật
toán giữ đúng bản chất tìm kiếm có định hướng và thường mở rộng ít node hơn UCS.
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class AStar(SearchAlgorithm):
    """Tìm kiếm A* theo độ ưu tiên ``f = g + h``."""

    name = "A*"

    def __init__(self, heuristic: str | Heuristic = "span") -> None:
        if isinstance(heuristic, str):
            self._heuristic: Heuristic = get_heuristic(heuristic)
            self.heuristic_name = heuristic
        else:
            self._heuristic = heuristic
            self.heuristic_name = getattr(heuristic, "__name__", "custom")

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        counter = itertools.count()
        root = SearchNode(state=initial_state, h=self._heuristic(initial_state))

        open_list: list[tuple[float, float, int, SearchNode]] = [
            (root.f, root.h, next(counter), root)
        ]
        best_g: dict[tuple, float] = {initial_state.planning_key(): 0.0}
        closed: set[tuple] = set()

        best_node = root

        while open_list:
            if self._check_budget(result.nodes_expanded):
                result.path = best_node.reconstruct_path()
                result.cost = best_node.g
                return result

            _, _, _, node = heapq.heappop(open_list)
            
            if node != root:
                if best_node == root or node.h < best_node.h or (node.h == best_node.h and node.g > best_node.g):
                    best_node = node

            key = node.state.planning_key()
            if node.g > best_g.get(key, float("inf")):
                continue

            if key in closed:
                continue
            closed.add(key)
            result.nodes_expanded += 1

            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                new_g = node.g + step_cost

                next_key = next_state.planning_key()
                if new_g < best_g.get(next_key, float("inf")):
                    best_g[next_key] = new_g
                    closed.discard(next_key)
                    child = SearchNode(
                        state=next_state,
                        parent=node,
                        action=action,
                        g=new_g,
                        h=self._heuristic(next_state),
                    )
                    heapq.heappush(
                        open_list, (child.f, child.h, next(counter), child)
                    )

        return result
