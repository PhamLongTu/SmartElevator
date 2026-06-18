"""Bộ điều phối chế độ Đối đầu.

Hai bên cùng chạy trên một kịch bản được clone riêng để đảm bảo công bằng, sau
đó báo cáo các chỉ số vận hành và tìm kiếm để so sánh.
"""

from __future__ import annotations

from dataclasses import dataclass

from controllers.ai_mode import AIMode
from controllers.input_handler import InputHandler
from controllers.manual_mode import ManualMode
from models.enums import GameMode
from simulation.scenario import Scenario, ScenarioGenerator
from simulation.simulation_engine import SimulationEngine, StepResult
from statistics.score_manager import ScoreManager
from statistics.statistics_manager import StatisticsManager


@dataclass
class CompareReport:
    """Báo cáo so sánh hai lượt chạy."""

    player_wait: float
    player_distance: int
    player_urgent: int
    player_failures: str
    player_score: int
    player_finished: bool
    player_nodes_expanded: int
    player_nodes_generated: int
    player_planning_time: float

    ai_wait: float
    ai_distance: int
    ai_urgent: int
    ai_failures: str
    ai_score: int
    ai_finished: bool
    ai_nodes_expanded: int
    ai_nodes_generated: int
    ai_planning_time: float

    ai_algorithm: str = ""
    player_algorithm: str = ""
    is_left_ai: bool = False

    @property
    def winner(self) -> str:
        if self.player_score > self.ai_score:
            return "AI 1" if self.is_left_ai else "Player"
        if self.ai_score > self.player_score:
            return "AI 2" if self.is_left_ai else "AI"
        
        if self.player_finished and not self.ai_finished:
            return "AI 1" if self.is_left_ai else "Player"
        if self.ai_finished and not self.player_finished:
            return "AI 2" if self.is_left_ai else "AI"
            
        return "Tie"

    @property
    def margin(self) -> int:
        return abs(self.player_score - self.ai_score)

    def as_table(self) -> str:
        p1 = "AI 1" if self.is_left_ai else "Player"
        p2 = "AI 2" if self.is_left_ai else "AI"
        rows = [
            ("Metric", p1, p2),
            ("Waiting units", f"{self.player_wait:.2f}", f"{self.ai_wait:.2f}"),
            ("Distance", str(self.player_distance), str(self.ai_distance)),
            ("Urgent Served", str(self.player_urgent), str(self.ai_urgent)),
            ("Fail (L/A)", self.player_failures, self.ai_failures),
            ("Expanded", str(self.player_nodes_expanded), str(self.ai_nodes_expanded)),
            ("Generated", str(self.player_nodes_generated), str(self.ai_nodes_generated)),
            ("Final score", str(self.player_score), str(self.ai_score)),
        ]
        widths = [max(len(r[i]) for r in rows) for i in range(3)]
        sep = "-+-".join("-" * w for w in widths)
        out = []
        for idx, row in enumerate(rows):
            out.append(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
            if idx == 0:
                out.append(sep)
        out.append(f"\nWinner: {self.winner}" + (f" (by {self.margin})" if self.margin else ""))
        return "\n".join(out)


class CompareMode:
    """Điều phối hai engine chạy trên cùng một kịch bản."""

    mode = GameMode.COMPARE

    def __init__(
        self,
        scenario: Scenario | None = None,
        generator: ScenarioGenerator | None = None,
        ai_algorithm: str = "astar",
        player_algorithm: str | None = None,
        score: ScoreManager | None = None,
        input_handler: InputHandler | None = None,
        ai_algorithm_kwargs: dict | None = None,
        player_algorithm_kwargs: dict | None = None,
        **algorithm_kwargs,
    ) -> None:
        if scenario is None:
            if generator is None:
                raise ValueError("Provide either a scenario or a generator.")
            scenario = generator.generate()
        self.scenario = scenario
        self.score = score or ScoreManager()

        import copy
        self.player_engine = SimulationEngine(stats=StatisticsManager())
        self.player_engine.load_scenario(copy.deepcopy(scenario))
        self.ai_engine = SimulationEngine(stats=StatisticsManager())
        self.ai_engine.load_scenario(copy.deepcopy(scenario))

        ai_kwargs = dict(algorithm_kwargs)
        if ai_algorithm_kwargs:
            ai_kwargs.update(ai_algorithm_kwargs)

        player_kwargs = dict(algorithm_kwargs)
        if player_algorithm_kwargs:
            player_kwargs.update(player_algorithm_kwargs)

        if player_algorithm is not None:
            self.player = AIMode(
                self.player_engine, algorithm=player_algorithm, 
                score=ScoreManager(self.score.weights), **player_kwargs
            )
        else:
            self.player = ManualMode(
                self.player_engine, score=ScoreManager(self.score.weights), input_handler=input_handler
            )

        self.ai = AIMode(
            self.ai_engine, algorithm=ai_algorithm, 
            score=ScoreManager(self.score.weights), **ai_kwargs
        )

    def update_player(self) -> StepResult | None:
        return self.player.update()

    def update_ai(self) -> StepResult | None:
        return self.ai.update()

    def run_ai_to_completion(self, max_updates: int = 5000) -> None:
        n = 0
        while not self.ai.finished and n < max_updates:
            self.ai.update()
            n += 1

    @property
    def finished(self) -> bool:
        return self.player.finished and self.ai.finished

    def report(self) -> CompareReport:
        p, a = self.player_engine.stats, self.ai_engine.stats
        return CompareReport(
            player_wait=p.average_waiting_time,
            player_distance=p.total_distance,
            player_urgent=p.urgent_delivered_count,
            player_failures=f"{p.left_count}/{p.angry_count}",
            player_score=self.player.score.update(p),
            player_finished=self.player.finished,
            player_nodes_expanded=p.nodes_expanded,
            player_nodes_generated=p.nodes_generated,
            player_planning_time=p.planning_time,
            ai_wait=a.average_waiting_time,
            ai_distance=a.total_distance,
            ai_urgent=a.urgent_delivered_count,
            ai_failures=f"{a.left_count}/{a.angry_count}",
            ai_score=self.ai.score.update(a),
            ai_finished=self.ai.finished,
            ai_nodes_expanded=a.nodes_expanded,
            ai_nodes_generated=a.nodes_generated,
            ai_planning_time=a.planning_time,
            ai_algorithm=self.ai.algorithm_name,
            player_algorithm=getattr(self.player, "algorithm_name", ""),
            is_left_ai=isinstance(self.player, AIMode)
        )
