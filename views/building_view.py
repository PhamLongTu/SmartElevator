"""Shared building renderer: elevator shaft, cab, passengers, and HUD panels.

This is the visual heart reused by Manual, AI, and Compare screens -- one
renderer, parameterized by the engine to draw and an accent color, mirroring
the single-:class:`ModeController` architecture on the view side. It also draws
the optional AI "ghost" planned-path overlay (search visualization) and the
real-time statistics / score HUD.
"""

from __future__ import annotations

import pygame

from models.passenger import Passenger
from simulation.simulation_engine import SimulationEngine
from views import theme


class BuildingView:
    """Draws an elevator shaft for one engine within a given rectangle.

    Args:
        rect: The area to draw the shaft within.
        accent: Accent color (cyan for player, amber for AI).
    """

    # Padding that keeps the shaft below the title and above the bottom edge.
    _TOP_PAD = 40
    _BOT_PAD = 20

    def __init__(self, rect: pygame.Rect, accent: tuple[int, int, int] = theme.HUMAN) -> None:
        self.rect = pygame.Rect(rect)
        self.accent = accent
        self._cab_y: float | None = None  # smoothed cab pixel position

    def _floor_y(self, floor: int, num_floors: int) -> int:
        """Pixel y of a floor's row center (floor 0 at the bottom)."""
        usable = self.rect.height - self._TOP_PAD - self._BOT_PAD
        step = usable / max(1, num_floors)
        return int(self.rect.bottom - self._BOT_PAD - step * (floor + 0.5))

    def draw(self, surface: pygame.Surface, engine: SimulationEngine, *,
             planned_floors: list[int] | None = None, title: str = "") -> None:
        """Render the building for ``engine``. ``planned_floors`` draws a ghost path."""
        num_floors = engine.num_floors
        theme.draw_panel(surface, self.rect, fill=theme.BG_BOTTOM)

        shaft_x = self.rect.x + 60
        shaft_w = 140
        usable = self.rect.height - self._TOP_PAD - self._BOT_PAD
        step = usable / max(1, num_floors)

        # Current elevator floor for highlighting
        curr_f = engine.building.elevator.current_floor

        # Floor rows + labels.
        for floor in range(num_floors):
            y = self._floor_y(floor, num_floors)
            pygame.draw.line(surface, theme.BORDER,
                             (self.rect.x + 50, y + step / 2),
                             (self.rect.right - 14, y + step / 2), 1)
            
            is_active = (floor == curr_f)
            label = "G" if floor == 0 else f"F{floor}"
            color = self.accent if is_active else theme.TEXT_MUTED
            
            # Floor label
            theme.render_text(surface, label, (self.rect.x + 18, y),
                             size=16 if is_active else 15, color=color, 
                             center=True, bold=is_active)
            
            # Active floor beacon
            if is_active:
                # Pulsing beacon
                import math
                pulse = (math.sin(engine.time * 8) + 1) / 2
                r = 4 + 2 * pulse
                pygame.draw.circle(surface, self.accent, (self.rect.x + 40, y), r)
                pygame.draw.circle(surface, theme.BG_BOTTOM, (self.rect.x + 40, y), r, 1)

        # Shaft well.
        shaft_rect = pygame.Rect(shaft_x, self.rect.y + self._TOP_PAD, shaft_w, usable)
        pygame.draw.rect(surface, theme.SURFACE, shaft_rect, border_radius=6)
        pygame.draw.rect(surface, theme.BORDER, shaft_rect, width=1, border_radius=6)

        # Waiting passengers.
        for floor in range(num_floors):
            waiting = engine.building.waiting_at(floor)
            y = self._floor_y(floor, num_floors)
            for i, p in enumerate(waiting):
                cx = self.rect.right - 40 - i * 26
                if cx < shaft_x + shaft_w + 20:
                    break
                self._draw_passenger(surface, cx, y, p, theme.TEXT_MUTED, current_time=engine.time)

        # The cab.
        elevator = engine.building.elevator
        target_y = self._floor_y(elevator.current_floor, num_floors)
        if self._cab_y is None:
            self._cab_y = float(target_y)
        else:
            self._cab_y = theme.lerp(self._cab_y, target_y, 0.25)
        cab_h = max(int(step) - 6, 110)
        cab_rect = pygame.Rect(shaft_x + 4, int(self._cab_y) - cab_h // 2, shaft_w - 8, cab_h)
        full = elevator.is_full()
        theme.draw_panel(surface, cab_rect, radius=6,
                        fill=theme.SURFACE_HI,
                        border=theme.WARN if full else self.accent, border_w=2)
        
        direction = getattr(elevator.direction, "value", 0)
        theme.draw_arrow(surface, (cab_rect.right - 18, cab_rect.y + 16), direction,
                         size=12, color=theme.TEXT)
        
        # Passengers inside the cab in a clean 2x2 grid
        body_y = cab_rect.y + 24
        for i, p in enumerate(elevator.onboard):
            col = i % 2
            row = i // 2
            cx = cab_rect.x + 40 + col * 60
            cy = body_y + 12 + row * 40
            self._draw_passenger(surface, cx, cy, p, self.accent, small=True, current_time=engine.time)

        # Urgent Alerts (Global overlay)
        self._draw_urgent_alerts(surface, engine)

    def _draw_urgent_alerts(self, surface: pygame.Surface, engine: SimulationEngine) -> None:
        """Display a blinking warning if any passenger is close to a timeout."""
        urgent_passengers = []
        
        # Check all floors
        for floor in range(engine.num_floors):
            for p in engine.building.waiting_at(floor):
                time_left = p.max_wait_time - (engine.time - p.spawn_time)
                if 0 < time_left <= 3.0:
                    urgent_passengers.append((time_left, f"tầng {floor}"))
        
        # Check cab
        for p in engine.building.elevator.onboard:
            time_left = p.max_wait_time - (engine.time - p.spawn_time)
            if 0 < time_left <= 3.0:
                urgent_passengers.append((time_left, "thang máy"))
                
        if not urgent_passengers:
            return
            
        # Get the most urgent one
        urgent_passengers.sort()
        time_left, loc = urgent_passengers[0]
        
        # Blinking effect (4Hz)
        if int(engine.time * 4) % 2 == 0:
            msg = f"⚠️ URGENT: Khách ở {loc} sắp bỏ đi ({time_left:.1f}s còn lại)! ⚠️"
            
            # Draw alert banner at the top of the building rect
            alert_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 45, self.rect.width - 20, 30)
            theme.draw_panel(surface, alert_rect, radius=6, fill=(45, 10, 10), border=theme.WARN)
            theme.render_text(surface, msg, alert_rect.center, size=14, color=theme.WARN, 
                             bold=True, center=True)

    def _draw_passenger(self, surface: pygame.Surface, cx: int, cy: int,
                        p: 'Passenger', color: tuple[int, int, int], *, 
                        small: bool = False, current_time: float) -> None:
        """Draw a passenger chip with urgency indicators and deadline bars."""
        from models.enums import PassengerType
        is_urgent = p.passenger_type == PassengerType.URGENT
        
        # Color & Aura
        p_color = theme.WARN if is_urgent else color
        r = 6 if small else 9
        
        if is_urgent and not small:
            # Pulsing effect or just red glow
            pygame.draw.circle(surface, theme.WARN, (cx, cy), r + 2, 1)

        pygame.draw.circle(surface, p_color, (cx, cy), r)
        pygame.draw.circle(surface, theme.BG_BOTTOM, (cx, cy), r, 1)
        
        # Destination floor (always show)
        theme.render_text(surface, str(p.dest_floor), (cx, cy - (14 if small else 18)),
                         size=11 if small else 12, color=p_color, center=True, bold=is_urgent)
        
        if not small:
            # Deadline countdown bar (very small bar above the chip)
            limit = p.max_wait_time
            elapsed = current_time - p.spawn_time
            ratio = max(0.0, 1.0 - (elapsed / limit))
            bar_w = 20
            bar_rect = pygame.Rect(cx - bar_w//2, cy + 12, bar_w, 3)
            pygame.draw.rect(surface, theme.SURFACE_HI, bar_rect)
            if ratio > 0:
                bar_color = theme.GOLD if ratio > 0.3 else theme.WARN
                pygame.draw.rect(surface, bar_color, 
                                 pygame.Rect(bar_rect.x, bar_rect.y, int(bar_w * ratio), 3))


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
    """Enhanced v2 HUD panel."""
    theme.draw_panel(surface, rect)
    stats = engine.stats
    total = engine.scenario and len(engine.scenario.passengers) or stats.delivered_count
    x, w = rect.x + 18, rect.width - 36
    y = rect.y + 16
    theme.render_text(surface, "LIVE STATS", (x, y), size=14, color=accent, bold=True)
    y += 30
    
    rows = [
        ("Time", f"{engine.time:.2f}"),
        ("Capacity", f"{engine.building.elevator.occupancy} / {engine.building.elevator.capacity}", 
         theme.WARN if engine.building.elevator.is_full() else accent),
        ("Distance", f"{stats.total_distance} units"),
        ("Avg Wait", f"{stats.average_waiting_time:.1f}"),
        ("Delivered", f"{stats.delivered_count} / {total} ({stats.urgent_delivered_count}U)"),
        ("Fail (L/A)", f"{stats.left_count} / {stats.angry_count}", theme.WARN),
    ]
    for row in rows + (extra or []):
        color = row[2] if len(row) > 2 else theme.TEXT
        draw_stat_row(surface, x, y, w, row[0], row[1], color=color)
        y += 24

    # Score block.
    y += 12
    score_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, 60)
    theme.draw_panel(surface, score_rect, fill=theme.SURFACE_HI, border=theme.GOLD)
    theme.render_text(surface, "SCORE", (score_rect.x + 14, score_rect.y + 8),
                     size=13, color=theme.TEXT_MUTED)
    theme.render_text(surface, f"{score}", (score_rect.centerx, score_rect.centery + 6),
                     size=32, color=theme.GOLD, family="mono", bold=True, center=True)
