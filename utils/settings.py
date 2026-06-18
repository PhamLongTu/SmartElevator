"""Các hằng số cấu hình dùng chung cho game Smart Elevator."""

from __future__ import annotations

NUM_FLOORS: int = 7
"""Số tầng của tòa nhà, đánh số nội bộ từ 0."""

ELEVATOR_CAPACITY: int = 4
"""Số hành khách tối đa thang có thể chở cùng lúc."""

GROUND_FLOOR: int = 0
"""Tầng mặc định khi thang bắt đầu."""

MOVE_COST: float = 1.0
"""Chi phí của một hành động MOVE_UP hoặc MOVE_DOWN."""

STOP_COST: float = 0.0
"""Chi phí của hành động STOP."""
