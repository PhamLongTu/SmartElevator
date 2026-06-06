"""The :class:`StatisticsManager`.

Central collector for the two families of performance metrics:

* **Search-quality metrics** (set by the algorithms): nodes expanded/generated,
  planning wall-time, and solution cost.
* **Outcome metrics** (set by the simulation engine during execution): total
  travel distance, waiting time, journey time, and passenger satisfaction.

Keeping all measurement in one place lets the HUD, Compare view, and score
manager read from a single source of truth.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from time import perf_counter
from typing import ClassVar

from models.passenger import Passenger


@dataclass
class StatisticsManager:
    """Accumulates search and outcome metrics for a single run.

    Attributes:
        satisfaction_tau: Patience constant for the exponential satisfaction
            model ``S = exp(-J / tau)``. Larger means more tolerant riders.
    """

    # --- search-quality metrics (planning phase) ---
    nodes_expanded: int = 0
    nodes_generated: int = 0
    planning_time: float = 0.0
    solution_cost: float = 0.0

    # --- outcome metrics (execution phase) ---
    total_distance: int = 0
    total_wait: int = 0
    total_journey: int = 0
    delivered_count: int = 0
    _satisfaction_sum: float = 0.0

    # --- configuration ---
    satisfaction_tau: float = 10.0

    # --- internal timer state ---
    _timer_start: float | None = field(default=None, repr=False)

    # ------------------------------------------------------------------
    # Search-quality recording (called by algorithms)
    # ------------------------------------------------------------------
    def record_expansion(self) -> None:
        """Count one node popped from the frontier and expanded."""
        self.nodes_expanded += 1

    def record_generation(self, count: int = 1) -> None:
        """Count ``count`` successor nodes generated."""
        self.nodes_generated += count

    def start_timer(self) -> None:
        """Begin timing a planning run."""
        self._timer_start = perf_counter()

    def stop_timer(self) -> None:
        """Stop timing and accumulate elapsed milliseconds into planning_time."""
        if self._timer_start is not None:
            self.planning_time = (perf_counter() - self._timer_start) * 1000.0
            self._timer_start = None

    # ------------------------------------------------------------------
    # Outcome recording (called by the simulation engine)
    # ------------------------------------------------------------------
    def record_move(self, floors: int = 1) -> None:
        """Record ``floors`` floors of elevator travel."""
        self.total_distance += floors

    def record_pickup(self, passenger: Passenger) -> None:
        """Record a passenger's waiting time at boarding."""
        wait = passenger.waiting_time()
        if wait is not None:
            self.total_wait += wait

    def record_delivery(self, passenger: Passenger) -> None:
        """Record a passenger's journey time and satisfaction at delivery."""
        journey = passenger.journey_time()
        if journey is not None:
            self.total_journey += journey
            self._satisfaction_sum += math.exp(-journey / self.satisfaction_tau)
            self.delivered_count += 1

    # ------------------------------------------------------------------
    # Derived metrics
    # ------------------------------------------------------------------
    @property
    def average_waiting_time(self) -> float:
        """Mean waiting time per delivered passenger (0 if none delivered)."""
        return self.total_wait / self.delivered_count if self.delivered_count else 0.0

    @property
    def average_journey_time(self) -> float:
        """Mean journey time per delivered passenger (0 if none delivered)."""
        return self.total_journey / self.delivered_count if self.delivered_count else 0.0

    @property
    def satisfaction_score(self) -> float:
        """Mean passenger satisfaction in (0, 1] (0 if none delivered)."""
        return self._satisfaction_sum / self.delivered_count if self.delivered_count else 0.0

    def summary(self) -> dict[str, float]:
        """Return a flat dict of all reportable metrics."""
        return {
            "nodes_expanded": self.nodes_expanded,
            "nodes_generated": self.nodes_generated,
            "planning_time_ms": round(self.planning_time, 3),
            "solution_cost": self.solution_cost,
            "total_distance": self.total_distance,
            "average_waiting_time": round(self.average_waiting_time, 3),
            "average_journey_time": round(self.average_journey_time, 3),
            "satisfaction_score": round(self.satisfaction_score, 4),
            "delivered_count": self.delivered_count,
        }

    # ------------------------------------------------------------------
    # Reporting functions
    # ------------------------------------------------------------------
    def report(self, title: str = "Statistics Report") -> str:
        """Return a human-readable, multi-line report of all metrics.

        Groups the metrics into the search-quality family (planning) and the
        outcome family (execution) for clarity.
        """
        lines = [
            f"=== {title} ===",
            "-- Search quality (planning) --",
            f"  Runtime           : {self.planning_time:.3f} ms",
            f"  Expanded nodes    : {self.nodes_expanded}",
            f"  Generated nodes   : {self.nodes_generated}",
            f"  Solution cost     : {self.solution_cost:.1f}",
            "-- Outcome (execution) --",
            f"  Travel distance   : {self.total_distance} floors",
            f"  Avg waiting time  : {self.average_waiting_time:.2f} ticks",
            f"  Avg journey time  : {self.average_journey_time:.2f} ticks",
            f"  Satisfaction      : {self.satisfaction_score * 100:.1f}%",
            f"  Delivered         : {self.delivered_count}",
        ]
        return "\n".join(lines)

    #: Column headers matching :meth:`as_row`, for tabular reports.
    ROW_HEADERS: ClassVar[tuple[str, ...]] = (
        "Label",
        "Runtime(ms)",
        "Expanded",
        "Cost",
        "Distance",
        "AvgWait",
        "Satisf%",
    )

    def as_row(self, label: str = "") -> tuple[str, ...]:
        """Return the metrics as a tuple of strings aligned with ``ROW_HEADERS``.

        Useful for building comparison tables (e.g. Compare Mode, benchmarks).
        """
        return (
            label,
            f"{self.planning_time:.2f}",
            str(self.nodes_expanded),
            f"{self.solution_cost:.1f}",
            str(self.total_distance),
            f"{self.average_waiting_time:.2f}",
            f"{self.satisfaction_score * 100:.1f}",
        )

    @classmethod
    def comparison_table(
        cls, rows: dict[str, "StatisticsManager"]
    ) -> str:
        """Build an aligned text table comparing several runs.

        Args:
            rows: Mapping of run label -> the manager holding that run's metrics.

        Returns:
            A formatted, column-aligned table string.
        """
        table_rows = [cls.ROW_HEADERS]
        table_rows.extend(stats.as_row(label) for label, stats in rows.items())

        widths = [
            max(len(row[i]) for row in table_rows)
            for i in range(len(cls.ROW_HEADERS))
        ]
        sep = "-+-".join("-" * w for w in widths)

        def fmt(row: tuple[str, ...]) -> str:
            return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

        out = [fmt(table_rows[0]), sep]
        out.extend(fmt(row) for row in table_rows[1:])
        return "\n".join(out)

    def reset(self) -> None:
        """Clear all metrics for a fresh run."""
        self.nodes_expanded = 0
        self.nodes_generated = 0
        self.planning_time = 0.0
        self.solution_cost = 0.0
        self.total_distance = 0
        self.total_wait = 0
        self.total_journey = 0
        self.delivered_count = 0
        self._satisfaction_sum = 0.0
        self._timer_start = None
