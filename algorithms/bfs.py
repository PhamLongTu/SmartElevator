"""Thuật toán Tìm kiếm theo Chiều rộng (BFS) cho bài toán Thang máy Thông minh.

BFS khám phá đồ thị trạng thái theo từng cấp độ bằng hàng đợi FIFO. Trong bài toán này,
mỗi cạnh được tính là một hành động, vì vậy BFS trả về một kế hoạch với **ít 
hành động nhất** (lưu ý: không nhất thiết là ít *di chuyển* nhất, vì ``STOP`` có chi phí 
bằng 0 -- hãy sử dụng UCS/A* cho các kế hoạch tối ưu về di chuyển).

Các tính năng:
    * Biên (frontier) sử dụng hàng đợi FIFO ``deque``.
    * Phát hiện trạng thái trùng lặp thông qua một tập hợp ``visited`` chứa các trạng thái có thể băm (hashable).
    * Tái tạo đường đi thông qua các liên kết cha (parent links).
    * Theo dõi các nút đã mở rộng và các nút đã được tạo ra.
"""

from __future__ import annotations

from collections import deque

from algorithms.base_search import SearchAlgorithm, SearchResult
from algorithms.search_node import SearchNode
from models.state import State


class BFS(SearchAlgorithm):
    """Tìm kiếm theo chiều rộng trên không gian trạng thái thang máy."""

    name = "BFS"

    def _search(self, initial_state: State) -> SearchResult:
        result = SearchResult()

        # Trường hợp tầm thường: đã giải quyết xong.
        if initial_state.is_goal():
            result.success = True
            return result

        root = SearchNode(state=initial_state)
        frontier: deque[SearchNode] = deque([root])

        # Các trạng thái đã được đưa vào hàng đợi (đánh dấu lúc đưa vào hàng đợi giúp ngăn 
        # cùng một trạng thái được thêm vào biên nhiều hơn một lần).
        visited: set[tuple] = {initial_state.planning_key()}

        best_node = root
        from algorithms.heuristics import span

        while frontier:
            if self._check_budget(result.nodes_expanded):
                result.path = best_node.reconstruct_path()
                result.cost = best_node.g
                return result

            node = frontier.popleft()
            # Tiến trình tìm kiếm mù: sử dụng span (khoảng cách) làm thước đo
            if span(node.state) < span(best_node.state):
                best_node = node
            result.nodes_expanded += 1

            for action, next_state, step_cost in node.state.successors():
                result.nodes_generated += 1
                key = next_state.planning_key()
                if key in visited:
                    continue

                child = SearchNode(
                    state=next_state,
                    parent=node,
                    action=action,
                    g=node.g + step_cost,
                )

                # Kiểm tra mục tiêu sớm tại thời điểm tạo nút (chuẩn cho BFS).
                if next_state.is_goal():
                    result.path = child.reconstruct_path()
                    result.cost = child.g
                    result.success = True
                    return result

                visited.add(key)
                frontier.append(child)

        # Biên đã cạn kiệt mà không tìm thấy mục tiêu.
        return result
