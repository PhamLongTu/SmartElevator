"""Compare Mode coordinator.

Runs a player (manual) simulation and an AI simulation on the **same scenario**
so their results are directly comparable, then reports the head-to-head metrics
and declares a winner.

Fairness guarantee: both sides are built from one shared
:class:`~simulation.scenario.Scenario`. Loading the same scenario into two
engines yields identical initial states, so neither side gets an easier problem.

Unlike :class:`ManualMode` / :class:`AIMode`, this is a *coordinator* rather
than a :class:`~controllers.mode_controller.ModeController`: it owns one of each
and advances them independently (the player drives interactively while the AI
auto-runs).
"""

from __future__ import annotations

from dataclasses import dataclass

from controllers.ai_mode import AIMode
from controllers.input_handler import InputHandler
from controllers.manual_mode import ManualMode
from models.enums import GameMode
from simulation.scenario import Scenario, ScenarioGenerator
from simulation.simulation_engine import SimulationEngine
from statistics.score_manager import ScoreManager
from statistics.statistics_manager import StatisticsManager


@dataclass
class CompareReport:
    """Head-to-head comparison of the player and AI runs."""

    # Player metrics
    player_wait: float
    player_distance: int
    player_urgent: int
    player_failures: str # "Left/Angry"
    player_score: int
    player_finished: bool

    # AI metrics
    ai_wait: float
    ai_distance: int
    ai_urgent: int
    ai_failures: str
    ai_score: int
    ai_finished: bool

    ai_algorithm: str = ""

    @property
    def winner(self) -> str:
        if self.player_finished and not self.ai_finished:
            return "Player"
        if self.ai_finished and not self.player_finished:
            return "AI"
        if not self.player_finished and not self.ai_finished:
            return "Tie"
        if self.player_score > self.ai_score:
            return "Player"
        if self.ai_score > self.player_score:
            return "AI"
        return "Tie"

    @property
    def margin(self) -> int:
        return abs(self.player_score - self.ai_score)

    def as_table(self) -> str:
        rows = [
            ("Metric", "Player", "AI"),
            ("Waiting units", f"{self.player_wait:.2f}", f"{self.ai_wait:.2f}"),
            ("Distance", str(self.player_distance), str(self.ai_distance)),
            ("Urgent Served", str(self.player_urgent), str(self.ai_urgent)),
            ("Fail (L/A)", self.player_failures, self.ai_failures),
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
    """Coordinates a player run and an AI run over one shared scenario."""

    mode = GameMode.COMPARE

    def __init__(
        self,
        scenario: Scenario | None = None,
        generator: ScenarioGenerator | None = None,
        ai_algorithm: str = "astar",
        score: ScoreManager | None = None,
        input_handler: InputHandler | None = None,
    ) -> None:
        if scenario is None:
            if generator is None:
                raise ValueError("Provide either a scenario or a generator.")
            scenario = generator.generate()
        self.scenario = scenario
        self.score = score or ScoreManager()

        self.player_engine = SimulationEngine(stats=StatisticsManager())
        self.player_engine.load_scenario(scenario)
        self.ai_engine = SimulationEngine(stats=StatisticsManager())
        self.ai_engine.load_scenario(scenario)

        self.player = ManualMode(
            self.player_engine, score=ScoreManager(self.score.weights), input_handler=input_handler
        )
        self.ai = AIMode(
            self.ai_engine, algorithm=ai_algorithm, score=ScoreManager(self.score.weights)
        )

    def update_player(self) -> None:
        self.player.update()

    def update_ai(self) -> None:
        self.ai.update()

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
            ai_wait=a.average_waiting_time,
            ai_distance=a.total_distance,
            ai_urgent=a.urgent_delivered_count,
            ai_failures=f"{a.left_count}/{a.angry_count}",
            ai_score=self.ai.score.update(a),
            ai_finished=self.ai.finished,
            ai_algorithm=self.ai.algorithm_name,
        )
