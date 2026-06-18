"""Benchmark harness for comparing all search algorithms.

Runs every algorithm in the :class:`~algorithms.algorithm_factory
.AlgorithmFactory` registry on the **same** set of scenarios (identical seeds,
so every algorithm faces exactly the same problems), then aggregates and
tabulates the results.

Two kinds of metric are collected per run:

* **Search-quality** (planning): solution cost, plan length, nodes
  expanded/generated, planning runtime across every reactive re-plan.
* **Outcome** (execution): the selected algorithm is driven through
  :class:`controllers.ai_mode.AIMode`, so benchmark runs follow the same
  dynamic spawn, walking, STOP-duration, scoring, and timeout logic as the game.

Because wall-clock runtime is noisy, aggregates report the **mean** across
scenarios and a **success rate**; node counts (hardware-independent) are the
more reliable effort metric.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.ai_mode import AIMode
from simulation.dataset import specs_by_difficulty
from simulation.scenario import RandomScenarioGenerator, Scenario
from simulation.simulation_engine import SimulationEngine
from statistics.score_manager import ScoreManager
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
        successes: Number of scenarios completed within the simulation limit.
        avg_cost: Mean cumulative plan cost over all runs.
        avg_expanded: Mean cumulative nodes expanded over all runs.
        avg_generated: Mean cumulative nodes generated over all runs.
        avg_runtime_ms: Mean cumulative planning runtime over all runs.
        median_runtime_ms: Median planning runtime (robust to outliers).
        avg_plan_length: Mean cumulative planned action count over all runs.
        avg_distance: Mean travel distance over all runs.
        avg_wait: Mean average-waiting-time over all runs.
        avg_satisfaction: Mean satisfaction (0..1) over all runs.
        avg_score: Mean game score over all runs.
    """

    key: str
    display_name: str
    runs: int = 0
    successes: int = 0
    avg_cost: float = 0.0
    avg_expanded: float = 0.0
    avg_generated: float = 0.0
    avg_runtime_ms: float = 0.0
    median_runtime_ms: float = 0.0
    avg_plan_length: float = 0.0
    avg_distance: float = 0.0
    avg_wait: float = 0.0
    avg_satisfaction: float = 0.0
    avg_score: float = 0.0

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
        difficulty: Optional dataset difficulty (Easy/Medium/Hard). When set,
            the 10 matching structured dataset scenarios are used.
        simulation_time_limit: Simulated game-time limit, matching AI Mode.
        max_updates: Safety cap for controller updates per run.
    """

    num_passengers: int = 6
    seeds: tuple[int, ...] = (1, 2, 3, 4, 5)
    beam_width: int = 5
    difficulty: str | None = None
    simulation_time_limit: float = 45.0
    max_updates: int = 5000
    results: dict[str, AlgorithmBenchmark] = field(default_factory=dict)

    def _scenarios(self) -> list[Scenario]:
        """Build one identical scenario per seed (shared by all algorithms)."""
        if self.difficulty:
            return [spec.build() for spec in specs_by_difficulty(self.difficulty)]

        return [
            RandomScenarioGenerator(
                num_passengers=self.num_passengers, seed=seed
            ).generate()
            for seed in self.seeds
        ]

    def _algorithm_kwargs(self, key: str) -> dict:
        """Per-algorithm constructor kwargs."""
        return {"beam_width": self.beam_width} if key == "beam" else {}

    def _run_one(self, key: str, scenario: Scenario) -> tuple[bool, dict[str, float]]:
        """Run one algorithm through the same controller path as AI Mode."""
        engine = SimulationEngine(stats=StatisticsManager())
        engine.load_scenario(copy.deepcopy(scenario))
        controller = AIMode(
            engine,
            algorithm=key,
            score=ScoreManager(),
            is_reactive=True,
            **self._algorithm_kwargs(key),
        )

        expanded = 0
        generated = 0
        runtime_ms = 0.0
        plan_cost = 0.0
        plan_length = 0
        last_search_result = None

        updates = 0
        while (
            not controller.finished
            and updates < self.max_updates
            and engine.time < self.simulation_time_limit
        ):
            result = controller.update()
            updates += 1

            search_result = controller.result
            if search_result is not None and search_result is not last_search_result:
                last_search_result = search_result
                expanded += search_result.nodes_expanded
                generated += search_result.nodes_generated
                runtime_ms += search_result.planning_time_ms
                plan_cost += search_result.cost
                plan_length += search_result.plan_length

            if result is None and controller.finished:
                break

        score = controller.score.update(engine.stats)
        completed = (
            controller.finished
            and engine.scenario is not None
            and engine.stats.delivered_count == len(engine.scenario.passengers)
        )
        return completed, {
            "cost": plan_cost,
            "expanded": expanded,
            "generated": generated,
            "runtime_ms": runtime_ms,
            "plan_length": plan_length,
            "distance": engine.stats.total_distance,
            "wait": engine.stats.average_waiting_time,
            "satisfaction": engine.stats.satisfaction_score,
            "score": score,
        }

    def run(self) -> dict[str, AlgorithmBenchmark]:
        """Execute the full benchmark and return per-algorithm aggregates."""
        scenarios = self._scenarios()
        self.results = {}

        for key in AlgorithmFactory.available():
            info = AlgorithmFactory.info(key)
            costs: list[float] = []
            expanded: list[int] = []
            generated: list[int] = []
            runtimes: list[float] = []
            plan_lengths: list[int] = []
            distances: list[float] = []
            waits: list[float] = []
            satisfactions: list[float] = []
            scores: list[float] = []
            successes = 0

            for scenario in scenarios:
                completed, metrics = self._run_one(key, scenario)
                if completed:
                    successes += 1

                costs.append(metrics["cost"])
                expanded.append(int(metrics["expanded"]))
                generated.append(int(metrics["generated"]))
                runtimes.append(metrics["runtime_ms"])
                plan_lengths.append(int(metrics["plan_length"]))
                distances.append(metrics["distance"])
                waits.append(metrics["wait"])
                satisfactions.append(metrics["satisfaction"])
                scores.append(metrics["score"])

            self.results[key] = AlgorithmBenchmark(
                key=key,
                display_name=info.display_name,
                runs=len(scenarios),
                successes=successes,
                avg_cost=_mean(costs),
                avg_expanded=_mean(expanded),
                avg_generated=_mean(generated),
                avg_runtime_ms=_mean(runtimes),
                median_runtime_ms=_median(runtimes),
                avg_plan_length=_mean(plan_lengths),
                avg_distance=_mean(distances),
                avg_wait=_mean(waits),
                avg_satisfaction=_mean(satisfactions),
                avg_score=_mean(scores),
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
            "Runtime(ms)", "Distance", "AvgWait", "Satisf%", "Score",
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
                    f"{bench.avg_score:.0f}",
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
            f"({len(self._scenarios())} scenarios, {self.simulation_time_limit:.0f}s limit) ==="
        )
        notes = (
            "Notes: Success means every scenario passenger was delivered before "
            "the simulation time limit. Costs/nodes/runtime are cumulative across "
            "reactive re-plans."
        )
        return f"{title}\n{self.comparison_table()}\n{notes}"
