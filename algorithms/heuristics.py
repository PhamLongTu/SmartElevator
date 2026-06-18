"""Hàm Heuristic cho các thuật toán tìm kiếm thông minh và tìm kiếm cục bộ.

Một hàm heuristic ước tính chi phí còn lại từ một :class:`~models.state.State` 
đến đích. Module này cung cấp một registry nhỏ để các thuật toán có thể chọn 
heuristic theo tên.

Các hàm heuristic dựa trên bước di chuyển:

* ``span``      -- H1, bao phủ đoạn tầng; chấp nhận được (admissible) và nhất quán (consistent). Đây là mặc định cho A*.
* ``greedy``    -- H2, kết hợp giữa ``span + alpha * số người chưa giao xong`` (không chấp nhận được, dùng cho thuật toán Tham lam).
"""

from __future__ import annotations

from collections.abc import Callable

from models.state import State

#: Một hàm heuristic ánh xạ một trạng thái tới chi phí ước tính còn lại.
Heuristic = Callable[[State], float]


def span(state: State) -> float:
    """Heuristic bao phủ khoảng tầng; mặc định cho A*."""
    return state.heuristic("span")


def greedy_blend(alpha: float = 1.5, waiting_weight: float = 4.0) -> Heuristic:
    """Heuristic trộn ``span`` với số khách còn trong hệ thống."""

    def _h(state: State) -> float:
        # Khách đang chờ được ưu tiên cao hơn vì STOP có thể làm lộ đích xa hơn.
        return (
            state.heuristic("span")
            + alpha * state.num_in_system
            + waiting_weight * state.num_waiting
        )

    return _h


#: Danh sách các heuristic có thể chọn theo tên.
REGISTRY: dict[str, Heuristic] = {
    "span": span,
    "greedy": greedy_blend(),
}


def get_heuristic(name: str) -> Heuristic:
    """Lấy heuristic theo tên."""
    try:
        return REGISTRY[name]
    except KeyError as exc:
        valid = ", ".join(sorted(REGISTRY))
        raise KeyError(f"Unknown heuristic {name!r}. Valid options: {valid}.") from exc
