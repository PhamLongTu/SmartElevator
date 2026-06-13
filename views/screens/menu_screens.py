"""Menu screens: Main Menu and Mode Selection."""

from __future__ import annotations

import math
import os
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

        # Load and scale the custom background image if it exists.
        self._bg_img = None
        bg_path = os.path.join("assets", "images", "menu_bg.png")
        if os.path.isfile(bg_path):
            try:
                raw = pygame.image.load(bg_path).convert()
                self._bg_img = pygame.transform.smoothscale(raw, (theme.WIDTH, theme.HEIGHT))
            except (pygame.error, ValueError):
                pass

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
        if self._bg_img:
            surface.blit(self._bg_img, (0, 0))
            # Subtle dark overlay to keep text/buttons poppable.
            overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 9, 20, 80))  # ~30% opacity
            surface.blit(overlay, (0, 0))

        for b in self.buttons:
            b.draw(surface)
        theme.render_text(surface, "Building: 7 floors  -  1 elevator  -  capacity 4",
                         (theme.WIDTH // 2, theme.HEIGHT - 40), size=15, color=theme.TEXT_MUTED, center=True)


_card_cache: dict[tuple, pygame.Surface] = {}

def get_bright_card_surface(w: int, h: int, accent: tuple[int, int, int]) -> pygame.Surface:
    """Generate and cache a bright, unique gradient card surface."""
    key = (w, h, accent)
    if key in _card_cache:
        return _card_cache[key]
        
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    radius = 20
    
    # Base shadow
    pygame.draw.rect(surf, (0, 0, 0, 40), (6, 6, w-6, h-6), border_radius=radius)
    
    # Inner light gradient
    inner_rect = pygame.Rect(0, 0, w-6, h-6)
    gradient = pygame.Surface((w-6, h-6), pygame.SRCALPHA)
    top_c = (245, 250, 255)  # almost white / ice blue
    bot_c = (190, 210, 230)  # soft metallic blue
    for i in range(h-6):
        t = i / max(1, h-7)
        r = int(top_c[0] + (bot_c[0] - top_c[0]) * t)
        g = int(top_c[1] + (bot_c[1] - top_c[1]) * t)
        b = int(top_c[2] + (bot_c[2] - top_c[2]) * t)
        pygame.draw.line(gradient, (r, g, b, 255), (0, i), (w-6, i))
        
    mask = pygame.Surface((w-6, h-6), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    surf.blit(gradient, (0, 0))
    
    # Border
    pygame.draw.rect(surf, accent, inner_rect, width=4, border_radius=radius)
    
    # Soft inner top highlight
    hi_rect = pygame.Rect(4, 4, w-14, 16)
    hi_mask = pygame.Surface((w-6, h-6), pygame.SRCALPHA)
    pygame.draw.rect(hi_mask, (255, 255, 255, 180), hi_rect, border_top_left_radius=radius, border_top_right_radius=radius)
    surf.blit(hi_mask, (0, 0))
    
    _card_cache[key] = surf
    return surf


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

        # Load and scale the custom background image if it exists.
        self._bg_img = None
        bg_path = os.path.join("assets", "images", "mode_bg.png")
        if os.path.isfile(bg_path):
            try:
                raw = pygame.image.load(bg_path).convert()
                self._bg_img = pygame.transform.smoothscale(raw, (theme.WIDTH, theme.HEIGHT))
            except (pygame.error, ValueError):
                pass

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
        if self._bg_img:
            surface.blit(self._bg_img, (0, 0))
            # Dark overlay for depth.
            overlay = pygame.Surface((theme.WIDTH, theme.HEIGHT), pygame.SRCALPHA)
            overlay.fill((6, 9, 20, 80))
            surface.blit(overlay, (0, 0))

        # Render "SELECT MODE" with the new arcade stroke style
        theme.render_text(surface, "SELECT MODE", (theme.WIDTH // 2, 80),
                         size=54, color=(255, 255, 255), family="display", bold=True, center=True,
                         outline_color=theme.BTN_BORDER, outline_width=4)
        self.back.draw(surface)
        for i, rect in enumerate(self.card_rects):
            label, _, accent, icon, lines = self.cards[i]
            
            # Draw unique bright custom panel
            card_surf = get_bright_card_surface(rect.width + 6, rect.height + 6, accent)
            surface.blit(card_surf, (rect.x, rect.y))
            
            # Card Label with dark outline for high contrast on bright bg
            theme.render_text(surface, label, (rect.centerx, rect.y + 40),
                             size=34, color=accent, family="display", bold=True, center=True,
                             outline_color=(20, 30, 45), outline_width=2)
                             
            # Card Description lines (dark navy blue for readability)
            for j, line in enumerate(lines):
                theme.render_text(surface, line, (rect.centerx, rect.y + 110 + j * 24),
                                 size=16, color=(30, 42, 64), family="ui", bold=True, center=True)
                                 
            # Select buttons are inside the card area
            self.select_buttons[i].draw(surface)
            
        # Scenario setup strip.
        theme.render_text(surface, "Passengers", (theme.WIDTH // 2 - 55, 572),
                         size=20, color=(255, 255, 255), family="ui", bold=True, right=True)
        theme.render_text(surface, str(self.session.passengers),
                         (theme.WIDTH // 2 + 42, 582), size=28, color=(255, 255, 255),
                         family="display", bold=True, center=True)
        self.minus.draw(surface)
        self.plus.draw(surface)
        theme.render_text(surface, f"Seed {self.session.seed}",
                         (theme.WIDTH // 2, 640), size=16, color=(255, 255, 255), bold=True, center=True)
