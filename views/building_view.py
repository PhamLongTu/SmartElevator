"""Shared building renderer: elevator shaft, cab, passengers, and HUD panels.

This is the visual heart reused by Manual, AI, and Compare screens -- one
renderer, parameterized by the engine to draw and an accent color, mirroring
the single-:class:`ModeController` architecture on the view side. It also draws
the optional AI "ghost" planned-path overlay (search visualization) and the
real-time statistics / score HUD.
"""

from __future__ import annotations

import pygame

from simulation.simulation_engine import SimulationEngine
from views import theme


class BuildingView:
    """Draws an elevator shaft for one engine within a given rectangle.

    Args:
        rect: The area to draw the shaft within.
        accent: Accent color (cyan for player, amber for AI).
    """

    def __init__(self, rect: pygame.Rect, accent: tuple[int, int, int] = theme.HUMAN) -> None:
        self.rect = pygame.Rect(rect)
        self.accent = accent
        self._cab_y: float | None = None  # smoothed cab pixel position

    def _floor_y(self, floor: int, num_floors: int) -> int:
        """Pixel y of a floor's row center (floor 0 at the bottom)."""
        usable = self.rect.height - 40
        step = usable / max(1, num_floors)
        return int(self.rect.bottom - 20 - step * (floor + 0.5))

    def draw(self, surface: pygame.Surface, engine: SimulationEngine, *,
             planned_floors: list[int] | None = None, title: str = "") -> None:
        """Render the building for ``engine``. ``planned_floors`` draws a ghost path."""
        num_floors = engine.num_floors
        theme.draw_panel(surface, self.rect, fill=theme.BG_BOTTOM)
        if title:
            theme.render_text(surface, title, (self.rect.x + 14, self.rect.y + 8),
                             size=18, color=self.accent, bold=True)

        shaft_x = self.rect.x + 70
        shaft_w = 86
        usable = self.rect.height - 40
        step = usable / max(1, num_floors)

        # Floor rows + labels.
        for floor in range(num_floors):
            y = self._floor_y(floor, num_floors)
            pygame.draw.line(surface, theme.BORDER,
                             (self.rect.x + 50, y + step / 2),
                             (self.rect.right - 14, y + step / 2), 1)
            label = "G" if floor == 0 else f"F{floor}"
            theme.render_text(surface, label, (self.rect.x + 16, y),
                             size=15, color=theme.TEXT_MUTED, center=True)

        # Shaft well.
        shaft_rect = pygame.Rect(shaft_x, self.rect.y + 30, shaft_w, usable)
        pygame.draw.rect(surface, theme.SURFACE, shaft_rect, border_radius=6)
        pygame.draw.rect(surface, theme.BORDER, shaft_rect, width=1, border_radius=6)

        # Ghost planned path (AI search visualization).
        if planned_floors:
            pts = [
                (shaft_x + shaft_w // 2, self._floor_y(f, num_floors))
                for f in planned_floors if 0 <= f < num_floors
            ]
            if len(pts) >= 2:
                pygame.draw.lines(surface, self.accent, False, pts, 2)
            for p in pts:
                pygame.draw.circle(surface, self.accent, p, 4, 1)

        # Waiting passengers (chips to the right of each floor).
        for floor in range(num_floors):
            waiting = engine.building.waiting_at(floor)
            y = self._floor_y(floor, num_floors)
            for i, passenger in enumerate(waiting):
                cx = self.rect.right - 40 - i * 26
                if cx < shaft_x + shaft_w + 20:
                    break
                self._draw_passenger(surface, cx, y, passenger.dest_floor, theme.TEXT_MUTED)

        # The cab (smoothly eased toward its target floor).
        elevator = engine.building.elevator
        target_y = self._floor_y(elevator.current_floor, num_floors)
        if self._cab_y is None:
            self._cab_y = float(target_y)
        else:
            self._cab_y = theme.lerp(self._cab_y, target_y, 0.25)
        cab_h = int(step) - 6
        cab_rect = pygame.Rect(shaft_x + 4, int(self._cab_y) - cab_h // 2, shaft_w - 8, cab_h)
        full = elevator.is_full()
        theme.draw_panel(surface, cab_rect, radius=6,
                        fill=theme.SURFACE_HI,
                        border=theme.WARN if full else self.accent, border_w=2)
        # Occupancy text + onboard destination chips.
        theme.render_text(surface, f"{elevator.occupancy}/{elevator.capacity}",
                         (cab_rect.centerx, cab_rect.y + 12),
                         size=14, color=theme.WARN if full else self.accent,
                         center=True, bold=True)
        for i, passenger in enumerate(elevator.onboard):
            cx = cab_rect.x + 14 + (i % 2) * 26
            cy = cab_rect.centery + 6 + (i // 2) * 18
            self._draw_passenger(surface, cx, cy, passenger.dest_floor, self.accent, small=True)

        # Direction indicator.
        arrow = {1: "▲", -1: "▼"}.get(getattr(elevator.direction, "value", 0), "•")
        theme.render_text(surface, arrow, (cab_rect.centerx, cab_rect.bottom - 10),
                         size=16, color=theme.TEXT, center=True)

    def _draw_passenger(self, surface: pygame.Surface, cx: int, cy: int,
                        dest: int, color: tuple[int, int, int], *, small: bool = False) -> None:
        """Draw a passenger chip: a dot tagged with destination floor."""
        r = 6 if small else 9
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, theme.BG_BOTTOM, (cx, cy), r, 1)
        if not small:
            theme.render_text(surface, str(dest), (cx, cy - 16),
                             size=12, color=theme.TEXT_MUTED, center=True)


def draw_stat_row(surface: pygame.Surface, x: int, y: int, w: int,
                  label: str, value: str, *,
                  color: tuple[int, int, int] = theme.TEXT) -> None:
    """Draw one label/value statistic row (label left, value right, monospace)."""
    theme.render_text(surface, label, (x, y), size=16, color=theme.TEXT_MUTED)
    theme.render_text(surface, value, (x + w, y), size=16, color=color,
                     family="mono", bold=True, right=True)


def draw_hud(surface: pygame.Surface, rect: pygame.Rect, engine: SimulationEngine,
             score: int, *, accent: tuple[int, int, int] = theme.HUMAN,
             extra: list[tuple[str, str]] | None = None) -> None:
    """Draw the real-time statistics + score HUD panel for ``engine``."""
    theme.draw_panel(surface, rect)
    stats = engine.stats
    total = engine.scenario and len(engine.scenario.passengers) or stats.delivered_count
    x, w = rect.x + 18, rect.width - 36
    y = rect.y + 16
    theme.render_text(surface, "LIVE STATS", (x, y), size=14, color=accent, bold=True)
    y += 30
    rows = [
        ("Tick", str(engine.tick)),
        ("Distance", f"{stats.total_distance} floors"),
        ("Avg wait", f"{stats.average_waiting_time:.1f} ticks"),
        ("Delivered", f"{stats.delivered_count} / {total}"),
    ]
    for label, value in rows + (extra or []):
        draw_stat_row(surface, x, y, w, label, value)
        y += 26

    # Score block.
    y += 10
    score_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, 64)
    theme.draw_panel(surface, score_rect, fill=theme.SURFACE_HI, border=theme.GOLD)
    theme.render_text(surface, "SCORE", (score_rect.x + 14, score_rect.y + 10),
                     size=13, color=theme.TEXT_MUTED)
    theme.render_text(surface, f"{score}", (score_rect.centerx, score_rect.centery + 8),
                     size=34, color=theme.GOLD, family="mono", bold=True, center=True)
