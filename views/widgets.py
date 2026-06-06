"""Reusable Pygame widgets: Button, Dropdown, and Tabs.

Each widget owns its rect, draws itself, and handles a Pygame event, returning
a simple value when activated. Kept framework-light so screens can compose them
freely. All visuals come from :mod:`views.theme`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pygame

from views import theme


class Button:
    """A clickable, keyboard-focusable button.

    Args:
        rect: Bounding rectangle.
        label: Text shown on the button.
        on_click: Callback invoked when the button is activated.
        accent: Accent color for hover/focus and the left marker.
        icon: Optional short glyph drawn before the label.
    """

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        on_click: Callable[[], None],
        *,
        accent: tuple[int, int, int] = theme.HUMAN,
        icon: str = "",
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.accent = accent
        self.icon = icon
        self.hover = False
        self.focused = False

    def handle(self, event: pygame.event.Event) -> bool:
        """Process one event. Returns True if the button was activated."""
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        elif event.type == pygame.KEYDOWN and self.focused:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        active = self.hover or self.focused
        fill = theme.SURFACE_HI if active else theme.SURFACE
        theme.draw_panel(surface, self.rect, fill=fill,
                         border=self.accent if active else theme.BORDER)
        if active:
            marker = pygame.Rect(self.rect.x, self.rect.y + 8, 4, self.rect.height - 16)
            pygame.draw.rect(surface, self.accent, marker, border_radius=2)
        text = f"{self.icon}  {self.label}" if self.icon else self.label
        theme.render_text(surface, text, self.rect.center,
                         size=20, color=theme.TEXT, center=True,
                         bold=active)


class Dropdown:
    """A dropdown selector with an expandable option list.

    Args:
        rect: Bounding rectangle of the collapsed control.
        options: Selectable option labels.
        index: Initially selected index.
        on_change: Callback invoked with the newly selected index.
        accent: Accent color for the open/selected state.
    """

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        options: Sequence[str],
        *,
        index: int = 0,
        on_change: Callable[[int], None] | None = None,
        accent: tuple[int, int, int] = theme.AI,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.options = list(options)
        self.index = index
        self.on_change = on_change
        self.accent = accent
        self.open = False

    @property
    def value(self) -> str:
        """The currently selected option label."""
        return self.options[self.index]

    def _option_rects(self) -> list[pygame.Rect]:
        return [
            pygame.Rect(self.rect.x, self.rect.bottom + 4 + i * self.rect.height,
                        self.rect.width, self.rect.height)
            for i in range(len(self.options))
        ]

    def handle(self, event: pygame.event.Event) -> bool:
        """Process one event. Returns True if the selection changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.open = not self.open
                return False
            if self.open:
                for i, r in enumerate(self._option_rects()):
                    if r.collidepoint(event.pos):
                        changed = i != self.index
                        self.index = i
                        self.open = False
                        if changed and self.on_change:
                            self.on_change(i)
                        return changed
                self.open = False
        return False

    def draw(self, surface: pygame.Surface) -> None:
        theme.draw_panel(surface, self.rect, fill=theme.SURFACE_HI, border=self.accent)
        theme.render_text(surface, self.value, (self.rect.x + 14, self.rect.centery),
                         size=18, color=theme.TEXT, bold=True,
                         center=False)
        # caret
        cx, cy = self.rect.right - 22, self.rect.centery
        pts = [(cx - 6, cy - 3), (cx + 6, cy - 3), (cx, cy + 4)]
        pygame.draw.polygon(surface, self.accent, pts)

    def draw_overlay(self, surface: pygame.Surface) -> None:
        """Draw the expanded option list (call after other widgets, on top)."""
        if not self.open:
            return
        for i, r in enumerate(self._option_rects()):
            sel = i == self.index
            theme.draw_panel(surface, r,
                            fill=theme.SURFACE_HI if sel else theme.SURFACE,
                            border=self.accent if sel else theme.BORDER)
            theme.render_text(surface, self.options[i], (r.x + 14, r.centery),
                             size=18, color=theme.TEXT if sel else theme.TEXT_MUTED)


class Tabs:
    """A horizontal row of toggle tabs (single selection).

    Args:
        rect: Bounding rectangle of the whole tab strip.
        labels: Tab labels.
        index: Initially active tab.
        on_change: Callback invoked with the newly active index.
    """

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        labels: Sequence[str],
        *,
        index: int = 0,
        on_change: Callable[[int], None] | None = None,
        accent: tuple[int, int, int] = theme.WIN,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.labels = list(labels)
        self.index = index
        self.on_change = on_change
        self.accent = accent

    def _tab_rects(self) -> list[pygame.Rect]:
        n = len(self.labels)
        w = self.rect.width // n
        return [
            pygame.Rect(self.rect.x + i * w, self.rect.y, w - 6, self.rect.height)
            for i in range(n)
        ]

    def handle(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._tab_rects()):
                if r.collidepoint(event.pos):
                    changed = i != self.index
                    self.index = i
                    if changed and self.on_change:
                        self.on_change(i)
                    return changed
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for i, r in enumerate(self._tab_rects()):
            active = i == self.index
            theme.draw_panel(surface, r,
                            fill=theme.SURFACE_HI if active else theme.SURFACE,
                            border=self.accent if active else theme.BORDER)
            theme.render_text(surface, self.labels[i], r.center,
                             size=18, color=theme.TEXT if active else theme.TEXT_MUTED,
                             center=True, bold=active)
