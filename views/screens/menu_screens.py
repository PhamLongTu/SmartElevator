"""Menu screens: Main Menu and Mode Selection."""

from __future__ import annotations

import pygame

from views import theme
from views.app import Screen
from views.widgets import Button


class MainMenuScreen(Screen):
    """The landing screen with primary navigation."""

    def on_enter(self) -> None:
        cx = theme.WIDTH // 2
        w, h, gap = 320, 56, 14
        top = 340
        specs = [
            ("PLAY", "mode_select", theme.HUMAN, ""),
            ("BENCHMARK", "benchmark", theme.AI, ""),
            ("QUIT", "__quit__", theme.WARN, ""),
        ]
        self.buttons: list[Button] = []
        for i, (label, target, accent, icon) in enumerate(specs):
            rect = (cx - w // 2, top + i * (h + gap), w, h)
            self.buttons.append(
                Button(rect, label, self._make_nav(target), accent=accent, icon=icon)
            )
        self._t = 0.0

    def _make_nav(self, target: str):
        def nav() -> None:
            if target == "__quit__":
                self.app.running = False
            else:
                self.app.go_to(target)
        return nav

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle(event)

    def update(self, dt: float) -> None:
        self._t += dt

    def draw(self, surface: pygame.Surface) -> None:
        cx = theme.WIDTH // 2
        theme.render_text(surface, "SMART ELEVATOR", (cx, 150),
                         size=72, color=theme.TEXT, family="display", bold=True, center=True)
        theme.render_text(surface, "AI DISPATCH SIMULATION", (cx, 210),
                         size=22, color=theme.HUMAN, center=True)
        # Pulsing accent underline.
        import math
        glow = int(120 + 80 * abs(math.sin(self._t * 1.5)))
        pygame.draw.line(surface, (glow, 180, 200), (cx - 180, 240), (cx + 180, 240), 2)
        for b in self.buttons:
            b.draw(surface)
        theme.render_text(surface, "Building: 7 floors  -  1 elevator  -  capacity 4",
                         (cx, theme.HEIGHT - 40), size=15, color=theme.TEXT_MUTED, center=True)


class ModeSelectScreen(Screen):
    """Choose Manual, AI, or Compare; configure the shared scenario."""

    def on_enter(self) -> None:
        self.cards = [
            ("MANUAL", "manual", theme.HUMAN, "",
             ["Drive the cab yourself.", "", "Up / Down arrow keys", "move the cab.", "Space opens the door."]),
            ("AI", "ai", theme.AI, "",
             ["Watch a search algorithm", "solve the dispatch", "problem.", "", "Pick 1 of 7 algorithms."]),
            ("COMPARE", "compare", theme.WIN, "",
             ["You vs the AI on the", "SAME scenario.", "", "Head-to-head metrics", "and a winner."]),
        ]
        cw, ch = 300, 320
        gap = 40
        total = cw * 3 + gap * 2
        x0 = (theme.WIDTH - total) // 2
        y0 = 180
        self.card_rects = [
            pygame.Rect(x0 + i * (cw + gap), y0, cw, ch) for i in range(3)
        ]
        self.select_buttons = [
            Button((r.x + 60, r.bottom - 60, r.width - 120, 44), "SELECT",
                   self._make_nav(self.cards[i][1]), accent=self.cards[i][2])
            for i, r in enumerate(self.card_rects)
        ]
        # Scenario setup controls.
        self.back = Button((30, 30, 120, 44), "Back", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.minus = Button((theme.WIDTH // 2 - 40, 560, 44, 44), "-",
                            self._dec, accent=theme.HUMAN)
        self.plus = Button((theme.WIDTH // 2 + 80, 560, 44, 44), "+",
                           self._inc, accent=theme.HUMAN)

    def _make_nav(self, target: str):
        return lambda: self.app.go_to(target)

    def _dec(self) -> None:
        self.session.passengers = max(1, self.session.passengers - 1)

    def _inc(self) -> None:
        self.session.passengers = min(12, self.session.passengers + 1)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        self.minus.handle(event)
        self.plus.handle(event)
        for b in self.select_buttons:
            b.handle(event)

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "SELECT MODE", (theme.WIDTH // 2, 90),
                         size=44, color=theme.TEXT, family="display", bold=True, center=True)
        self.back.draw(surface)
        for i, rect in enumerate(self.card_rects):
            label, _, accent, icon, lines = self.cards[i]
            theme.draw_panel(surface, rect, border=accent)
            theme.render_text(surface, icon, (rect.centerx, rect.y + 50),
                             size=48, color=accent, center=True)
            theme.render_text(surface, label, (rect.centerx, rect.y + 110),
                             size=26, color=accent, bold=True, center=True)
            for j, line in enumerate(lines):
                theme.render_text(surface, line, (rect.centerx, rect.y + 150 + j * 24),
                                 size=15, color=theme.TEXT_MUTED, center=True)
            self.select_buttons[i].draw(surface)
        # Scenario setup strip.
        theme.render_text(surface, "Passengers", (theme.WIDTH // 2 - 55, 572),
                         size=18, color=theme.TEXT, right=True)
        theme.render_text(surface, str(self.session.passengers),
                         (theme.WIDTH // 2 + 42, 582), size=28, color=theme.HUMAN,
                         family="mono", bold=True, center=True)
        self.minus.draw(surface)
        self.plus.draw(surface)
        theme.render_text(surface, f"Seed {self.session.seed}",
                         (theme.WIDTH // 2, 630), size=16, color=theme.TEXT_MUTED, center=True)
