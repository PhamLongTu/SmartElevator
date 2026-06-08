"""Greedy Best-First Search for the Smart Elevator problem.

Greedy expands the frontier node that *looks* closest to the goal, ordering the
priority queue purely by the heuristic ``h(s)`` and ignoring the path cost
``g``. This makes it fast and strongly goal-directed, but **not optimal** and
not even complete unless cycles are prevented (which they are here, via a
visited set on the finite state space).

Because ``g`` is ignored, admissibility is irrelevant: the default heuristic is
the inadmissible ``"greedy"`` blend (``span + alpha * undelivered``), which
gives the strongest pull toward clearing all passengers.

Features:
    * Selectable heuristic by name (see :mod:`algorithms.heuristics`).
    * ``heapq`` priority queue ordered by ``h`` (insertion counter breaks ties).
    * Cycle prevention via a ``visited`` set.
    * Statistics collection (expanded/generated nodes, cost of the found plan).
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class GreedyBestFirst(SearchAlgorithm):
    """Greedy best-first search ordered by a selected heuristic.

    Args:
        heuristic: Either a heuristic name (looked up in the registry) or a
            ready callable. Defaults to the ``"greedy"`` blend.
    """

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

        # Heap entries: (h, insertion_index, node).
        frontier: list[tuple[float, int, SearchNode]] = [
            (root.h, next(counter), root)
        ]
        visited: set[State] = {initial_state}

        while frontier:
            if self._check_budget(result.nodes_expanded):
                return result

            _, _, node = heapq.heappop(frontier)
            result.nodes_expanded += 1

            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                if next_state in visited:
                    continue
                visited.add(next_state)
                child = SearchNode(
                    state=next_state,
                    parent=node,
                    action=action,
                    g=node.g + step_cost,
                    h=self._heuristic(next_state),
                )
                heapq.heappush(frontier, (child.h, next(counter), child))

        return result
