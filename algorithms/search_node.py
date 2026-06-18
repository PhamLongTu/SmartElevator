"""Node tìm kiếm dùng chung cho các thuật toán.

``SearchNode`` lưu trạng thái, liên kết cha, hành động sinh ra node và các chi
phí ``g``, ``h``, ``f``. Phần này tách khỏi ``State`` để việc so sánh trạng thái
không bị lẫn với thông tin đường đi.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.enums import ElevatorAction
from models.state import State


@dataclass(slots=True)
class SearchNode:
    """Một node trong cây tìm kiếm."""

    state: State
    parent: "SearchNode | None" = None
    action: ElevatorAction | None = None
    g: float = 0.0
    h: float = 0.0

    @property
    def f(self) -> float:
        """Chi phí đánh giá ``f = g + h`` dùng cho A*."""
        return self.g + self.h

    def reconstruct_path(self) -> list[ElevatorAction]:
        """Trả về chuỗi hành động từ node gốc tới node hiện tại."""
        actions: list[ElevatorAction] = []
        node: "SearchNode | None" = self
        while node is not None and node.action is not None:
            actions.append(node.action)
            node = node.parent
        actions.reverse()
        return actions

    def depth(self) -> int:
        """Số hành động từ node gốc tới node hiện tại."""
        count = 0
        node: "SearchNode | None" = self.parent
        while node is not None:
            count += 1
            node = node.parent
        return count

    def __lt__(self, other: "SearchNode") -> bool:
        """Ưu tiên ``f`` nhỏ hơn, sau đó đến ``h`` nhỏ hơn."""
        if self.f != other.f:
            return self.f < other.f
        return self.h < other.h
