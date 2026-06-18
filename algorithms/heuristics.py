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
    """H2: interval-cover span. Admissible and consistent; default for A*."""
    return state.heuristic("span")


def greedy_blend(alpha: float = 1.5, waiting_weight: float = 4.0) -> Heuristic:
    """Blended heuristic ``span + alpha * (# undelivered passengers)``.

    Inadmissible by design: it adds strong goal-pull toward clearing all
    passengers, which suits Greedy Best-First Search (admissibility is
    irrelevant there since ``g`` is ignored).

    Args:
        alpha: Weight on the undelivered-passenger term.

    Returns:
        A heuristic callable.
    """

    def _h(state: State) -> float:
        # Waiting passengers are weighted more heavily than onboard passengers.
        # Otherwise a STOP can look worse than moving away, because boarding a
        # passenger reveals a farther destination and temporarily increases span.
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
    """Look up a heuristic by name.

    Args:
        name: One of the keys in :data:`REGISTRY`.

    Raises:
        KeyError: If ``name`` is not a registered heuristic.
    """
    try:
        return REGISTRY[name]
    except KeyError as exc:
        valid = ", ".join(sorted(REGISTRY))
        raise KeyError(f"Unknown heuristic {name!r}. Valid options: {valid}.") from exc
