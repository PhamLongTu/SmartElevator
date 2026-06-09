"""Screen framework: the :class:`Screen` base and the :class:`App` main loop.

The app holds a stack of named screens and runs the Pygame event/update/draw
loop. Screens request transitions by returning a :class:`Transition` from their
event handler (or calling :meth:`App.go_to`), keeping navigation declarative and
matching the UI/UX navigation flow.

A shared :class:`Session` carries cross-screen choices (selected scenario setup,
last run's engine/score) so the Statistics Dashboard can report on whatever mode
just finished.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from views import theme


@dataclass
class Session:
    """Cross-screen state shared between screens."""

    passengers: int = 5
    seed: int = 7
    algorithm: str = "astar"
    # Populated by a mode screen when a run ends, read by the dashboard.
    last_engine: object | None = None
    last_score: int = 0
    last_label: str = ""
    extras: dict = field(default_factory=dict)


class Screen:
    """Base class for all screens.

    Subclasses override :meth:`handle_event`, :meth:`update`, and :meth:`draw`.
    """

    def __init__(self, app: "App") -> None:
        self.app = app
        self.session = app.session

    def on_enter(self) -> None:
        """Called each time the screen becomes active."""

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle a single Pygame event."""

    def update(self, dt: float) -> None:
        """Advance any time-based state by ``dt`` seconds."""

    def draw(self, surface: pygame.Surface) -> None:
        """Render the screen."""


class App:
    """Owns the window, the screen registry, and the main loop.

    Args:
        headless: If True, render to an offscreen surface (for tests); no window
            is created and the loop is not started.
    """

    def __init__(self, headless: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption(theme.TITLE)
        self.headless = headless
        if headless:
            self.screen_surface = pygame.Surface((theme.WIDTH, theme.HEIGHT))
        else:
            # Use SCALED for better high-DPI support and automatic aspect ratio handling
            # Added RESIZABLE to enable the window maximize button
            self.screen_surface = pygame.display.set_mode((theme.WIDTH, theme.HEIGHT), 
                                                         pygame.SCALED | pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.session = Session()
        self.fullscreen = False
        self.running = True

        self._registry: dict[str, type[Screen]] = {}
        self._current: Screen | None = None
        self._current_name = ""

    # ------------------------------------------------------------------
    # Screen management
    # ------------------------------------------------------------------
    def register(self, name: str, screen_cls: type[Screen]) -> None:
        """Register a screen class under a name."""
        self._registry[name] = screen_cls

    def go_to(self, name: str) -> None:
        """Switch to a registered screen (instantiated fresh each time)."""
        screen_cls = self._registry[name]
        self._current = screen_cls(self)
        self._current_name = name
        self._current.on_enter()

    @property
    def current_name(self) -> str:
        """Name of the active screen."""
        return self._current_name

    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and full-screen mode."""
        self.fullscreen = not self.fullscreen
        pygame.display.toggle_fullscreen()

    # ------------------------------------------------------------------
    # Frame stepping
    # ------------------------------------------------------------------
    def step(self, dt: float, events: list[pygame.event.Event] | None = None) -> None:
        """Run one frame: handle events, update, and draw (used by loop + tests)."""
        if self._current is None:
            return
        for event in events if events is not None else pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            else:
                self._current.handle_event(event)
        self._current.update(dt)
        theme.draw_vgradient(self.screen_surface,
                             pygame.Rect(0, 0, theme.WIDTH, theme.HEIGHT),
                             theme.BG_TOP, theme.BG_BOTTOM)
        self._current.draw(self.screen_surface)

    def run(self) -> None:
        """Run the blocking main loop until the user quits."""
        while self.running:
            dt = self.clock.tick(theme.FPS) / 1000.0
            self.step(dt)
            if not self.headless:
                pygame.display.flip()
        pygame.quit()
