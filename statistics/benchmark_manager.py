"""Chạy benchmark để so sánh các thuật toán tìm kiếm.

Benchmark dùng cùng kịch bản cho mọi thuật toán, chạy qua ``AIMode`` giống game
thật, rồi lấy trung bình các chỉ số tìm kiếm và vận hành.
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


def _mean(values: Sequence[float]) -> float:
    """Trung bình cộng, trả 0 nếu rỗng."""
    return sum(values) / len(values) if values else 0.0


def _median(values: Sequence[float]) -> float:
    """Trung vị, trả 0 nếu rỗng."""
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
    """Chỉ số benchmark đã tổng hợp cho một thuật toán."""

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
        """Tỉ lệ scenario hoàn thành."""
        return self.successes / self.runs if self.runs else 0.0


@dataclass
class BenchmarkManager:
    """Chạy tất cả thuật toán trên cùng tập scenario và gom kết quả."""

    num_passengers: int = 6
    seeds: tuple[int, ...] = (1, 2, 3, 4, 5)
    beam_width: int = 5
    difficulty: str | None = None
    simulation_time_limit: float = 45.0
    max_updates: int = 5000
    results: dict[str, AlgorithmBenchmark] = field(default_factory=dict)

    def _scenarios(self) -> list[Scenario]:
        """Tạo danh sách scenario dùng chung cho mọi thuật toán."""
        if self.difficulty:
            return [spec.build() for spec in specs_by_difficulty(self.difficulty)]

        return [
            RandomScenarioGenerator(
                num_passengers=self.num_passengers, seed=seed
            ).generate()
            for seed in self.seeds
        ]

    def _algorithm_kwargs(self, key: str) -> dict:
        """Tham số riêng cho từng thuật toán."""
        return {"beam_width": self.beam_width} if key == "beam" else {}

    def _run_one(self, key: str, scenario: Scenario) -> tuple[bool, dict[str, float]]:
        """Chạy một thuật toán trên một scenario."""
        engine = SimulationEngine(stats=StatisticsManager())
        engine.load_scenario(copy.deepcopy(scenario))
        controller = AIMode(
            engine,
            algorithm=key,
            score=ScoreManager(),
            is_reactive=True,
            **self._algorithm_kwargs(key),
        )

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
            "cost": engine.stats.solution_cost,
            "expanded": engine.stats.nodes_expanded,
            "generated": engine.stats.nodes_generated,
            "runtime_ms": engine.stats.planning_time,
            "plan_length": plan_length,
            "distance": engine.stats.total_distance,
            "wait": engine.stats.average_waiting_time,
            "satisfaction": engine.stats.satisfaction_score,
            "score": score,
        }

    def run(self) -> dict[str, AlgorithmBenchmark]:
        """Chạy benchmark và trả kết quả tổng hợp theo thuật toán."""
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

    def comparison_table(self) -> str:
        """Trả về bảng so sánh dạng văn bản."""
        if not self.results:
            self.run()

        headers = (
            "Algorithm", "Success", "AvgPlanCost", "AvgExpand",
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
        """Trả về báo cáo benchmark đầy đủ."""
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
