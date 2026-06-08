"""A* Search for the Smart Elevator problem.

A* expands the frontier node minimizing ``f(n) = g(n) + h(n)``, where ``g`` is
the accumulated path cost and ``h`` is the heuristic estimate of remaining cost.
With an **admissible** heuristic A* is optimal; with a **consistent** heuristic
(the default ``"span"`` interval-cover is both) it never needs to reopen closed
nodes. A* combines UCS's cost-optimality with Greedy's goal-direction, so it
typically reaches the optimal plan while expanding far fewer nodes than UCS.

Implementation:
    * **Open list**: a ``heapq`` priority queue ordered by ``f`` (ties broken by
      ``h`` then insertion order via the node ordering / counter).
    * **Closed list**: a set of states already expanded.
    * **best_g** map: cheapest known cost per state; supports reopening a closed
      node if a strictly cheaper path is later discovered (safe even for merely
      admissible, non-consistent heuristics).
    * Path reconstruction through parent links.
    * Statistics: expanded/generated node counts and final plan cost.
"""

from __future__ import annotations

import heapq
import itertools

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class AStar(SearchAlgorithm):
    """A* search ordered by ``f = g + h``.

    Args:
        heuristic: A heuristic name (looked up in the registry) or a callable.
            Defaults to ``"span"`` -- admissible and consistent, so A* is optimal.
    """

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

        # Open list: (f, h, insertion_index, node).
        open_list: list[tuple[float, float, int, SearchNode]] = [
            (root.f, root.h, next(counter), root)
        ]
        # Cheapest known g per state (open or closed).
        best_g: dict[State, float] = {initial_state: 0.0}
        # Closed list: states already expanded.
        closed: set[State] = set()

        while open_list:
            if self._check_budget(result.nodes_expanded):
                return result

            _, _, _, node = heapq.heappop(open_list)

            # Skip stale entries: a cheaper path to this state was queued later.
            if node.g > best_g.get(node.state, float("inf")):
                continue

            if node.state in closed:
                continue
            closed.add(node.state)
            result.nodes_expanded += 1

            # Goal test on expansion preserves optimality.
            if node.state.is_goal():
                result.path = node.reconstruct_path()
                result.cost = node.g
                result.success = True
                return result

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                new_g = node.g + step_cost

                # Enqueue only if this is a strictly cheaper route to next_state.
                if new_g < best_g.get(next_state, float("inf")):
                    best_g[next_state] = new_g
                    # Allow reopening if a cheaper path to a closed node appears.
                    closed.discard(next_state)
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
