"""Input handling for Manual Mode.

Translates raw key input into elevator :class:`~models.enums.ElevatorAction`
values. Kept deliberately Pygame-agnostic: bindings are defined over single
character strings so the logic is unit-testable without a display, while
:meth:`InputHandler.from_pygame_key` lazily maps real Pygame key constants when
a GUI front-end is wired up.

Default controls:
    * ``W`` -> move up
    * ``S`` -> move down
    * ``Space`` -> open door (serve: drop off then pick up)
"""

from __future__ import annotations

from models.enums import ElevatorAction


class InputHandler:
    """Maps key input to elevator actions.

    Args:
        bindings: Optional custom mapping of lowercase character -> action.
    """

    def __init__(self, bindings: dict[str, ElevatorAction] | None = None) -> None:
        self.bindings: dict[str, ElevatorAction] = bindings or {
            "w": ElevatorAction.MOVE_UP,
            "s": ElevatorAction.MOVE_DOWN,
            " ": ElevatorAction.STOP,
        }

    def translate(self, key: str) -> ElevatorAction | None:
        """Translate a character key to an action, or ``None`` if unbound."""
        if not key:
            return None
        return self.bindings.get(key.lower())

    def from_pygame_key(self, key: int) -> ElevatorAction | None:
        """Translate a Pygame key constant to an action (lazy Pygame import).

        Returns ``None`` if Pygame is unavailable or the key is unbound.
        """
        try:
            import pygame
        except ImportError:
            return None

        pygame_map: dict[int, ElevatorAction] = {
            pygame.K_w: ElevatorAction.MOVE_UP,
            pygame.K_UP: ElevatorAction.MOVE_UP,
            pygame.K_s: ElevatorAction.MOVE_DOWN,
            pygame.K_DOWN: ElevatorAction.MOVE_DOWN,
            pygame.K_SPACE: ElevatorAction.STOP,
        }
        return pygame_map.get(key)
