"""Heuristic functions for the informed and local search algorithms.

A heuristic estimates the remaining cost from a :class:`~models.state.State`
to a goal. The module exposes a small registry so algorithms can select a
heuristic by name (the "selected heuristic" used by Greedy / A* / local search).

All move-based heuristics are admissible **relative to the unit-move objective**
(``MOVE = 1``, ``STOP = 0``). See the design notes for proofs:

* ``zero``      -- H0, baseline (turns A* into UCS).
* ``farthest``  -- H1, distance to the farthest pending floor.
* ``span``      -- H2, interval-cover; admissible **and** consistent (default A*).
* ``onboard``   -- H3, delivery span of onboard riders only.
* ``stops``     -- H4, count of distinct service floors (informative, *inadmissible*).
* ``greedy``    -- blended ``span + alpha * undelivered`` (inadmissible, for Greedy).
"""

from __future__ import annotations

from collections.abc import Callable

from models.state import State

#: A heuristic maps a state to an estimated remaining cost.
Heuristic = Callable[[State], float]


def zero(state: State) -> float:
    """H0: no information. Admissible and consistent."""
    return 0.0


def farthest(state: State) -> float:
    """H1: moves to reach the single farthest pending floor."""
    return state.heuristic("farthest")


def span(state: State) -> float:
    """H2: interval-cover span. Admissible and consistent; default for A*."""
    return state.heuristic("span")


def onboard(state: State) -> float:
    """H3: delivery span considering only passengers already onboard."""
    dests = state.onboard_dests
    if not dests:
        return 0.0
    f = state.elevator_floor
    lo, hi = min(dests), max(dests)
    return float((hi - lo) + min(abs(f - lo), abs(f - hi)))


def stops(state: State) -> float:
    """H4: number of distinct floors still needing service.

    Strong goal-progress signal but **inadmissible** under the move objective
    (counts zero-cost STOPs). Use for Greedy, not for optimal A*.
    """
    return float(len(state.targets()))


def greedy_blend(alpha: float = 1.5) -> Heuristic:
    """Blended heuristic ``span + alpha * (# undelivered passengers)``.

    Inadmissible by design: it adds strong goal-pull toward clearing all
    passengers, which suits Greedy Best-First Search (admissibility is
    irrelevant there since ``g`` is ignored).

    Args:
        alpha: Weight on the undelivered-passenger term.

    Returns:
        A heuristic callable.
    """

    def _h(state: State) -> float:
        return state.heuristic("span") + alpha * state.num_in_system

    return _h


#: Registry of the parameter-free heuristics, selectable by name.
REGISTRY: dict[str, Heuristic] = {
    "zero": zero,
    "farthest": farthest,
    "span": span,
    "onboard": onboard,
    "stops": stops,
    "greedy": greedy_blend(),
}


def get_heuristic(name: str) -> Heuristic:
    """Look up a heuristic by name.

    Args:
        name: One of the keys in :data:`REGISTRY`.

    Raises:
        KeyError: If ``name`` is not a registered heuristic.
    """
    try:
        return REGISTRY[name]
    except KeyError as exc:
        valid = ", ".join(sorted(REGISTRY))
        raise KeyError(f"Unknown heuristic {name!r}. Valid options: {valid}.") from exc
