from __future__ import annotations

from dataclasses import dataclass

from models.enums import ElevatorAction, PassengerType
from utils.settings import ELEVATOR_CAPACITY, MOVE_COST, NUM_FLOORS, STOP_COST

# A passenger in a state is defined by (destination, type, spawn_time).
PassengerInfo = tuple[int, PassengerType, float]

# A successor is (action taken, resulting state, step cost).
Successor = tuple[ElevatorAction, "State", float]


@dataclass(frozen=True, slots=True)
class State:
    """An immutable, hashable snapshot of the search problem.

    In Version 2, the state is dynamic and time-aware. Two states are considered
    equal if the elevator is at the same floor and the distribution of
    passenger types and deadlines is identical.
    """

    current_time: float
    elevator_floor: int
    onboard: tuple[PassengerInfo, ...]
    waiting_by_floor: tuple[tuple[PassengerInfo, ...], ...]
    delivered: int
    angry: int
    left: int
    score: int

    # -- construction ------------------------------------------------------
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
        """Build a canonicalized state with all passenger lists sorted."""
        # Use a key function to make PassengerType (enum) sortable by
        # converting each tuple element to a comparable form.
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
        """Hash the state, rounding time to discretize the search space."""
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

    # -- goal test ---------------------------------------------------------
    def is_goal(self) -> bool:
        """A state is a goal when no passenger is onboard or waiting anywhere."""
        if self.onboard:
            return False
        return all(len(floor) == 0 for floor in self.waiting_by_floor)

    # -- derived helpers ---------------------------------------------------
    @property
    def num_waiting(self) -> int:
        """Total passengers still waiting across all floors."""
        return sum(len(floor) for floor in self.waiting_by_floor)

    @property
    def num_in_system(self) -> int:
        """Passengers neither delivered yet (onboard + waiting)."""
        return len(self.onboard) + self.num_waiting

    def targets(self) -> set[int]:
        """Floors the elevator still must visit."""
        result: set[int] = {p[0] for p in self.onboard}
        for floor, ps in enumerate(self.waiting_by_floor):
            if ps:
                result.add(floor)
                for p in ps:
                    result.add(p[0])
        return result

    # -- transitions -------------------------------------------------------
    def _apply_deadlines(self, dt: float) -> tuple[int, int, int]:
        """Check for passengers who leave or become angry during delta time."""
        new_left = 0
        new_angry = 0
        
        # Deadlines are fixed: Normal=15, Urgent=8
        def is_expired(p: PassengerInfo, t_now: float) -> bool:
            limit = 15.0 if p[1] == PassengerType.NORMAL else 8.0
            return (t_now - p[2]) >= limit

        # Check waiting
        for floor_ps in self.waiting_by_floor:
            for p in floor_ps:
                if is_expired(p, self.current_time + dt):
                    new_left += 1

        # Check onboard
        for p in self.onboard:
            if is_expired(p, self.current_time + dt):
                new_angry += 1

        return new_left, new_angry, 0

    def successors(self) -> list[Successor]:
        """Generate (action, next_state, cost) successors in version 2."""
        res: list[Successor] = []
        
        # 1. UP
        if self.elevator_floor + 1 < len(self.waiting_by_floor):
            dt = MOVE_COST
            l, a, _ = self._apply_deadlines(dt)
            # Cost reflects time + penalties
            cost = dt + (l * 50) + (a * 10) # Using v2 reward weights
            up = State.create(
                self.current_time + dt,
                self.elevator_floor + 1,
                self.onboard,
                self.waiting_by_floor,
                delivered=self.delivered,
                angry=self.angry + a,
                left=self.left + l,
                score=self.score - int(cost)
            )
            res.append((ElevatorAction.MOVE_UP, up, cost))

        # 2. DOWN
        if self.elevator_floor - 1 >= 0:
            dt = MOVE_COST
            l, a, _ = self._apply_deadlines(dt)
            cost = dt + (l * 50) + (a * 10)
            down = State.create(
                self.current_time + dt,
                self.elevator_floor - 1,
                self.onboard,
                self.waiting_by_floor,
                delivered=self.delivered,
                angry=self.angry + a,
                left=self.left + l,
                score=self.score - int(cost)
            )
            res.append((ElevatorAction.MOVE_DOWN, down, cost))

        # 3. STOP
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
        l, a, _ = self._apply_deadlines(dt)
        
        # Calculate rewards/penalties
        reward = sum(100 if p[1] == PassengerType.NORMAL else 200 for p in alighting)
        # Note: if P was already angry, we don't double count, but in State we track total angry
        
        new_waiting = list(self.waiting_by_floor)
        new_waiting[floor] = tuple(remaining)
        
        next_s = State.create(
            self.current_time + dt,
            floor,
            tuple(staying + boarding),
            tuple(new_waiting),
            delivered=self.delivered + len(alighting),
            angry=self.angry + a,
            left=self.left + l,
            score=self.score + reward - int(dt + l*50 + a*10)
        )
        return (ElevatorAction.STOP, next_s, dt)

    # -- heuristics --------------------------------------------------------
    def heuristic(self, kind: str = "span") -> float:
        """Estimate of remaining moves. H2 (span) is version 2 baseline."""
        targets = self.targets()
        if not targets:
            return 0.0

        f = self.elevator_floor
        lo, hi = min(targets), max(targets)
        base = float((hi - lo) + min(abs(f - lo), abs(f - hi)))
        
        if kind == "span":
            return base
        if kind == "deadline":
            # H3: Weight distance by earliest deadline if possible (Greedy focus)
            return base * 1.5 # simple multiplier for now
        return base
