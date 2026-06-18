"""Tính điểm game từ các chỉ số thống kê."""

from __future__ import annotations

from dataclasses import dataclass

from statistics.statistics_manager import StatisticsManager


@dataclass
class ScoreWeights:
    """Các trọng số dùng trong công thức điểm."""

    delivery_bonus: int = 100
    urgent_delivery_bonus: int = 200
    satisfaction_bonus: int = 100
    move_penalty: int = 2
    wait_penalty: int = 1
    angry_penalty: int = 100
    lost_penalty: int = 50


@dataclass
class ComparisonResult:
    """Kết quả so sánh điểm hai lượt chạy."""

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
    """Tính và lưu điểm của một lượt chạy."""

    def __init__(self, weights: ScoreWeights | None = None) -> None:
        self.weights = weights or ScoreWeights()
        self.value: int = 0

    def compute(self, stats: StatisticsManager) -> int:
        """Tính điểm từ thống kê mà không lưu lại."""
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
        """Tính lại điểm, lưu và trả về giá trị mới."""
        self.value = self.compute(stats)
        return self.value

    def reset(self) -> None:
        """Đặt điểm về 0."""
        self.value = 0

    def compare(
        self, player_stats: StatisticsManager, ai_stats: StatisticsManager
    ) -> ComparisonResult:
        """So sánh điểm người chơi và AI."""
        return ComparisonResult(
            player_score=self.compute(player_stats),
            ai_score=self.compute(ai_stats),
        )
