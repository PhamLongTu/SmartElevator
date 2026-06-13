"""The :class:`ScoreManager`.

Converts raw :class:`~statistics.statistics_manager.StatisticsManager` metrics
into a single game **score** (higher is better) for both Manual and AI runs, and
compares two runs to decide a Compare-Mode winner.

The score rewards delivering passengers quickly and penalizes wasted travel and
long waits, mirroring the cost-function design (journey time + distance) but
inverted so that a better run yields a higher number.
"""

from __future__ import annotations

from dataclasses import dataclass

from statistics.statistics_manager import StatisticsManager


@dataclass
class ScoreWeights:
    """Tunable weights for the score formula."""

    delivery_bonus: int = 100      # base points per delivered passenger
    urgent_delivery_bonus: int = 200 # New in v2
    satisfaction_bonus: int = 100  # scaled by mean satisfaction
    move_penalty: int = 2          # points lost per floor travelled
    wait_penalty: int = 1          # points lost per tick of total waiting
    angry_penalty: int = 100        # New in v2
    lost_penalty: int = 50          # New in v2 (LEFT)


@dataclass
class ComparisonResult:
    """Outcome of comparing two scored runs."""

    player_score: int
    ai_score: int

    @property
    def winner(self) -> str:
        if self.player_score > self.ai_score:
            return "Player"
        if self.ai_score > self.player_score:
            return "AI"
        return "Tie"

    @property
    def margin(self) -> int:
        return abs(self.player_score - self.ai_score)


class ScoreManager:
    """Computes and tracks the game score derived from run statistics.

    Args:
        weights: Optional custom :class:`ScoreWeights`.
    """

    def __init__(self, weights: ScoreWeights | None = None) -> None:
        self.weights = weights or ScoreWeights()
        self.value: int = 0

    def compute(self, stats: StatisticsManager) -> int:
        """Compute (without storing) the score implied by ``stats``."""
        w = self.weights
        score = (
            stats.delivered_count * w.delivery_bonus
            + stats.urgent_delivered_count * w.urgent_delivery_bonus
            + round(stats.satisfaction_score * w.satisfaction_bonus)
            - stats.total_distance * w.move_penalty
            - stats.total_wait * w.wait_penalty
            - stats.angry_count * w.angry_penalty
            - stats.left_count * w.lost_penalty
        )
        return score

    def update(self, stats: StatisticsManager) -> int:
        """Recompute the score from ``stats``, store it, and return it."""
        self.value = self.compute(stats)
        return self.value

    def reset(self) -> None:
        """Reset the stored score to zero."""
        self.value = 0

    def compare(
        self, player_stats: StatisticsManager, ai_stats: StatisticsManager
    ) -> ComparisonResult:
        """Compare a player run against an AI run and report the winner."""
        return ComparisonResult(
            player_score=self.compute(player_stats),
            ai_score=self.compute(ai_stats),
        )
