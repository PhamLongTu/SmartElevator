"""Uniform-Cost Search for the Smart Elevator problem.

UCS expands the frontier node with the lowest accumulated path cost ``g`` using
a priority queue (min-heap). It is **complete and optimal** for non-negative
edge costs, so on this problem it returns a plan of minimum total cost. Under
the move-count objective (``MOVE = 1``, ``STOP = 0``) that means the
**fewest elevator moves** -- unlike BFS, which only minimizes the number of
actions.

Features:
    * ``heapq`` priority queue ordered by ``g`` (with an insertion counter to
      break ties deterministically and avoid comparing nodes).
    * Cost tracking via ``SearchNode.g``.
    * ``best_g`` map so a cheaper path to a state supersedes an earlier one.
    * Goal test on *expansion* (pop) to preserve optimality.
    * Expanded- and generated-node tracking.
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class UCS(SearchAlgorithm):
    """Uniform-cost (Dijkstra-style) search over the elevator state space."""

    name = "UCS"

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        root = SearchNode(state=initial_state)
        counter = itertools.count()  # tie-breaker for equal-cost nodes

        # Heap entries are (g, insertion_index, node).
        frontier: list[tuple[float, int, SearchNode]] = [(0.0, next(counter), root)]

        # Cheapest known cost to reach each state.
        best_g: dict[State, float] = {initial_state: 0.0}

        while frontier:
            if self._check_budget(result.nodes_expanded):
                return result

            g, _, node = heapq.heappop(frontier)

            # A stale heap entry: a cheaper path to this state was found later.
            if g > best_g.get(node.state, float("inf")):
                continue

            result.nodes_expanded += 1

            # Goal test on expansion guarantees optimality.
            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                new_g = node.g + step_cost

                # Only enqueue if this is a strictly cheaper route to next_state.
                if new_g < best_g.get(next_state, float("inf")):
                    best_g[next_state] = new_g
                    child = SearchNode(
                        state=next_state,
                        parent=node,
                        action=action,
                        g=new_g,
                    )
                    heapq.heappush(frontier, (new_g, next(counter), child))

        return result
