"""Thuật toán Tìm kiếm theo Chiều sâu (DFS).

DFS đi sâu theo một nhánh trước khi quay lui. Thuật toán dùng stack LIFO và
``visited`` để tránh vòng lặp, nhưng không đảm bảo tìm lời giải tối ưu.
"""

from __future__ import annotations

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class DFS(SearchAlgorithm):
    """Tìm kiếm DFS trên không gian trạng thái thang máy."""

    name = "DFS"

    def __init__(self, depth_limit: int | None = None) -> None:
        self.depth_limit = depth_limit

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        if initial_state.is_goal():
            result.success = True
            return result

        root = SearchNode(state=initial_state)
        stack: list[SearchNode] = [root]

        visited: set[tuple] = set()

        while stack:
            if self._check_budget(result.nodes_expanded):
                return result

            node = stack.pop()

            key = node.state.planning_key()
            if key in visited:
                continue
            visited.add(key)
            result.nodes_expanded += 1

            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            if self.depth_limit is not None and node.depth() >= self.depth_limit:
                continue

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                if next_state.planning_key() in visited:
                    continue
                stack.append(
                    SearchNode(
                        state=next_state,
                        parent=node,
                        action=action,
                        g=node.g + step_cost,
                    )
                )

        return result
