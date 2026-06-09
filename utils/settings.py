"""Global configuration constants for the Smart Elevator game.

Centralizes the building rules so the models, simulation, and views all
share a single source of truth.
"""

from __future__ import annotations

# --- Building rules -------------------------------------------------------
NUM_FLOORS: int = 7
"""Number of floors in the building (indexed internally as 0..NUM_FLOORS-1)."""

ELEVATOR_CAPACITY: int = 4
"""Maximum number of passengers the elevator can carry at once."""

GROUND_FLOOR: int = 0
"""The floor the elevator starts on by default."""

# --- Cost model (see cost_functions design) -------------------------------
MOVE_COST: float = 1.0
"""Cost of a single MOVE_UP / MOVE_DOWN action (one floor transition)."""

STOP_COST: float = 0.0
"""Cost of a STOP (serve) action. Zero under the move-count objective."""
