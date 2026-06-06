"""Factory for selecting search algorithms by name (Strategy + Factory pattern).

Centralizes the mapping from a short key (e.g. ``"astar"``) to a concrete
:class:`~algorithms.base_search.SearchAlgorithm`, along with display metadata
for building an algorithm-selection menu in AI Mode. Adding a new algorithm is a
one-line registry entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from algorithms.astar import AStar
from algorithms.base_search import SearchAlgorithm
from algorithms.beam_search import BeamSearch
from algorithms.bfs import BFS
from algorithms.dfs import DFS
from algorithms.greedy import GreedyBestFirst
from algorithms.hill_climbing import HillClimbing
from algorithms.ucs import UCS


@dataclass(frozen=True)
class AlgorithmInfo:
    """Display metadata for a selectable algorithm.

    Attributes:
        key: Short identifier used for selection.
        display_name: Human-friendly name for menus/HUD.
        category: ``"Uninformed"``, ``"Informed"``, or ``"Local"``.
        factory: Zero-arg callable returning a fresh algorithm instance.
    """

    key: str
    display_name: str
    category: str
    factory: type[SearchAlgorithm]


class AlgorithmFactory:
    """Creates search algorithms by name and lists what's available."""

    #: Ordered registry of selectable algorithms.
    REGISTRY: dict[str, AlgorithmInfo] = {
        "bfs": AlgorithmInfo("bfs", "Breadth-First Search", "Uninformed", BFS),
        "dfs": AlgorithmInfo("dfs", "Depth-First Search", "Uninformed", DFS),
        "ucs": AlgorithmInfo("ucs", "Uniform-Cost Search", "Uninformed", UCS),
        "greedy": AlgorithmInfo("greedy", "Greedy Best-First", "Informed", GreedyBestFirst),
        "astar": AlgorithmInfo("astar", "A* Search", "Informed", AStar),
        "hill": AlgorithmInfo("hill", "Hill Climbing", "Local", HillClimbing),
        "beam": AlgorithmInfo("beam", "Beam Search", "Local", BeamSearch),
    }

    @classmethod
    def create(cls, name: str, **kwargs) -> SearchAlgorithm:
        """Instantiate the algorithm registered under ``name``.

        Args:
            name: A registry key (case-insensitive).
            **kwargs: Forwarded to the algorithm constructor (e.g.
                ``beam_width=10`` for beam, ``heuristic="span"`` for A*).

        Raises:
            KeyError: If ``name`` is not registered.
        """
        key = name.lower()
        try:
            info = cls.REGISTRY[key]
        except KeyError as exc:
            valid = ", ".join(cls.REGISTRY)
            raise KeyError(f"Unknown algorithm {name!r}. Valid: {valid}.") from exc
        return info.factory(**kwargs)

    @classmethod
    def available(cls) -> list[str]:
        """Return the list of registered algorithm keys, in display order."""
        return list(cls.REGISTRY)

    @classmethod
    def info(cls, name: str) -> AlgorithmInfo:
        """Return the :class:`AlgorithmInfo` for a registry key."""
        return cls.REGISTRY[name.lower()]
