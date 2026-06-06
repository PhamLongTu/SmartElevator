"""Compare Mode screen: player vs AI on the same scenario, side by side."""

from __future__ import annotations

import pygame

from algorithms.algorithm_factory import AlgorithmFactory
from controllers.compare_mode import CompareMode
from simulation import RandomScenarioGenerator
from views import theme
from views.app import Screen
from views.building_view import BuildingView
from views.widgets import Button


class CompareScreen(Screen):
    """Run a manual player and an AI on one shared scenario; declare a winner."""

    def on_enter(self) -> None:
        generator = RandomScenarioGenerator(
            num_passengers=self.session.passengers, seed=self.session.seed
        )
        self.compare = CompareMode(generator=generator, ai_algorithm=self.session.algorithm)
        self.player_view = BuildingView(pygame.Rect(30, 90, 420, 430), accent=theme.HUMAN)
        self.ai_view = BuildingView(pygame.Rect(830, 90, 420, 430), accent=theme.AI)
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.algo_name = AlgorithmFactory.info(self.session.algorithm).display_name
        self._cooldown = 0.0
        self._done = False

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
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
        self._cooldown -= dt
        if self._cooldown <= 0:
            self._cooldown = 0.18
            if not self.compare.player.finished:
                self.compare.update_player()
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

        # Live head-to-head table.
        report = self.compare.report()
        panel = pygame.Rect(470, 90, 340, 430)
        theme.draw_panel(surface, panel)
        theme.render_text(surface, "HEAD-TO-HEAD", (panel.centerx, panel.y + 16),
                         size=16, color=theme.TEXT, center=True, bold=True)
        headers = [("", "YOU", "AI")]
        rows = [
            ("Wait", f"{report.player_wait:.1f}", f"{report.ai_wait:.1f}"),
            ("Dist", str(report.player_distance), str(report.ai_distance)),
            ("Time", f"{report.player_runtime_ms:.1f}", f"{report.ai_runtime_ms:.1f}"),
            ("Score", str(report.player_score), str(report.ai_score)),
        ]
        cols = [panel.x + 30, panel.x + 170, panel.x + 260]
        y = panel.y + 56
        for label, pv, av in headers + rows:
            color_p = theme.HUMAN if label == "" else theme.TEXT
            theme.render_text(surface, label, (cols[0], y), size=15, color=theme.TEXT_MUTED)
            theme.render_text(surface, pv, (cols[1], y), size=15, color=theme.HUMAN,
                             family="mono", bold=True)
            theme.render_text(surface, av, (cols[2], y), size=15, color=theme.AI,
                             family="mono", bold=True)
            y += 34

        # Controls hint.
        theme.render_text(surface, "Drive with W / S / Space",
                         (panel.centerx, panel.bottom - 60), size=14,
                         color=theme.HUMAN, center=True)
        status = "AI: running..." if not self.compare.ai.finished else "AI: done"
        theme.render_text(surface, status, (panel.centerx, panel.bottom - 36),
                         size=13, color=theme.TEXT_MUTED, center=True)

        if self._done:
            self._draw_winner(surface, report)

    def _draw_winner(self, surface: pygame.Surface, report) -> None:
        overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 9, 20, 200))
        surface.blit(overlay, (0, 0))
        banner = pygame.Rect(theme.WIDTH // 2 - 280, theme.HEIGHT // 2 - 110, 560, 220)
        winner = report.winner
        accent = {"Player": theme.HUMAN, "AI": theme.AI}.get(winner, theme.TEXT_MUTED)
        theme.draw_panel(surface, banner, fill=theme.SURFACE_HI, border=accent, border_w=2)
        title = {"Player": "YOU WIN!", "AI": "AI WINS!"}.get(winner, "TIE")
        theme.render_text(surface, "\U0001F3C6", (banner.centerx, banner.y + 44),
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
