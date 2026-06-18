"""Xử lý input cho chế độ thủ công."""

from __future__ import annotations

from models.enums import ElevatorAction


class InputHandler:
    """Ánh xạ phím bấm sang hành động thang máy."""

    def __init__(self, bindings: dict[str, ElevatorAction] | None = None) -> None:
        self.bindings: dict[str, ElevatorAction] = bindings or {
            "w": ElevatorAction.MOVE_UP,
            "s": ElevatorAction.MOVE_DOWN,
            " ": ElevatorAction.STOP,
        }

    def translate(self, key: str) -> ElevatorAction | None:
        """Chuyển phím dạng chuỗi sang hành động."""
        if not key:
            return None
        return self.bindings.get(key.lower())

    def from_pygame_key(self, key: int) -> ElevatorAction | None:
        """Chuyển mã phím Pygame sang hành động."""
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
