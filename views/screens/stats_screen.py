"""Statistics Dashboard: post-run metrics for the last completed mode."""

from __future__ import annotations

import pygame

from views import theme
from views.app import Screen
from views.building_view import draw_stat_row
from views.widgets import Button


class StatsScreen(Screen):
    """Shows search-quality and outcome metrics for the last run."""

    def on_enter(self) -> None:
        self.back = Button((30, 30, 110, 40), "Menu", lambda: self.app.go_to("main"),
                           accent=theme.TEXT_MUTED)
        self.again = Button((1120, 30, 130, 40), "Play Again",
                            lambda: self.app.go_to(self.session.last_mode), accent=theme.WIN)
        self.engine = self.session.last_engine
        self.score = getattr(self.session, "last_score", 0)

    def handle_event(self, event: pygame.event.Event) -> None:
        self.back.handle(event)
        self.again.handle(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go_to("main")

    def draw(self, surface: pygame.Surface) -> None:
        theme.render_text(surface, "STATISTICS", (theme.WIDTH // 2, 50),
                         size=36, color=theme.TEXT, family="display", bold=True, center=True)
        self.back.draw(surface)
        self.again.draw(surface)

        if self.engine is None:
            theme.render_text(surface, "No run yet. Play a mode to see statistics.",
                             (theme.WIDTH // 2, theme.HEIGHT // 2), size=20,
                             color=theme.TEXT_MUTED, center=True)
            return

        stats = self.engine.stats
        theme.render_text(surface, f"Last run:  {self.session.last_label}",
                         (theme.WIDTH // 2, 96), size=16, color=theme.TEXT_MUTED, center=True)

        # Search quality panel (planning phase)
        left = pygame.Rect(60, 140, 560, 240)
        theme.draw_panel(surface, left)
        theme.render_text(surface, "SEARCH QUALITY (planning)", (left.x + 20, left.y + 16),
                         size=15, color=theme.AI, bold=True)
        if stats.planning_time > 0 or stats.nodes_expanded > 0:
            rows = [
                ("Runtime", f"{stats.planning_time:.3f} ms"),
                ("Nodes expanded", str(stats.nodes_expanded)),
                ("Nodes generated", str(stats.nodes_generated)),
                ("Solution cost", f"{stats.solution_cost:.1f}"),
            ]
        else:
            rows = [
                ("Mode", "Manual (No search)"),
                ("Runtime", "N/A"),
                ("Complexity", "None"),
                ("Solution", "User-driven"),
            ]
        for i, (label, value) in enumerate(rows):
            draw_stat_row(surface, left.x + 20, left.y + 56 + i * 38, left.width - 40,
                          label, value, color=theme.AI)

        # Outcome panel (execution phase)
        right = pygame.Rect(660, 140, 560, 240)
        theme.draw_panel(surface, right)
        theme.render_text(surface, "OUTCOME (execution)", (right.x + 20, right.y + 16),
                         size=15, color=theme.WIN, bold=True)
        total = len(self.engine.scenario.passengers) if self.engine.scenario else stats.delivered_count
        orows = [
            ("Travel distance", f"{stats.total_distance} units"),
            ("Avg waiting time", f"{stats.average_waiting_time:.2f}"),
            ("Delivered", f"{stats.delivered_count} / {total} ({stats.urgent_delivered_count}U)"),
            ("Failures (L/A)", f"{stats.left_count} / {stats.angry_count}"),
        ]
        for i, (label, value) in enumerate(orows):
            draw_stat_row(surface, right.x + 20, right.y + 56 + i * 38, right.width - 40,
                          label, value, color=theme.WIN)

        # Satisfaction gauge
        sat = pygame.Rect(60, 400, 560, 250)
        theme.draw_panel(surface, sat)
        theme.render_text(surface, "SATISFACTION", (sat.x + 20, sat.y + 16),
                         size=15, color=theme.HUMAN, bold=True)
        pct = stats.satisfaction_score
        cx, cy, r = sat.centerx, sat.centery + 20, 70
        pygame.draw.circle(surface, theme.SURFACE_HI, (cx, cy), r)
        
        import math
        end = -math.pi / 2 + 2 * math.pi * pct
        pts = [(cx, cy)]
        steps = max(2, int(60 * pct))
        for i in range(steps + 1):
            a = -math.pi / 2 + (end + math.pi / 2) * i / steps
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        if len(pts) >= 3:
            pygame.draw.polygon(surface, theme.HUMAN, pts)
        theme.render_text(surface, f"{pct * 100:.1f}%", (cx, cy),
                         size=28, color=theme.TEXT, family="mono", bold=True, center=True)

        # Per-passenger waiting times
        waits = pygame.Rect(660, 400, 560, 250)
        theme.draw_panel(surface, waits)
        theme.render_text(surface, "WAITING TIME PER PASSENGER", (waits.x + 20, waits.y + 16),
                         size=15, color=theme.WARN, bold=True)
        delivered = getattr(self.engine, "delivered_passengers", [])
        if delivered:
            max_wait = max((p.current_wait_time or 0) for p in delivered) or 1
            bar_w = waits.width - 120
            for i, p in enumerate(delivered[:6]):
                y = waits.y + 56 + i * 30
                w = p.current_wait_time
                theme.render_text(surface, f"F{p.origin_floor}", (waits.x + 20, y), size=14,
                                 color=theme.TEXT_MUTED)
                bar = pygame.Rect(waits.x + 60, y + 2, int(bar_w * w / max_wait), 16)
                pygame.draw.rect(surface, theme.WARN, bar, border_radius=4)
                theme.render_text(surface, f"{w:.1f}", (waits.right - 30, y), size=14,
                                 color=theme.TEXT, family="mono", right=True)
 
        # Score Panel
        score_panel = pygame.Rect(theme.WIDTH // 2 - 140, 20, 280, 50)
        theme.draw_panel(surface, score_panel, fill=theme.SURFACE_HI, border=theme.WIN)
        theme.render_text(surface, f"FINAL SCORE: {self.score}", score_panel.center,
                         size=24, color=theme.WIN, bold=True, center=True)
