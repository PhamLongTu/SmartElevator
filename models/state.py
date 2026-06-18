from __future__ import annotations

from dataclasses import dataclass

from models.enums import ElevatorAction, PassengerType
from utils.settings import ELEVATOR_CAPACITY, MOVE_COST

# Hành khách trong state được biểu diễn bằng (đích, loại, thời điểm spawn).
PassengerInfo = tuple[int, PassengerType, float]

# Successor gồm (hành động, state kế tiếp, chi phí bước).
Successor = tuple[ElevatorAction, "State", float]


@dataclass(frozen=True, slots=True)
class State:
    """Ảnh chụp bất biến và có thể hash của bài toán tìm kiếm."""

    current_time: float
    elevator_floor: int
    onboard: tuple[PassengerInfo, ...]
    waiting_by_floor: tuple[tuple[PassengerInfo, ...], ...]
    delivered: int
    angry: int
    left: int
    score: int

    @classmethod
    def create(
        cls,
        current_time: float,
        elevator_floor: int,
        onboard: tuple[PassengerInfo, ...],
        waiting_by_floor: tuple[tuple[PassengerInfo, ...], ...],
        delivered: int = 0,
        angry: int = 0,
        left: int = 0,
        score: int = 0,
    ) -> "State":
        """Tạo state chuẩn hóa với các danh sách hành khách đã sắp xếp."""
        def _sort_key(p: PassengerInfo) -> tuple:
            return (p[0], p[1].value, p[2])

        return cls(
            current_time=current_time,
            elevator_floor=elevator_floor,
            onboard=tuple(sorted(onboard, key=_sort_key)) if isinstance(onboard, list) else onboard,
            waiting_by_floor=tuple(
                tuple(sorted(f, key=_sort_key)) if isinstance(f, list) else f
                for f in waiting_by_floor
            ),
            delivered=delivered,
            angry=angry,
            left=left,
            score=score,
        )

    def __hash__(self) -> int:
        """Hash toàn bộ state, làm tròn thời gian để rời rạc hóa không gian tìm kiếm."""
        return hash(
            (
                round(self.current_time, 2),
                self.elevator_floor,
                self.onboard,
                self.waiting_by_floor,
                self.delivered,
                self.angry,
                self.left,
                self.score,
            )
        )

    def planning_key(self) -> tuple:
        """Trả về khóa dùng để loại trạng thái kém hơn trong graph search."""
        return (self.elevator_floor, self.onboard, self.waiting_by_floor)

    def is_goal(self) -> bool:
        """State là goal khi không còn khách trên thang hoặc đang chờ."""
        if self.onboard:
            return False
        return all(len(floor) == 0 for floor in self.waiting_by_floor)

    @property
    def num_waiting(self) -> int:
        """Tổng số hành khách còn chờ ở mọi tầng."""
        return sum(len(floor) for floor in self.waiting_by_floor)

    @property
    def num_in_system(self) -> int:
        """Số hành khách chưa hoàn tất, gồm đang chờ và đang trên thang."""
        return len(self.onboard) + self.num_waiting

    def targets(self) -> set[int]:
        """Các tầng thang vẫn cần ghé."""
        result: set[int] = {p[0] for p in self.onboard}
        if len(self.onboard) >= ELEVATOR_CAPACITY:
            return result

        top_floor = len(self.waiting_by_floor) - 1
        for floor, ps in enumerate(self.waiting_by_floor):
            if ps:
                result.add(floor)
                for p in ps:
                    if p[0] >= 0:
                        result.add(p[0])
                    else:
                        result.add(top_floor if floor < len(self.waiting_by_floor) / 2 else 0)
        return result

    @staticmethod
    def _deadline_for(p: PassengerInfo) -> float:
        return 30.0 if p[1] == PassengerType.NORMAL else 16.0

    def _is_expired(self, p: PassengerInfo, at_time: float) -> bool:
        return (at_time - p[2]) >= self._deadline_for(p)

    def _deadline_effects(
        self,
        dt: float,
        waiting_by_floor: tuple[tuple[PassengerInfo, ...], ...] | None = None,
        onboard: tuple[PassengerInfo, ...] | None = None,
    ) -> tuple[tuple[tuple[PassengerInfo, ...], ...], int, int]:
        """Cập nhật deadline và loại khách chờ vừa hết hạn."""
        new_left = 0
        new_angry = 0

        waiting_source = waiting_by_floor if waiting_by_floor is not None else self.waiting_by_floor
        onboard_source = onboard if onboard is not None else self.onboard
        now = self.current_time
        then = self.current_time + dt

        new_waiting: list[tuple[PassengerInfo, ...]] = []
        for floor_ps in waiting_source:
            kept: list[PassengerInfo] = []
            for p in floor_ps:
                if self._is_expired(p, then):
                    new_left += 1
                else:
                    kept.append(p)
            new_waiting.append(tuple(kept))

        for p in onboard_source:
            if not self._is_expired(p, now) and self._is_expired(p, then):
                new_angry += 1

        return tuple(new_waiting), new_left, new_angry

    def successors(self) -> list[Successor]:
        """Sinh các successor dạng (hành động, state kế tiếp, chi phí)."""
        res: list[Successor] = []

        if self.elevator_floor + 1 < len(self.waiting_by_floor):
            dt = MOVE_COST
            new_waiting, l, a = self._deadline_effects(dt)
            cost = dt + (l * 50) + (a * 10)
            up = State.create(
                self.current_time + dt,
                self.elevator_floor + 1,
                self.onboard,
                new_waiting,
                delivered=self.delivered,
                angry=self.angry + a,
                left=self.left + l,
                score=self.score - int(cost)
            )
            res.append((ElevatorAction.MOVE_UP, up, cost))

        if self.elevator_floor - 1 >= 0:
            dt = MOVE_COST
            new_waiting, l, a = self._deadline_effects(dt)
            cost = dt + (l * 50) + (a * 10)
            down = State.create(
                self.current_time + dt,
                self.elevator_floor - 1,
                self.onboard,
                new_waiting,
                delivered=self.delivered,
                angry=self.angry + a,
                left=self.left + l,
                score=self.score - int(cost)
            )
            res.append((ElevatorAction.MOVE_DOWN, down, cost))

        stop_res = self._stop_result()
        if stop_res:
            res.append(stop_res)

        return res

    def _stop_result(self) -> Successor | None:
        floor = self.elevator_floor
        alighting = [p for p in self.onboard if p[0] == floor]
        staying = [p for p in self.onboard if p[0] != floor]
        
        waiting_here = list(self.waiting_by_floor[floor])
        capacity_left = ELEVATOR_CAPACITY - len(staying)
        boarding = waiting_here[:capacity_left] if capacity_left > 0 else []
        remaining = waiting_here[len(boarding):]

        if not alighting and not boarding:
            return None

        dt = (len(alighting) * 0.5) + (len(boarding) * 0.5)
        new_waiting = list(self.waiting_by_floor)
        new_waiting[floor] = tuple(remaining)
        
        boarded_simulated = []
        for p in boarding:
            if p[0] == -1:
                dummy_dest = len(self.waiting_by_floor) - 1 if floor < len(self.waiting_by_floor) / 2 else 0
                boarded_simulated.append((dummy_dest, p[1], p[2]))
            else:
                boarded_simulated.append(p)
        
        next_onboard = tuple(staying + boarded_simulated)
        advanced_waiting, l, a = self._deadline_effects(
            dt,
            waiting_by_floor=tuple(new_waiting),
            onboard=next_onboard,
        )
        reward = sum(100 if p[1] == PassengerType.NORMAL else 200 for p in alighting)
        cost = dt + l * 50 + a * 10

        next_s = State.create(
            self.current_time + dt,
            floor,
            next_onboard,
            advanced_waiting,
            delivered=self.delivered + len(alighting),
            angry=self.angry + a,
            left=self.left + l,
            score=self.score + reward - int(cost)
        )
        return (ElevatorAction.STOP, next_s, cost)

    def heuristic(self, kind: str = "span") -> float:
        """Ước lượng số bước di chuyển còn lại."""
        targets = self.targets()
        if not targets:
            return 0.0

        f = self.elevator_floor
        lo, hi = min(targets), max(targets)
        base = float((hi - lo) + min(abs(f - lo), abs(f - hi)))
        
        if kind == "span":
            return base
        if kind == "deadline":
            return base * 1.5
        return base
