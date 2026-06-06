"""Abstract base for all search algorithms.

Defines the common contract every algorithm implements (the Strategy pattern),
a :class:`SearchResult` value object carrying the plan and its metrics, and a
``solve`` template method that handles timing and optional
:class:`~statistics.statistics_manager.StatisticsManager` integration so each
concrete algorithm only implements the core search in :meth:`_search`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter

from models.enums import ElevatorAction
from models.state import State
from statistics.statistics_manager import StatisticsManager


@dataclass
class SearchResult:
    """Outcome of a search run.

    Attributes:
        path: Ordered actions from the initial state to a goal. Empty if the
            initial state was already a goal; ``None`` semantics are conveyed
            by ``success``.
        cost: Total path cost ``g`` of the returned plan.
        success: Whether a goal was reached.
        nodes_expanded: Nodes popped from the frontier and expanded.
        nodes_generated: Successor nodes created during the search.
        planning_time_ms: Wall-clock planning time in milliseconds.
        algorithm: Name of the algorithm that produced this result.
    """

    path: list[ElevatorAction] = field(default_factory=list)
    cost: float = 0.0
    success: bool = False
    nodes_expanded: int = 0
    nodes_generated: int = 0
    planning_time_ms: float = 0.0
    algorithm: str = ""

    @property
    def plan_length(self) -> int:
        """Number of actions in the plan."""
        return len(self.path)


class SearchAlgorithm(ABC):
    """Base class for every elevator search algorithm.

    Subclasses implement :meth:`_search`. Callers use :meth:`solve`, which
    times the run, fills in the algorithm name, and (optionally) mirrors the
    metrics into a shared :class:`StatisticsManager`.
    """

    #: Human-readable name, overridden by each subclass.
    name: str = "Search"

    def solve(
        self,
        initial_state: State,
        stats: StatisticsManager | None = None,
    ) -> SearchResult:
        """Plan from ``initial_state`` to a goal state.

        Args:
            initial_state: The state to search from.
            stats: Optional shared statistics manager to update with the
                resulting search-quality metrics.

        Returns:
            A :class:`SearchResult` with the plan and its metrics.
        """
        start = perf_counter()
        result = self._search(initial_state)
        result.planning_time_ms = (perf_counter() - start) * 1000.0
        result.algorithm = self.name

        if stats is not None:
            stats.nodes_expanded = result.nodes_expanded
            stats.nodes_generated = result.nodes_generated
            stats.planning_time = result.planning_time_ms
            stats.solution_cost = result.cost

        return result

    @abstractmethod
    def _search(self, initial_state: State) -> SearchResult:
        """Run the core search. Implemented by each concrete algorithm."""
        raise NotImplementedError
