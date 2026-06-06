"""Screen implementations for the Smart Elevator UI."""

from views.screens.benchmark_screen import BenchmarkScreen
from views.screens.compare_screen import CompareScreen
from views.screens.menu_screens import MainMenuScreen, ModeSelectScreen
from views.screens.play_screens import AIScreen, ManualScreen
from views.screens.stats_screen import StatsScreen

#: Maps the screen names used by App.go_to to their classes.
SCREEN_REGISTRY = {
    "main": MainMenuScreen,
    "mode_select": ModeSelectScreen,
    "manual": ManualScreen,
    "ai": AIScreen,
    "compare": CompareScreen,
    "stats": StatsScreen,
    "benchmark": BenchmarkScreen,
}

__all__ = [
    "SCREEN_REGISTRY",
    "MainMenuScreen",
    "ModeSelectScreen",
    "ManualScreen",
    "AIScreen",
    "CompareScreen",
    "StatsScreen",
    "BenchmarkScreen",
]
