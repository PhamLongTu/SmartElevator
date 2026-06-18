"""Beam Search for the Smart Elevator problem.

Beam search is a level-synchronous local search: it keeps a *beam* of at most
``beam_width`` states, expands all of them, then **prunes** the combined pool of
successors back down to the best ``beam_width`` by heuristic ``h`` before
advancing to the next level. It is essentially a memory-bounded breadth-first /
greedy hybrid.

With ``beam_width = 1`` it degenerates to greedy hill climbing; as
``beam_width -> infinity`` it approaches a full greedy best-first frontier. It
is **incomplete and non-optimal**: a goal can be pruned out of the beam, so
callers must check :attr:`SearchResult.success`.

Heuristic choice matters: the default ``"greedy"`` blend rewards reducing the
number of passengers still in the system, which (unlike the STOP-invariant
``"span"`` heuristic) gives beam search a gradient toward actually serving
passengers.

Features:
    * Configurable ``beam_width``.
    * Beam pruning to the top-``k`` successors per level.
    * Cycle prevention via a ``visited`` set.
    * Statistics collection (expanded/generated nodes, plan cost).
"""

from __future__ import annotations

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.heuristics import Heuristic, get_heuristic
from algorithms.search_node import SearchNode
from models.state import State


class BeamSearch(SearchAlgorithm):
    """Beam search with a configurable beam width.

    Args:
        beam_width: Maximum number of states retained per level (``k``). Must
            be >= 1.
        heuristic: Heuristic name or callable used to rank/prune nodes.
            Defaults to ``"greedy"`` (better suited to local search than the
            STOP-invariant ``"span"``).
        max_levels: Hard cap on search depth, guarding against non-termination
            on instances the beam cannot solve.
    """

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

            # Expand every node currently in the beam, pooling their successors.
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

                    # Goal test at generation: return as soon as one is found.
                    if next_state.is_goal():
                        result.path = child.reconstruct_path()
                        result.cost = child.g
                        result.success = True
                        return result

                    visited.add(key)
                    candidates.append(child)

            # Beam pruning: keep only the best `beam_width` successors by h.
            candidates.sort(key=lambda n: n.h)
            beam = candidates[: self.beam_width]

        # Exhausted the beam or the level cap without reaching a goal.
        if beam:
            best = min(beam, key=lambda n: n.h)
            result.path = best.reconstruct_path()
            result.cost = best.g
        result.success = False
        return result
