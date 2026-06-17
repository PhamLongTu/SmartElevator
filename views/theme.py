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

BTN_TOP = (255, 210, 50)
BTN_BOT = (255, 130, 0)
BTN_BORDER = (45, 20, 5)
BTN_SHADOW = (180, 80, 0)
BTN_HOVER_TOP = (255, 230, 100)
BTN_HOVER_BOT = (255, 160, 30)
GOLD = (255, 215, 0)      # Gold - for best score
GREEN = (0, 255, 100)     # Bright green - for best in other metrics

# Category colors for the algorithm selector.
CATEGORY_COLOR = {
    "Uninformed": (129, 140, 248),  # indigo
    "Informed": AI,
    "Local": (244, 114, 182),       # pink
}

# --- Fonts ------------------------------------------------------------------
_DISPLAY = ["Segoe UI Semibold", "Bahnschrift", "Arial Black", "Arial"]
_UI = ["Verdana", "Segoe UI", "Calibri", "Arial"]
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
    """Draw a premium rounded panel with subtle gradients and highlights."""
    # 1. Base Rounded Background
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    
    # 2. Add Gloss and Glow using a temporary alpha surface
    if rect.height > 5:
        # Create an alpha-enabled surface matching the panel size
        alpha_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        
        # Top Glossy highlight (very subtle white overlay)
        gloss_h = rect.height // 2
        pygame.draw.rect(alpha_surf, (255, 255, 255, 12), (0, 0, rect.width, gloss_h), 
                         border_top_left_radius=radius, border_top_right_radius=radius)
        
        # Inner fine highlight edge
        if border is not None:
            hi_color = tuple(min(255, c + 60) for c in border)
            pygame.draw.rect(alpha_surf, (hi_color[0], hi_color[1], hi_color[2], 50), 
                             (1, 1, rect.width-2, rect.height-2), 
                             width=1, border_radius=radius-1)
        
        # Blit the accumulated alpha effects
        surface.blit(alpha_surf, rect.topleft)

    # 3. Main Outer Border
    if border is not None:
        pygame.draw.rect(surface, border, rect, width=border_w, border_radius=radius)


def render_text(surface: pygame.Surface, text: str, pos: tuple[int, int], *,
                size: int = 18, color: tuple[int, int, int] = TEXT,
                family: str = "ui", bold: bool = False,
                center: bool = False, right: bool = False,
                midleft: bool = False, max_width: int | None = None,
                outline_color: tuple[int, int, int] | None = None,
                outline_width: int = 2) -> pygame.Rect:
    """Blit text and return its rect.

    Anchors at top-left unless ``center`` (both axes), ``right`` (top-right),
    or ``midleft`` (left edge, vertically centered) is set.
    If ``max_width`` is set, shrinks the font size until the text fits.
    If ``outline_color`` is set, blits a thick stroke around the text.
    """
    if max_width:
        # Scale down if too wide
        current_size = size
        while current_size > 8:
            base_font = get_font(current_size, family=family, bold=bold)
            img = base_font.render(text, True, color)
            if img.get_width() <= max_width:
                break
            current_size -= 2
    else:
        base_font = get_font(size, family=family, bold=bold)
        img = base_font.render(text, True, color)

    rect = img.get_rect()
    if center:
        rect.center = pos
    elif right:
        rect.topright = pos
    elif midleft:
        rect.midleft = pos
    else:
        rect.topleft = pos

    if outline_color is not None:
        outline_img = base_font.render(text, True, outline_color)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx*dx + dy*dy > 0:
                    surface.blit(outline_img, (rect.x + dx, rect.y + dy))

    surface.blit(img, rect)
    return rect


def draw_arrow(surface: pygame.Surface, center: tuple[int, int], direction: int,
               size: int = 12, color: tuple[int, int, int] = TEXT) -> None:
    """Draw an up/down arrow as a filled triangle (font-independent).

    ``direction`` > 0 points up, < 0 points down, 0 draws a small dot. Using a
    polygon avoids relying on Unicode arrow glyphs, which some system fonts
    (e.g. Verdana) do not provide and render as empty boxes.
    """
    cx, cy = center
    h = size // 2
    w = size // 2
    if direction > 0:
        pts = [(cx, cy - h), (cx - w, cy + h), (cx + w, cy + h)]
        pygame.draw.polygon(surface, color, pts)
    elif direction < 0:
        pts = [(cx, cy + h), (cx - w, cy - h), (cx + w, cy - h)]
        pygame.draw.polygon(surface, color, pts)
    else:
        pygame.draw.circle(surface, color, (cx, cy), max(2, h // 2))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation, used for smooth cab/animation easing."""
    return a + (b - a) * t


def draw_countdown(surface: pygame.Surface, seconds: float) -> None:
    """Draw a large countdown overlay in the center of the screen."""
    import math
    if seconds <= 0:
        return
        
    # Dim the background
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((11, 16, 32, 160))
    surface.blit(overlay, (0, 0))
    
    # Scale and opacity pulse
    fraction = seconds % 1.0 or 1.0
    size = int(120 + 80 * fraction)
    alpha = int(255 * fraction)
    
    val = math.ceil(seconds)
    text = str(val) if seconds > 0.3 else "GO!"
    color = WIN if text == "GO!" else TEXT
    
    # Render with alpha
    img = get_font(size, family="display", bold=True).render(text, True, color)
    img.set_alpha(alpha)
    rect = img.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(img, rect)
