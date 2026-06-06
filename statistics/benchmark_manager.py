"""Benchmark harness for comparing all search algorithms.

Runs every algorithm in the :class:`~algorithms.algorithm_factory
.AlgorithmFactory` registry on the **same** set of scenarios (identical seeds,
so every algorithm faces exactly the same problems), then aggregates and
tabulates the results.

Two kinds of metric are collected per run:

* **Search-quality** (planning): success, solution cost, plan length, nodes
  expanded/generated, planning runtime.
* **Outcome** (execution): the plan is executed in a fresh engine to measure
  travel distance, average waiting time, and passenger satisfaction.

Because wall-clock runtime is noisy, aggregates report the **mean** across
scenarios and a **success rate**; node counts (hardware-independent) are the
more reliable effort metric.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from algorithms.algorithm_factory import AlgorithmFactory
from simulation.scenario import RandomScenarioGenerator, Scenario
from simulation.simulation_engine import SimulationEngine
from statistics.statistics_manager import StatisticsManager


# NOTE: this module lives inside the local ``statistics`` package, which shadows
# Python's stdlib ``statistics`` module on the import path. We therefore define
# tiny local aggregation helpers instead of importing mean/median from stdlib.
def _mean(values: Sequence[float]) -> float:
    """Arithmetic mean, or 0.0 for an empty sequence."""
    return sum(values) / len(values) if values else 0.0


def _median(values: Sequence[float]) -> float:
    """Median, or 0.0 for an empty sequence."""
    if not values:
        return 0.0
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


@dataclass
class AlgorithmBenchmark:
    """Aggregated benchmark metrics for one algorithm across all scenarios.

    Attributes:
        key: Algorithm registry key.
        display_name: Human-friendly name.
        runs: Number of scenarios attempted.
        successes: Number of scenarios where a complete plan was found.
        avg_cost: Mean solution cost over successful runs.
        avg_expanded: Mean nodes expanded over all runs.
        avg_runtime_ms: Mean planning runtime over all runs.
        median_runtime_ms: Median planning runtime (robust to outliers).
        avg_distance: Mean travel distance of executed successful plans.
        avg_wait: Mean average-waiting-time of executed successful plans.
        avg_satisfaction: Mean satisfaction (0..1) of executed successful plans.
    """

    key: str
    display_name: str
    runs: int = 0
    successes: int = 0
    avg_cost: float = 0.0
    avg_expanded: float = 0.0
    avg_runtime_ms: float = 0.0
    median_runtime_ms: float = 0.0
    avg_distance: float = 0.0
    avg_wait: float = 0.0
    avg_satisfaction: float = 0.0

    @property
    def success_rate(self) -> float:
        """Fraction of scenarios solved (0..1)."""
        return self.successes / self.runs if self.runs else 0.0


@dataclass
class BenchmarkManager:
    """Runs all registered algorithms over identical scenarios and tabulates.

    Args:
        num_passengers: Passengers per generated scenario.
        seeds: Scenario seeds to run; each seed is one identical scenario shared
            across all algorithms.
        beam_width: Beam width passed to Beam Search.
    """

    num_passengers: int = 6
    seeds: tuple[int, ...] = (1, 2, 3, 4, 5)
    beam_width: int = 5
    results: dict[str, AlgorithmBenchmark] = field(default_factory=dict)

    def _scenarios(self) -> list[Scenario]:
        """Build one identical scenario per seed (shared by all algorithms)."""
        return [
            RandomScenarioGenerator(
                num_passengers=self.num_passengers, seed=seed
            ).generate()
            for seed in self.seeds
        ]

    def _algorithm_kwargs(self, key: str) -> dict:
        """Per-algorithm constructor kwargs."""
        return {"beam_width": self.beam_width} if key == "beam" else {}

    def run(self) -> dict[str, AlgorithmBenchmark]:
        """Execute the full benchmark and return per-algorithm aggregates."""
        scenarios = self._scenarios()
        self.results = {}

        for key in AlgorithmFactory.available():
            info = AlgorithmFactory.info(key)
            costs: list[float] = []
            expanded: list[int] = []
            runtimes: list[float] = []
            distances: list[float] = []
            waits: list[float] = []
            satisfactions: list[float] = []
            successes = 0

            for scenario in scenarios:
                # Fresh engine + algorithm per run so state never leaks.
                engine = SimulationEngine(stats=StatisticsManager())
                engine.load_scenario(scenario)
                algorithm = AlgorithmFactory.create(
                    key, **self._algorithm_kwargs(key)
                )

                result = algorithm.solve(engine.snapshot(), stats=engine.stats)
                expanded.append(result.nodes_expanded)
                runtimes.append(result.planning_time_ms)

                if result.success:
                    successes += 1
                    costs.append(result.cost)
                    # Execute the plan to capture outcome metrics.
                    for action in result.path:
                        engine.apply(action)
                    distances.append(engine.stats.total_distance)
                    waits.append(engine.stats.average_waiting_time)
                    satisfactions.append(engine.stats.satisfaction_score)

            self.results[key] = AlgorithmBenchmark(
                key=key,
                display_name=info.display_name,
                runs=len(scenarios),
                successes=successes,
                avg_cost=_mean(costs),
                avg_expanded=_mean(expanded),
                avg_runtime_ms=_mean(runtimes),
                median_runtime_ms=_median(runtimes),
                avg_distance=_mean(distances),
                avg_wait=_mean(waits),
                avg_satisfaction=_mean(satisfactions),
            )

        return self.results

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def comparison_table(self) -> str:
        """Return an aligned text table comparing all algorithms.

        Runs the benchmark first if it has not been run yet.
        """
        if not self.results:
            self.run()

        headers = (
            "Algorithm", "Success", "AvgCost", "AvgExpand",
            "Runtime(ms)", "Distance", "AvgWait", "Satisf%",
        )
        rows: list[tuple[str, ...]] = [headers]
        for bench in self.results.values():
            rows.append(
                (
                    bench.display_name,
                    f"{bench.successes}/{bench.runs}",
                    f"{bench.avg_cost:.1f}",
                    f"{bench.avg_expanded:.0f}",
                    f"{bench.avg_runtime_ms:.2f}",
                    f"{bench.avg_distance:.1f}",
                    f"{bench.avg_wait:.2f}",
                    f"{bench.avg_satisfaction * 100:.1f}",
                )
            )

        widths = [max(len(r[i]) for r in rows) for i in range(len(headers))]
        sep = "-+-".join("-" * w for w in widths)

        def fmt(row: tuple[str, ...]) -> str:
            return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

        out = [fmt(rows[0]), sep]
        out.extend(fmt(row) for row in rows[1:])
        return "\n".join(out)

    def report(self) -> str:
        """Return a titled benchmark report including the comparison table."""
        if not self.results:
            self.run()
        title = (
            f"=== Algorithm Benchmark "
            f"({self.num_passengers} passengers, {len(self.seeds)} scenarios) ==="
        )
        notes = (
            "Notes: AvgCost over successful runs only. "
            "UCS/A* are cost-optimal; BFS minimizes #actions; "
            "Hill/Beam are local (may not solve every scenario)."
        )
        return f"{title}\n{self.comparison_table()}\n{notes}"
