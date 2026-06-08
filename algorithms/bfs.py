"""Breadth-First Search for the Smart Elevator problem.

BFS explores the state graph level by level using a FIFO queue. On this problem
every edge counts as one action, so BFS returns a plan with the **fewest
actions** (note: not necessarily the fewest *moves*, since ``STOP`` has zero
cost -- use UCS/A* for move-optimal plans).

Features:
    * FIFO ``deque`` frontier.
    * Duplicate-state detection via a ``visited`` set of hashable states.
    * Path reconstruction through parent links.
    * Expanded- and generated-node tracking.
"""

from __future__ import annotations

from collections import deque

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class BFS(SearchAlgorithm):
    """Breadth-first search over the elevator state space."""

    name = "BFS"

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        # Trivial case: already solved.
        if initial_state.is_goal():
            result.success = True
            return result

        root = SearchNode(state=initial_state)
        frontier: deque[SearchNode] = deque([root])

        # States that have been enqueued (enqueue-time marking prevents the
        # same state being added to the frontier more than once).
        visited: set[State] = {initial_state}

        while frontier:
            if self._check_budget(result.nodes_expanded):
                return result

            node = frontier.popleft()
            result.nodes_expanded += 1

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                if next_state in visited:
                    continue

                child = SearchNode(
                    state=next_state,
                    parent=node,
                    action=action,
                    g=node.g + step_cost,
                )

                # Early goal test at generation time (standard for BFS).
                if next_state.is_goal():
                    result.path = child.reconstruct_path()
                    result.cost = child.g
                    result.success = True
                    return result

                visited.add(next_state)
                frontier.append(child)

        # Frontier exhausted with no goal found.
        return result
