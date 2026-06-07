"""Visual theme for the Pygame UI: palette, fonts, and layout constants.

Centralizes every color, font, and dimension so all screens stay visually
consistent (mirrors the UI/UX design system). Fonts are loaded via ``SysFont``
with a candidate list so the app looks good on Windows without bundling files,
and degrades gracefully if a family is missing.
"""

from __future__ import annotations

import pygame

# --- Window -----------------------------------------------------------------
WIDTH: int = 1280
HEIGHT: int = 720
FPS: int = 60
TITLE: str = "Smart Elevator - AI Dispatch Simulation"

# --- Palette (from the UI/UX design system) ---------------------------------
BG_TOP = (11, 16, 32)
BG_BOTTOM = (6, 9, 20)
SURFACE = (21, 27, 46)
SURFACE_HI = (30, 38, 64)
BORDER = (43, 54, 86)
TEXT = (226, 232, 240)
TEXT_MUTED = (148, 163, 184)

HUMAN = (34, 211, 238)   # cyan  -> player / manual
AI = (245, 158, 11)      # amber -> AI
WIN = (52, 211, 153)     # green -> success / winner / delivered
WARN = (244, 63, 94)     # rose  -> full cab / long wait
GOLD = (250, 204, 21)    # score star

# Category colors for the algorithm selector.
CATEGORY_COLOR = {
    "Uninformed": (129, 140, 248),  # indigo
    "Informed": AI,
    "Local": (244, 114, 182),       # pink
}

# --- Fonts ------------------------------------------------------------------
_DISPLAY = ["Bahnschrift", "Segoe UI Semibold", "Arial Black", "Arial"]
_UI = ["Segoe UI", "Calibri", "Arial"]
_MONO = ["Consolas", "Courier New", "monospace"]

_font_cache: dict[tuple, pygame.font.Font] = {}


def get_font(size: int, *, family: str = "ui", bold: bool = False) -> pygame.font.Font:
    """Return a cached font. ``family`` is ``"display"``, ``"ui"`` or ``"mono"``."""
    key = (size, family, bold)
    if key not in _font_cache:
        names = {"display": _DISPLAY, "ui": _UI, "mono": _MONO}.get(family, _UI)
        _font_cache[key] = pygame.font.SysFont(",".join(names), size, bold=bold)
    return _font_cache[key]


# --- Drawing helpers --------------------------------------------------------
def draw_vgradient(surface: pygame.Surface, rect: pygame.Rect,
                   top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    """Fill ``rect`` with a vertical gradient from ``top`` to ``bottom``."""
    x, y, w, h = rect
    for i in range(h):
        t = i / max(1, h - 1)
        color = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(surface, color, (x, y + i), (x + w, y + i))


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, *,
               radius: int = 14, fill: tuple[int, int, int] = SURFACE,
               border: tuple[int, int, int] | None = BORDER,
               border_w: int = 1) -> None:
    """Draw a rounded surface panel with an optional border."""
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border is not None:
        pygame.draw.rect(surface, border, rect, width=border_w, border_radius=radius)


def render_text(surface: pygame.Surface, text: str, pos: tuple[int, int], *,
                size: int = 18, color: tuple[int, int, int] = TEXT,
                family: str = "ui", bold: bool = False,
                center: bool = False, right: bool = False,
                midleft: bool = False) -> pygame.Rect:
    """Blit text and return its rect.

    Anchors at top-left unless ``center`` (both axes), ``right`` (top-right),
    or ``midleft`` (left edge, vertically centered) is set.
    """
    img = get_font(size, family=family, bold=bold).render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    elif right:
        rect.topright = pos
    elif midleft:
        rect.midleft = pos
    else:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation, used for smooth cab/animation easing."""
    return a + (b - a) * t
