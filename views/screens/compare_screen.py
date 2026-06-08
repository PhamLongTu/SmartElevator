"""Compare Mode screen: player vs AI on the same scenario, side by side."""

from __future__ import annotations

import pygame

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.compare_mode import CompareMode
from simulation import RandomScenarioGenerator
from views import theme
from views.app import Screen
from views.building_view import BuildingView
from views.widgets import Button, Dropdown


class CompareScreen(Screen):
    """Run a manual player and an AI on one shared scenario; declare a winner."""

    def on_enter(self) -> None:
        self.generator = RandomScenarioGenerator(
            num_passengers=self.session.passengers, seed=self.session.seed
        )
        # Algorithm choices for the AI side.
        self.algo_keys = AlgorithmFactory.available()
        self.algo_labels = [AlgorithmFactory.info(k).display_name for k in self.algo_keys]
        self.algo_index = self.algo_keys.index(self.session.algorithm) \
            if self.session.algorithm in self.algo_keys else self.algo_keys.index("astar")

        self.player_view = BuildingView(pygame.Rect(30, 90, 420, 430), accent=theme.HUMAN)
        self.ai_view = BuildingView(pygame.Rect(830, 90, 420, 430), accent=theme.AI)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)

        # Setup controls (shown before the run starts).
        self.dropdown = Dropdown((485, 200, 310, 40), self.algo_labels,
                                 index=self.algo_index, on_change=self._select_algo,
                                 accent=theme.AI)
        self.start_btn = Button((560, 300, 160, 44), "START", self._start, accent=theme.WIN)

        self.started = False
        self._cooldown = 0.0       # player stepping cadence
        self._ai_cooldown = 0.0    # AI stepping cadence (slower)
        self._done = False
        self._build_compare()

    def _build_compare(self) -> None:
        """(Re)build the comparison with the currently selected AI algorithm."""
        self.session.algorithm = self.algo_keys[self.algo_index]
        self.algo_name = self.algo_labels[self.algo_index]
        self.compare = CompareMode(generator=self.generator,
                                   ai_algorithm=self.session.algorithm)
        self._cooldown = 0.0
        self._ai_cooldown = 0.0

    def _select_algo(self, index: int) -> None:
        self.algo_index = index
        self._build_compare()

    def _start(self) -> None:
        """Begin the head-to-head run with the selected algorithm."""
        self.started = True

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        if not self.started:
            self.dropdown.handle(event)
            self.start_btn.handle(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.app.go_to("main")
            return
        # Once finished, the winner banner's "View Stats" button is active.
        if self._done and hasattr(self, "stats_btn"):
            self.stats_btn.handle(event)
        if event.type == pygame.KEYDOWN:
            action = self.compare.player.input.from_pygame_key(event.key)
            if action is not None:
                self.compare.player.queue_action(action)
            elif event.key == pygame.K_ESCAPE:
                self.app.go_to("main")

    def update(self, dt: float) -> None:
        if not self.started:
            return
        self._cooldown -= dt
        if self._cooldown <= 0:
            self._cooldown = 0.18
            if not self.compare.player.finished:
                self.compare.update_player()
        # AI steps slower than the player.
        self._ai_cooldown -= dt
        if self._ai_cooldown <= 0:
            self._ai_cooldown = 0.54
            if not self.compare.ai.finished:
                self.compare.update_ai()
        if self.compare.finished and not self._done:
            self._done = True
            report = self.compare.report()
            self.session.last_engine = self.compare.ai_engine
            self.session.last_score = report.ai_score
            self.session.last_label = f"Compare (AI {self.algo_name})"

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "COMPARE MODE", (theme.WIDTH // 2, 50),
                         size=30, color=theme.WIN, family="display", bold=True, center=True)
        theme.render_text(surface, f"same scenario - seed {self.session.seed}",
                         (theme.WIDTH // 2, 78), size=14, color=theme.TEXT_MUTED, center=True)
        self.back.draw(surface)
        self.player_view.draw(surface, self.compare.player_engine, title="YOU (Manual)")
        self.ai_view.draw(surface, self.compare.ai_engine, title=f"AI ({self.algo_name})")

        panel = pygame.Rect(470, 90, 340, 430)
        theme.draw_panel(surface, panel)

        if not self.started:
            self._draw_setup(surface, panel)
        else:
            self._draw_scoreboard(surface, panel)

        if self._done:
            self._draw_winner(surface, self.compare.report())

    def _draw_setup(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        """Pre-run panel: choose the AI's algorithm, then START."""
        theme.render_text(surface, "AI ALGORITHM", (panel.centerx, panel.y + 30),
                         size=18, color=theme.AI, center=True, bold=True)
        theme.render_text(surface, "Choose the search algorithm the",
                         (panel.centerx, panel.y + 62), size=13,
                         color=theme.TEXT_MUTED, center=True)
        theme.render_text(surface, "AI will use, then press START.",
                         (panel.centerx, panel.y + 80), size=13,
                         color=theme.TEXT_MUTED, center=True)
        self.start_btn.draw(surface)
        theme.render_text(surface, "You drive with arrow keys + Space",
                         (panel.centerx, panel.bottom - 40), size=14,
                         color=theme.HUMAN, center=True)
        # Dropdown last so its expanded list renders on top.
        self.dropdown.draw(surface)
        self.dropdown.draw_overlay(surface)

    def _draw_scoreboard(self, surface: pygame.Surface, panel: pygame.Rect) -> None:
        """Live head-to-head table during the run."""
        report = self.compare.report()
        theme.render_text(surface, "HEAD-TO-HEAD", (panel.centerx, panel.y + 16),
                         size=16, color=theme.TEXT, center=True, bold=True)
        headers = [("", "YOU", "AI")]
        rows = [
            ("Wait", f"{report.player_wait:.1f}", f"{report.ai_wait:.1f}"),
            ("Dist", str(report.player_distance), str(report.ai_distance)),
            ("Urgent", str(report.player_urgent), str(report.ai_urgent)),
            ("Fail", report.player_failures, report.ai_failures),
            ("Score", str(report.player_score), str(report.ai_score)),
        ]
        cols = [panel.x + 30, panel.x + 170, panel.x + 260]
        y = panel.y + 46
        for label, pv, av in headers + rows:
            theme.render_text(surface, label, (cols[0], y), size=15, color=theme.TEXT_MUTED)
            theme.render_text(surface, pv, (cols[1], y), size=15, color=theme.HUMAN,
                             family="mono", bold=True)
            theme.render_text(surface, av, (cols[2], y), size=15, color=theme.AI,
                             family="mono", bold=True)
            y += 32

        theme.render_text(surface, "Drive with arrow keys + Space",
                         (panel.centerx, panel.bottom - 60), size=14,
                         color=theme.HUMAN, center=True)
        status = "AI: running..." if not self.compare.ai.finished else "AI: done"
        theme.render_text(surface, status, (panel.centerx, panel.bottom - 36),
                         size=13, color=theme.TEXT_MUTED, center=True)

    def _draw_winner(self, surface: pygame.Surface, report) -> None:
        overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 9, 20, 200))
        surface.blit(overlay, (0, 0))
        banner = pygame.Rect(theme.WIDTH // 2 - 280, theme.HEIGHT // 2 - 110, 560, 220)
        winner = report.winner
        accent = {"Player": theme.HUMAN, "AI": theme.AI}.get(winner, theme.TEXT_MUTED)
        theme.draw_panel(surface, banner, fill=theme.SURFACE_HI, border=accent, border_w=2)
        title = {"Player": "YOU WIN!", "AI": "AI WINS!"}.get(winner, "TIE")
        theme.render_text(surface, "\u2605", (banner.centerx, banner.y + 44),
                         size=40, color=theme.GOLD, center=True)
        theme.render_text(surface, title, (banner.centerx, banner.y + 96),
                         size=40, color=accent, family="display", bold=True, center=True)
        sub = f"by {report.margin} points" if report.margin else "dead heat"
        theme.render_text(surface, sub, (banner.centerx, banner.y + 140),
                         size=18, color=theme.TEXT_MUTED, center=True)
        theme.render_text(surface, "Press Esc for Menu  -  click Stats below",
                         (banner.centerx, banner.bottom - 26), size=14,
                         color=theme.TEXT_MUTED, center=True)
        if not hasattr(self, "stats_btn"):
            self.stats_btn = Button((banner.centerx - 80, banner.bottom + 10, 160, 40),
                                    "View Stats", lambda: self.app.go_to("stats"),
                                    accent=theme.WIN)
        self.stats_btn.draw(surface)

    def handle_event_late(self, event: pygame.event.Event) -> None:  # pragma: no cover
        if self._done and hasattr(self, "stats_btn"):
            self.stats_btn.handle(event)
