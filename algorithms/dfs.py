"""Depth-First Search for the Smart Elevator problem.

DFS explores as deep as possible along each branch before backtracking, using
an explicit LIFO stack. Because the elevator can move up and down indefinitely
without serving anyone, naive DFS could descend forever; this implementation
is a **graph search** that prevents cycles with a ``visited`` set, which makes
it complete on the finite elevator state space. An optional ``depth_limit``
provides an extra safety bound and enables depth-limited search.

DFS is **not optimal** -- the first solution found is rarely the shortest -- but
it is memory-light and fast to reach *a* solution.

Features:
    * Explicit LIFO stack frontier.
    * Cycle prevention via a ``visited`` set (marked on expansion).
    * Path reconstruction through parent links.
    * Expanded- and generated-node tracking.
    * Optional depth limit.
"""

from __future__ import annotations

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class DFS(SearchAlgorithm):
    """Depth-first (graph) search over the elevator state space.

    Args:
        depth_limit: Optional maximum depth to explore. ``None`` means no
            explicit limit (cycle prevention still guarantees termination).
    """

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

        # Cycle prevention: configurations already expanded are never expanded
        # again. Time/score are intentionally excluded because later arrivals at
        # the same passenger distribution are dominated by earlier arrivals.
        visited: set[tuple] = set()

        while stack:
            if self._check_budget(result.nodes_expanded):
                return result

            node = stack.pop()

            # Skip states already expanded via another (deeper-first) branch.
            key = node.state.planning_key()
            if key in visited:
                continue
            visited.add(key)
            result.nodes_expanded += 1

            # Goal test on expansion.
            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            # Respect an optional depth limit.
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
