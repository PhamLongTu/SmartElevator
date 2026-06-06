"""Measurement and scoring package for the Smart Elevator game.

Note: :class:`~statistics.benchmark_manager.BenchmarkManager` is intentionally
NOT re-exported here. It depends on the ``algorithms`` layer, which in turn
imports this package -- eagerly importing it would create a circular import.
Import it directly: ``from statistics.benchmark_manager import BenchmarkManager``.
"""

from statistics.score_manager import ComparisonResult, ScoreManager, ScoreWeights
from statistics.statistics_manager import StatisticsManager

__all__ = [
    "StatisticsManager",
    "ScoreManager",
    "ScoreWeights",
    "ComparisonResult",
]
