"""Shared building renderer with per-cell background images.

Visual heart reused by Manual, AI, and Compare screens. The central elevator
shaft splits every floor into TWO zones (left / right), so a 7-floor building
has 7 x 2 = 14 cells. Each cell can be skinned independently with an image:

    assets/images/floor_<N>_left.png      (N = 1..num_floors, floor_1 = "G")
    assets/images/floor_<N>_right.png

Missing or corrupted images fall back to a generated gradient, so the game
never crashes regardless of which files exist.

Performance: the entire static building (cell images, separators, shaft well,
neutral labels) is rendered ONCE into ``self.building_surface`` at init. The
main loop only blits that surface, then draws the dynamic elements (cab,
passengers, the active-floor beacon, alerts) on top.
"""

from __future__ import annotations

import math
import os

import pygame

from models.passenger import Passenger
from simulation.simulation_engine import SimulationEngine
from utils.settings import NUM_FLOORS
from views import theme

# Where the per-cell background images live.
_IMAGE_DIR = os.path.join("assets", "images")

# The two horizontal zones each floor is partitioned into by the center shaft.
_SIDES = ("left", "right")


class BuildingView:
    """Draws an elevator shaft for one engine within a given rectangle.

    Args:
        rect: The area to draw the shaft within.
        accent: Accent color (cyan for player, amber for AI).
        num_floors: Number of floors to pre-render (defaults to NUM_FLOORS).
    """

    # Padding that keeps the shaft below the title and above the bottom edge.
    _TOP_PAD = 10
    _BOT_PAD = 20
    _SIDE_PAD = 10
    _SHAFT_W = 140
    # Dark strip on the far left reserved for floor labels (G, F1...), kept
    # clear of the background images so labels never get washed out by art.
    _LABEL_GUTTER = 40

    # Distinct base hues used by the default (no-image) gradient per floor.
    _DEFAULT_PALETTE = [
        (38, 50, 78),   # Floor 0 / G  -> deep slate blue
        (44, 62, 80),   # Floor 1      -> steel
        (60, 48, 78),   # Floor 2      -> muted violet
        (48, 70, 66),   # Floor 3      -> teal-green
        (78, 60, 44),   # Floor 4      -> warm bronze
        (70, 44, 52),   # Floor 5      -> dusty maroon
        (52, 58, 50),   # Floor 6      -> olive slate
    ]

    def __init__(self, rect: pygame.Rect,
                 accent: tuple[int, int, int] = theme.HUMAN,
                 num_floors: int = NUM_FLOORS) -> None:
        self.rect = pygame.Rect(rect)
        self.accent = accent
        self.num_floors = max(1, num_floors)
        self._cab_y: float | None = None  # smoothed cab pixel position

        self._recompute_geometry()

        # Load images, then bake the static building into one surface.
        self.floor_images = self._load_floor_images()
        self._raw_shaft = self._load_shaft_image()
        self.building_surface = self._pre_render_building()

        # Load passenger character sprites (background already removed) and
        # pre-scale them to the two sizes we draw at.
        self._raw_sprites = self._load_passenger_sprites()
        self._raw_elevator = self._load_elevator_image()
        self._rescale_sprites()

    # ------------------------------------------------------------------ #
    # Passenger sprites
    # ------------------------------------------------------------------ #
    def _load_passenger_sprites(self) -> list[pygame.Surface]:
        """Load ``assets/images/passenger_<n>.png`` (1..N) until one is missing.

        Returns the raw (already background-removed) surfaces. An empty list is
        fine -- the renderer falls back to drawing colored dots.
        """
        sprites: list[pygame.Surface] = []
        i = 1
        while True:
            path = os.path.join(_IMAGE_DIR, f"passenger_{i}.png")
            if not os.path.isfile(path):
                break
            try:
                sprites.append(pygame.image.load(path).convert_alpha())
            except (pygame.error, ValueError) as exc:
                print(f"[BuildingView] Failed to load '{path}': {exc}")
            i += 1
        return sprites

    def _load_shaft_image(self) -> "pygame.Surface | None":
        """Load the elevator shaft backdrop art (assets/images/shaft.png)."""
        path = os.path.join(_IMAGE_DIR, "shaft.png")
        if not os.path.isfile(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, ValueError) as exc:
            print(f"[BuildingView] Failed to load '{path}': {exc}")
            return None

    def _load_elevator_image(self) -> "pygame.Surface | None":
        """Load the cut-out elevator door art (assets/images/elevator.png)."""
        path = os.path.join(_IMAGE_DIR, "elevator.png")
        if not os.path.isfile(path):
            return None
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, ValueError) as exc:
            print(f"[BuildingView] Failed to load '{path}': {exc}")
            return None

    def _rescale_sprites(self) -> None:
        """Build the 'waiting' and 'cab' scaled sprite lists for the current floor height."""
        self._sprites_wait: list[pygame.Surface] = []
        self._sprites_cab: list[pygame.Surface] = []
        wait_h = max(8, int(self._floor_h * 0.74))   # stands within the floor row
        cab_h = max(6, int(self._floor_h * 0.42))    # smaller, fits the 2x2 cab grid
        for s in self._raw_sprites:
            w, h = s.get_size()
            ar = w / h if h else 1.0
            self._sprites_wait.append(
                pygame.transform.smoothscale(s, (max(1, int(wait_h * ar)), wait_h)))
            self._sprites_cab.append(
                pygame.transform.smoothscale(s, (max(1, int(cab_h * ar)), cab_h)))

        # Scale the elevator door art to the cab box (fills the frame).
        self._cab_img = None
        raw_elev = getattr(self, "_raw_elevator", None)
        if raw_elev is not None:
            self._cab_img = pygame.transform.smoothscale(
                raw_elev, (self._SHAFT_W - 8, max(1, self._floor_h)))

    # ------------------------------------------------------------------ #
    # Geometry
    # ------------------------------------------------------------------ #
    def _recompute_geometry(self) -> None:
        """(Re)compute floor height + the left/right zone boxes (cells).

        Called on init and whenever the engine's floor count changes. Zone
        widths are derived from the centered shaft, so a 720px view and a 480px
        compare panel both get correctly sized cells automatically.
        """
        self._usable = self.rect.height - self._TOP_PAD - self._BOT_PAD
        self._step = self._usable / self.num_floors
        self._floor_h = int(self._step)

        # Shaft position in both absolute and surface-local coordinates.
        self.shaft_x = self.rect.centerx - self._SHAFT_W // 2  # absolute
        shaft_x_local = self.shaft_x - self.rect.x

        # Left zone: starts AFTER the label gutter, runs up to the shaft.
        self._left_x = self._SIDE_PAD + self._LABEL_GUTTER
        self._left_w = max(1, shaft_x_local - self._left_x)

        # Right zone: from the shaft up to the right pad.
        self._right_x = shaft_x_local + self._SHAFT_W
        self._right_w = max(1, (self.rect.width - self._SIDE_PAD) - self._right_x)

    def _zone_box(self, side: str) -> tuple[int, int]:
        """Return (x_local, width) of a zone's drawing box for the given side."""
        if side == "left":
            return self._left_x, self._left_w
        return self._right_x, self._right_w

    def _floor_y(self, floor: int) -> int:
        """Absolute pixel y of a floor's row center (floor 0 at the bottom)."""
        return int(self.rect.bottom - self._BOT_PAD - self._step * (floor + 0.5))

    # ------------------------------------------------------------------ #
    # Image loading
    # ------------------------------------------------------------------ #
    def _load_floor_images(self) -> dict[tuple[int, str], pygame.Surface]:
        """Load one image per cell: ``floor_<N>_<side>.png``.

        Returns {(floor_index, side): Surface} scaled to that cell's box.
        Floors are 0-indexed internally; file names are 1-indexed
        (floor index 0 -> floor_1_*.png). Any missing/corrupted file falls
        back to a generated gradient so we never crash.
        """
        images: dict[tuple[int, str], pygame.Surface] = {}

        for floor in range(self.num_floors):
            for side in _SIDES:
                _, zone_w = self._zone_box(side)
                size = (zone_w, max(1, self._floor_h))
                path = os.path.join(_IMAGE_DIR, f"floor_{floor + 1}_{side}.png")
                surface: pygame.Surface | None = None

                if os.path.isfile(path):
                    try:
                        raw = pygame.image.load(path).convert_alpha()
                        surface = pygame.transform.smoothscale(raw, size)
                    except (pygame.error, ValueError) as exc:
                        # Corrupted/unsupported image -> log and fall back.
                        print(f"[BuildingView] Failed to load '{path}': {exc}")
                        surface = None

                if surface is None:
                    surface = self._create_default_floor_image(floor, side)

                images[(floor, side)] = surface

        return images

    def _create_default_floor_image(self, floor_num: int, side: str) -> pygame.Surface:
        """Generate a vertical-gradient placeholder for a cell without an image."""
        _, w = self._zone_box(side)
        h = max(1, self._floor_h)
        surface = pygame.Surface((w, h)).convert()

        base = self._DEFAULT_PALETTE[floor_num % len(self._DEFAULT_PALETTE)]
        # Tint the right zone slightly differently so the two cells are distinct.
        shift = 10 if side == "right" else 0
        top = tuple(min(255, c + 28 + shift) for c in base)   # lighter at top
        bottom = tuple(max(0, c - 18) for c in base)           # darker near floor

        for y in range(h):
            t = y / max(1, h - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(surface, color, (0, y), (w, y))

        pygame.draw.line(surface, theme.BORDER, (0, h - 1), (w, h - 1), 1)
        return surface

    # ------------------------------------------------------------------ #
    # Pre-render (static building baked once)
    # ------------------------------------------------------------------ #
    def _pre_render_building(self) -> pygame.Surface:
        """Bake all 14 cell images, separators, neutral labels and the shaft well.

        Everything here is static; dynamic parts (cab, passengers, the active
        floor beacon/highlight, alerts) are drawn on top each frame in draw().
        """
        surf = pygame.Surface((self.rect.width, self.rect.height)).convert()
        surf.fill(theme.BG_BOTTOM)

        shaft_x_local = self.shaft_x - self.rect.x

        for floor in range(self.num_floors):
            y_local = self._floor_y(floor) - self.rect.y
            top = int(y_local - self._step / 2)

            # 1) Blit the left and right cell images into their zones.
            for side in _SIDES:
                zone_x, zone_w = self._zone_box(side)
                img = self.floor_images.get((floor, side))
                if img is not None:
                    surf.blit(img, (zone_x, top))

                # 2) Dark tint per cell so passengers/text stay readable.
                overlay = pygame.Surface((zone_w, self._floor_h), pygame.SRCALPHA)
                overlay.fill((11, 16, 32, 90))
                surf.blit(overlay, (zone_x, top))

            # 3) Separator line between floors (skips the shaft region).
            sep_y = int(y_local + self._step / 2)
            pygame.draw.line(surf, theme.BORDER,
                             (self._left_x + 4, sep_y), (shaft_x_local, sep_y), 1)
            pygame.draw.line(surf, theme.BORDER,
                             (self._right_x, sep_y),
                             (self.rect.width - self._SIDE_PAD - 4, sep_y), 1)

            # 4) Neutral floor label, centered in the dark gutter (no overlap).
            label = "G" if floor == 0 else f"F{floor}"
            label_x = self._SIDE_PAD + self._LABEL_GUTTER // 2
            theme.render_text(surf, label, (label_x, int(y_local)),
                              size=15, color=theme.TEXT_MUTED, center=True)

        # 5) Shaft well (static backdrop for the moving cab). Use the
        #    pixel-art shaft.png if present, else a plain surface fallback.
        shaft_rect = pygame.Rect(shaft_x_local, self._TOP_PAD, self._SHAFT_W, self._usable)
        if self._raw_shaft is not None:
            shaft_img = pygame.transform.smoothscale(
                self._raw_shaft, (shaft_rect.width, shaft_rect.height))
            surf.blit(shaft_img, shaft_rect.topleft)
        else:
            pygame.draw.rect(surf, theme.SURFACE, shaft_rect, border_radius=6)
        pygame.draw.rect(surf, theme.BORDER, shaft_rect, width=1, border_radius=6)

        return surf

    # ------------------------------------------------------------------ #
    # Main draw pass
    # ------------------------------------------------------------------ #
    def draw(self, surface: pygame.Surface, engine: SimulationEngine, *,
             planned_floors: list[int] | None = None, title: str = "") -> None:
        """Render the building for ``engine``. ``planned_floors`` draws a ghost path."""
        # If the engine's floor count ever differs from what we baked, rebuild.
        if engine.num_floors != self.num_floors:
            self.num_floors = max(1, engine.num_floors)
            self._recompute_geometry()
            self.floor_images = self._load_floor_images()
            self.building_surface = self._pre_render_building()
            self._rescale_sprites()

        # 1) Blit the pre-rendered static building in one cheap operation.
        surface.blit(self.building_surface, self.rect.topleft)

        curr_f = engine.building.elevator.current_floor

        # 2) Active floor highlight + pulsing beacon (dynamic).
        y_active = self._floor_y(curr_f)
        label = "G" if curr_f == 0 else f"F{curr_f}"
        label_x = self.rect.x + self._SIDE_PAD + self._LABEL_GUTTER // 2
        # Small pulsing beacon just below the active label, inside the gutter.
        pulse = (math.sin(engine.time * 8) + 1) / 2
        r = 3 + 2 * pulse
        pygame.draw.circle(surface, self.accent, (label_x, y_active + 16), r)
        pygame.draw.circle(surface, theme.BG_BOTTOM, (label_x, y_active + 16), r, 1)
        theme.render_text(surface, label, (label_x, y_active),
                          size=16, color=self.accent, center=True, bold=True)

        # 3) Waiting passengers, split left/right of the shaft.
        for floor in range(self.num_floors):
            waiting = engine.building.waiting_at(floor)
            y = self._floor_y(floor)
            left_w = [p for p in waiting if p.id % 2 == 0]
            right_w = [p for p in waiting if p.id % 2 != 0]

            for i, p in enumerate(left_w):
                cx = self.shaft_x - 34 - i * 34
                if cx < self.rect.x + 60:  # avoid overlap with labels/beacon
                    break
                self._draw_passenger(surface, cx, y, p, theme.TEXT_MUTED,
                                     current_time=engine.time)

            for i, p in enumerate(right_w):
                cx = self.shaft_x + self._SHAFT_W + 34 + i * 34
                if cx > self.rect.right - 20:
                    break
                self._draw_passenger(surface, cx, y, p, theme.TEXT_MUTED,
                                     current_time=engine.time)

        # 4) The moving cab (smoothed toward its target floor).
        elevator = engine.building.elevator
        target_y = self._floor_y(elevator.current_floor)
        if self._cab_y is None:
            self._cab_y = float(target_y)
        else:
            self._cab_y = theme.lerp(self._cab_y, target_y, 0.25)

        cab_h = int(self._step)
        cab_rect = pygame.Rect(self.shaft_x + 4, int(self._cab_y) - cab_h // 2,
                               self._SHAFT_W - 8, cab_h)
        full = elevator.is_full()
        if self._cab_img is not None:
            # Elevator door artwork fills the cab frame.
            surface.blit(self._cab_img, cab_rect.topleft)
            pygame.draw.rect(surface, theme.WARN if full else self.accent,
                             cab_rect, width=2, border_radius=6)
        else:
            theme.draw_panel(surface, cab_rect, radius=6, fill=theme.SURFACE_HI,
                             border=theme.WARN if full else self.accent, border_w=2)

        direction = getattr(elevator.direction, "value", 0)
        theme.draw_arrow(surface, (cab_rect.right - 14, cab_rect.y + 14), direction,
                         size=11, color=theme.TEXT)

        # Occupancy badge: people now ride in the LIVE STATS panel, so the cab
        # just shows how many are aboard.
        occ = elevator.occupancy
        if occ:
            badge_c = (cab_rect.x + 14, cab_rect.y + 14)
            pygame.draw.circle(surface, theme.BG_BOTTOM, badge_c, 10)
            pygame.draw.circle(surface, self.accent, badge_c, 10, 1)
            theme.render_text(surface, str(occ), badge_c, size=12,
                              color=self.accent, center=True, bold=True)

        # 6) Urgent alerts overlay.
        self._draw_urgent_alerts(surface, engine)

    # ------------------------------------------------------------------ #
    # Sub-renderers
    # ------------------------------------------------------------------ #
    def _draw_urgent_alerts(self, surface: pygame.Surface, engine: SimulationEngine) -> None:
        """Display a blinking warning if any passenger is close to a timeout."""
        urgent_passengers = []

        for floor in range(engine.num_floors):
            for p in engine.building.waiting_at(floor):
                time_left = p.max_wait_time - (engine.time - p.spawn_time)
                if 0 < time_left <= 3.0:
                    urgent_passengers.append((time_left, f"tầng {floor}"))

        for p in engine.building.elevator.onboard:
            time_left = p.max_wait_time - (engine.time - p.spawn_time)
            if 0 < time_left <= 3.0:
                urgent_passengers.append((time_left, "thang máy"))

        if not urgent_passengers:
            return

        urgent_passengers.sort()
        time_left, loc = urgent_passengers[0]

        # Blinking effect (4Hz).
        if int(engine.time * 4) % 2 == 0:
            msg = f"⚠️ URGENT: Khách ở {loc} sắp bỏ đi ({time_left:.1f}s còn lại)! ⚠️"
            alert_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 15,
                                     self.rect.width - 20, 30)
            theme.draw_panel(surface, alert_rect, radius=6, fill=(45, 10, 10),
                             border=theme.WARN)
            theme.render_text(surface, msg, alert_rect.center, size=14,
                              color=theme.WARN, bold=True, center=True)

    def _draw_passenger(self, surface: pygame.Surface, cx: int, cy: int,
                        p: 'Passenger', color: tuple[int, int, int], *,
                        small: bool = False, current_time: float) -> None:
        """Draw a passenger as a character sprite (dot fallback) + dest label + timer."""
        from models.enums import PassengerType
        is_urgent = p.passenger_type == PassengerType.URGENT
        p_color = theme.WARN if is_urgent else color

        sprites = self._sprites_cab if small else self._sprites_wait
        if sprites:
            # Pick a consistent sprite per passenger by id.
            sprite = sprites[p.id % len(sprites)]
            if small:
                rect = sprite.get_rect(center=(cx, cy))
            else:
                # Stand the character so its feet rest near the floor's bottom.
                feet_y = int(cy + self._step / 2) - 4
                rect = sprite.get_rect(midbottom=(cx, feet_y))
            if is_urgent:
                # Red bounding outline so urgent passengers pop.
                pygame.draw.rect(surface, theme.WARN, rect.inflate(6, 6),
                                 width=2, border_radius=4)
            surface.blit(sprite, rect)
            label_y = rect.top - 8
        else:
            # Fallback: original colored dot.
            r = 6 if small else 9
            if is_urgent and not small:
                pygame.draw.circle(surface, theme.WARN, (cx, cy), r + 2, 1)
            pygame.draw.circle(surface, p_color, (cx, cy), r)
            pygame.draw.circle(surface, theme.BG_BOTTOM, (cx, cy), r, 1)
            rect = pygame.Rect(cx - r, cy - r, 2 * r, 2 * r)
            label_y = cy - (10 if small else 18)

        # Destination floor label on a small dark pill for readability.
        pill_r = 8 if not small else 7
        pygame.draw.circle(surface, theme.BG_BOTTOM, (cx, label_y), pill_r)
        pygame.draw.circle(surface, p_color, (cx, label_y), pill_r, 1)
        theme.render_text(surface, str(p.dest_floor), (cx, label_y),
                          size=11 if small else 12, color=p_color,
                          center=True, bold=is_urgent)

        if not small:
            # Deadline countdown bar at the character's feet (ground bar).
            limit = p.max_wait_time
            elapsed = current_time - p.spawn_time
            ratio = max(0.0, 1.0 - (elapsed / limit)) if limit else 0.0
            bar_w = 26
            bar_rect = pygame.Rect(cx - bar_w // 2, rect.bottom - 2, bar_w, 4)
            pygame.draw.rect(surface, theme.SURFACE_HI, bar_rect, border_radius=2)
            if ratio > 0:
                bar_color = theme.GOLD if ratio > 0.3 else theme.WARN
                pygame.draw.rect(surface, bar_color,
                                 pygame.Rect(bar_rect.x, bar_rect.y,
                                             int(bar_w * ratio), 4), border_radius=2)


_HUD_SPRITES: list[pygame.Surface] | None = None


def _hud_onboard_sprites(height: int) -> list[pygame.Surface]:
    """Lazy-load + cache passenger sprites scaled for the HUD onboard strip."""
    global _HUD_SPRITES
    if _HUD_SPRITES is None or (_HUD_SPRITES and _HUD_SPRITES[0].get_height() != height):
        sprites: list[pygame.Surface] = []
        i = 1
        while True:
            path = os.path.join(_IMAGE_DIR, f"passenger_{i}.png")
            if not os.path.isfile(path):
                break
            try:
                raw = pygame.image.load(path).convert_alpha()
                w, h = raw.get_size()
                ar = w / h if h else 1.0
                sprites.append(pygame.transform.smoothscale(
                    raw, (max(1, int(height * ar)), height)))
            except (pygame.error, ValueError):
                pass
            i += 1
        _HUD_SPRITES = sprites
    return _HUD_SPRITES


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

    # Onboard passengers ride here, in the LIVE STATS panel.
    spr_h = 42
    if rect.bottom - y >= spr_h + 96:  # only if there's room (protects short HUDs)
        from models.enums import PassengerType
        onboard = engine.building.elevator.onboard
        y += 8
        theme.render_text(surface, "ONBOARD", (x, y), size=13, color=accent, bold=True)
        y += 20
        strip = pygame.Rect(rect.x + 12, y, rect.width - 24, spr_h + 10)
        theme.draw_panel(surface, strip, fill=theme.SURFACE_HI)
        sprites = _hud_onboard_sprites(spr_h)
        if onboard and sprites:
            gap = min(48, (strip.width - 20) // max(1, len(onboard)))
            sx = strip.x + 12
            for p in onboard:
                spr = sprites[p.id % len(sprites)]
                r = spr.get_rect(midbottom=(sx + spr.get_width() // 2, strip.bottom - 4))
                surface.blit(spr, r)
                pc = theme.WARN if p.passenger_type == PassengerType.URGENT else accent
                pygame.draw.circle(surface, theme.BG_BOTTOM, (r.centerx, strip.y + 11), 8)
                pygame.draw.circle(surface, pc, (r.centerx, strip.y + 11), 8, 1)
                theme.render_text(surface, str(p.dest_floor), (r.centerx, strip.y + 11),
                                  size=11, color=pc, center=True, bold=True)
                sx += gap
        else:
            theme.render_text(surface, "Empty", strip.center, size=14,
                              color=theme.TEXT_MUTED, center=True)
        y = strip.bottom + 6

    # Score block.
    y += 12
    score_rect = pygame.Rect(rect.x + 12, y, rect.width - 24, 60)
    theme.draw_panel(surface, score_rect, fill=theme.SURFACE_HI, border=theme.GOLD)
    theme.render_text(surface, "SCORE", (score_rect.x + 14, score_rect.y + 8),
                     size=13, color=theme.TEXT_MUTED)
    theme.render_text(surface, f"{score}", (score_rect.centerx, score_rect.centery + 6),
                     size=32, color=theme.GOLD, family="mono", bold=True, center=True)
