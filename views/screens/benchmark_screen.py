"""Màn hình benchmark so sánh các thuật toán."""

from __future__ import annotations

import threading

import pygame

from statistics.benchmark_manager import BenchmarkManager
from views import theme
from views.app import Screen
from views.widgets import Button, Tabs


_TABS = ["Easy", "Medium", "Hard"]
_DIFFICULTY_DETAILS = {
    "Easy": "2-4 passengers per scenario",
    "Medium": "5-8 passengers per scenario",
    "Hard": "10-16 passengers per scenario",
}


class BenchmarkScreen(Screen):
    """Chạy benchmark trong thread riêng và hiển thị kết quả."""

    def on_enter(self) -> None:
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.run_btn = Button((1060, 30, 190, 40), "Run Benchmark", self._start_run,
                              accent=theme.AI)
        self.tabs = Tabs((400, 86, 480, 40), _TABS, index=0, on_change=self._on_tab)
        self.difficulty = "Easy"
        self.results: dict[str, dict] = {}
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
        for name in _TABS:
            mgr = BenchmarkManager(difficulty=name)
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
        detail = _DIFFICULTY_DETAILS.get(self.difficulty, "")
        theme.render_text(surface, f"{self.difficulty}: {detail}; values are averages across 10 scenarios",
                         (theme.WIDTH // 2, 170), size=12, color=theme.TEXT_MUTED, center=True)

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

    def _find_best_algorithms(self, data: dict) -> dict:
        """
        Find the best algorithm for each metric.
        
        Returns:
            dict with keys: 'score', 'expanded', 'generated', 'runtime', 'wait', 'satisfaction'
        """
        if not data:
            return {}
        
        best = {}
        algorithms = list(data.values())
        complete = [b for b in algorithms if b.successes == b.runs]
        successful = [b for b in algorithms if b.successes > 0]
        eligible = complete or successful or algorithms
        
        best['score'] = max(algorithms, key=lambda b: b.avg_score).key
        
        best['expanded'] = min(eligible, key=lambda b: b.avg_expanded).key

        best['generated'] = min(eligible, key=lambda b: b.avg_generated).key
        
        best['runtime'] = min(eligible, key=lambda b: b.avg_runtime_ms).key
        
        best['wait'] = min(eligible, key=lambda b: b.avg_wait).key
        
        best['satisfaction'] = max(eligible, key=lambda b: b.avg_satisfaction).key
        
        return best

    def _draw_table(self, surface: pygame.Surface, data: dict) -> None:
        """Vẽ bảng kết quả benchmark."""
        best = self._find_best_algorithms(data)
        
        panel = pygame.Rect(60, 180, 1160, 292)
        theme.draw_panel(surface, panel)
        
        cols = [
            ("Algorithm", None),
            ("Scenarios", None),
            ("Score", "high"),
            ("AvgExpanded", "low"),
            ("Generated", "low"),
            ("Runtime", "low"),
            ("AvgWait", "low"),
            ("Sat%", "high"),
        ]
        col_x = [panel.x + 20, panel.x + 300, panel.x + 420, panel.x + 535,
                 panel.x + 680, panel.x + 820, panel.x + 950, panel.x + 1070]
        
        for idx, ((name, indicator), cx) in enumerate(zip(cols, col_x)):
            text = name
            if indicator:
                text += f" ({indicator})"
            theme.render_text(surface, text, (cx, panel.y + 16), size=13,
                             color=theme.TEXT_MUTED, bold=True,
                             max_width=(col_x[idx + 1] - cx - 12) if idx + 1 < len(col_x) else 110)
        
        pygame.draw.line(surface, theme.BORDER, (panel.x + 14, panel.y + 44),
                         (panel.right - 14, panel.y + 44), 1)

        for i, b in enumerate(data.values()):
            y = panel.y + 56 + i * 32
            
            is_best_score = b.key == best.get('score')
            is_best_expanded = b.key == best.get('expanded')
            is_best_generated = b.key == best.get('generated')
            is_best_runtime = b.key == best.get('runtime')
            is_best_wait = b.key == best.get('wait')
            is_best_satisfaction = b.key == best.get('satisfaction')
            
            is_highlighted = (
                is_best_score or is_best_expanded or is_best_generated
                or is_best_runtime or is_best_wait or is_best_satisfaction
            )

            if is_best_score:
                row_rect = pygame.Rect(panel.x + 12, y - 4, panel.width - 24, 26)
                row_surf = pygame.Surface(row_rect.size, pygame.SRCALPHA)
                row_surf.fill((theme.GOLD[0], theme.GOLD[1], theme.GOLD[2], 28))
                surface.blit(row_surf, row_rect.topleft)
                pygame.draw.rect(surface, theme.GOLD, row_rect, width=1, border_radius=6)

            if is_highlighted:
                name_color = theme.GOLD if is_best_score else theme.AI
            else:
                name_color = theme.TEXT
            
            theme.render_text(surface, b.display_name, (col_x[0], y), size=15,
                             color=name_color, bold=is_highlighted,
                             max_width=col_x[1] - col_x[0] - 24)
            
            succ_color = theme.WIN if b.successes == b.runs else theme.WARN
            vals = [
                (f"{b.successes}/{b.runs}", succ_color),
                (f"{b.avg_score:.0f}", theme.GOLD if is_best_score else theme.TEXT),
                (f"{b.avg_expanded:.0f}", theme.GREEN if is_best_expanded else theme.TEXT),
                (f"{b.avg_generated:.0f}", theme.GREEN if is_best_generated else theme.TEXT),
                (f"{b.avg_runtime_ms:.2f}", theme.GREEN if is_best_runtime else theme.TEXT),
                (f"{b.avg_wait:.2f}", theme.GREEN if is_best_wait else theme.TEXT),
                (f"{b.avg_satisfaction * 100:.1f}", theme.GOLD if is_best_satisfaction else theme.TEXT),
            ]
            
            for cx, (text, color) in zip(col_x[1:], vals):
                theme.render_text(surface, text, (cx, y), size=15, color=color, family="mono")
        
        legend_y = panel.bottom + 8
        theme.render_text(surface, "Gold row: best score", (panel.x + 20, legend_y), size=12, color=theme.GOLD)
        theme.render_text(surface, "Green values: best low metric", (panel.x + 210, legend_y), size=12, color=theme.GREEN)
        theme.render_text(surface, "Gold values: best high metric", (panel.x + 470, legend_y), size=12, color=theme.GOLD)

        chart = pygame.Rect(60, 515, 1160, 160)
        theme.draw_panel(surface, chart)
        theme.render_text(surface, "AVG NODES EXPANDED PER SCENARIO (lower is better)",
                         (chart.x + 20, chart.y + 12), size=14, color=theme.AI, bold=True)
        
        algorithms = list(data.values())
        best_expanded_key = (
            min(algorithms, key=lambda b: b.avg_expanded).key
            if algorithms else None
        )
        
        max_exp = max((b.avg_expanded for b in data.values()), default=1) or 1
        bar_x = chart.x + 140
        bar_max_w = chart.width - 280
        
        for i, b in enumerate(data.values()):
            y = chart.y + 44 + i * 17
            
            is_best_in_chart = b.key == best_expanded_key
            name_color = theme.GOLD if is_best_in_chart else theme.TEXT_MUTED
            
            theme.render_text(surface, b.display_name[:14], (chart.x + 20, y - 2),
                             size=12, color=name_color, bold=is_best_in_chart)
            
            w = int(bar_max_w * b.avg_expanded / max_exp)
            
            color = theme.GOLD if is_best_in_chart else theme.AI
            
            pygame.draw.rect(surface, color, pygame.Rect(bar_x, y, max(2, w), 11),
                             border_radius=3)
            
            text_color = theme.GOLD if is_best_in_chart else theme.TEXT
            theme.render_text(surface, f"{b.avg_expanded:.0f}", (bar_x + w + 8, y - 2),
                             size=12, color=text_color, bold=is_best_in_chart)
