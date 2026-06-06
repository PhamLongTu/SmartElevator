"""Benchmark Results dashboard: run all 7 algorithms and tabulate."""

from __future__ import annotations

import threading

import pygame

from statistics.benchmark_manager import BenchmarkManager
from views import theme
from views.app import Screen
from views.widgets import Button, Tabs


# Seed groups per difficulty, mirroring the 30-scenario dataset bands.
_DIFFICULTY = {
    "Easy": dict(num_passengers=3, seeds=(101, 103, 105, 107, 109)),
    "Medium": dict(num_passengers=6, seeds=(201, 203, 205, 207, 209)),
    "Hard": dict(num_passengers=10, seeds=(301, 303, 305, 307, 309)),
}
_TABS = ["Easy", "Medium", "Hard"]


class BenchmarkScreen(Screen):
    """Runs the BenchmarkManager (in a thread) and renders comparison results."""

    def on_enter(self) -> None:
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.run_btn = Button((1060, 30, 190, 40), "Run Benchmark", self._start_run,
                              accent=theme.AI)
        self.tabs = Tabs((400, 86, 480, 40), _TABS, index=0, on_change=self._on_tab)
        self.difficulty = "Easy"
        self.results: dict[str, dict] = {}   # difficulty -> {key: AlgorithmBenchmark}
        self._thread: threading.Thread | None = None
        self._running = False

    def _on_tab(self, index: int) -> None:
        self.difficulty = _TABS[index]

    def _start_run(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_all, daemon=True)
        self._thread.start()

    def _run_all(self) -> None:
        for name, cfg in _DIFFICULTY.items():
            mgr = BenchmarkManager(num_passengers=cfg["num_passengers"], seeds=cfg["seeds"])
            self.results[name] = mgr.run()
        self._running = False

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        self.run_btn.handle(event)
        self.tabs.handle(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_to("main")

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "BENCHMARK RESULTS", (theme.WIDTH // 2, 50),
                         size=32, color=theme.AI, family="display", bold=True, center=True)
        self.back.draw(surface)
        self.run_btn.draw(surface)
        self.tabs.draw(surface)
        theme.render_text(surface, "30-scenario dataset  -  10 Easy / 10 Medium / 10 Hard",
                         (theme.WIDTH // 2, 150), size=14, color=theme.TEXT_MUTED, center=True)

        if self._running:
            theme.render_text(surface, "Running benchmark...",
                             (theme.WIDTH // 2, theme.HEIGHT // 2), size=24,
                             color=theme.AI, center=True)
            return
        if self.difficulty not in self.results:
            theme.render_text(surface, "Press 'Run Benchmark' to evaluate all 7 algorithms.",
                             (theme.WIDTH // 2, theme.HEIGHT // 2), size=20,
                             color=theme.TEXT_MUTED, center=True)
            return

        self._draw_table(surface, self.results[self.difficulty])

    def _draw_table(self, surface: pygame.Surface, data: dict) -> None:
        panel = pygame.Rect(60, 180, 1160, 300)
        theme.draw_panel(surface, panel)
        cols = ["Algorithm", "Success", "AvgCost", "Expanded", "Runtime", "AvgWait", "Sat%"]
        col_x = [panel.x + 20, panel.x + 320, panel.x + 460, panel.x + 600,
                 panel.x + 760, panel.x + 900, panel.x + 1040]
        for cx, name in zip(col_x, cols):
            theme.render_text(surface, name, (cx, panel.y + 16), size=15,
                             color=theme.TEXT_MUTED, bold=True)
        pygame.draw.line(surface, theme.BORDER, (panel.x + 14, panel.y + 44),
                         (panel.right - 14, panel.y + 44), 1)

        # Best-per-column highlighting.
        best_expanded = min((b.avg_expanded for b in data.values() if b.successes), default=0)
        for i, b in enumerate(data.values()):
            y = panel.y + 56 + i * 32
            recommended = b.key == "astar"
            name_color = theme.AI if recommended else theme.TEXT
            star = " *" if recommended else ""
            theme.render_text(surface, b.display_name + star, (col_x[0], y), size=15,
                             color=name_color, bold=recommended)
            succ_color = theme.WIN if b.successes == b.runs else theme.WARN
            vals = [
                (f"{b.successes}/{b.runs}", succ_color),
                (f"{b.avg_cost:.1f}", theme.TEXT),
                (f"{b.avg_expanded:.0f}",
                 theme.WIN if b.avg_expanded == best_expanded and b.successes else theme.TEXT),
                (f"{b.avg_runtime_ms:.2f}", theme.TEXT),
                (f"{b.avg_wait:.2f}", theme.TEXT),
                (f"{b.avg_satisfaction * 100:.1f}", theme.TEXT),
            ]
            for cx, (text, color) in zip(col_x[1:], vals):
                theme.render_text(surface, text, (cx, y), size=15, color=color, family="mono")

        # Nodes-expanded bar chart.
        chart = pygame.Rect(60, 500, 1160, 170)
        theme.draw_panel(surface, chart)
        theme.render_text(surface, "NODES EXPANDED (lower is better)",
                         (chart.x + 20, chart.y + 12), size=14, color=theme.AI, bold=True)
        max_exp = max((b.avg_expanded for b in data.values()), default=1) or 1
        bar_x = chart.x + 140
        bar_max_w = chart.width - 280
        for i, b in enumerate(data.values()):
            y = chart.y + 44 + i * 17
            theme.render_text(surface, b.display_name[:14], (chart.x + 20, y - 2),
                             size=12, color=theme.TEXT_MUTED)
            w = int(bar_max_w * b.avg_expanded / max_exp)
            color = theme.WIN if b.key == "astar" else theme.AI
            pygame.draw.rect(surface, color, pygame.Rect(bar_x, y, max(2, w), 11),
                             border_radius=3)
            theme.render_text(surface, f"{b.avg_expanded:.0f}", (bar_x + w + 8, y - 2),
                             size=12, color=theme.TEXT)
