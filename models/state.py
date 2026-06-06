"""The immutable search :class:`State`.

This is the value object the AI algorithms search over. It is **frozen and
hashable** so it can be used as a key in visited-sets and priority queues, and
it abstracts away passenger identity (two passengers with the same destination
are interchangeable). The mutable runtime world (``Building``/``Elevator``)
is kept entirely separate.

State layout::

    (elevator_floor, onboard_dests, waiting_by_floor)

where ``onboard_dests`` is a sorted tuple of destination floors of onboard
riders, and ``waiting_by_floor`` is a length-``num_floors`` tuple whose entry
*f* is the sorted tuple of destinations of passengers waiting at floor *f*.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.enums import ElevatorAction
from utils.settings import ELEVATOR_CAPACITY, MOVE_COST, NUM_FLOORS, STOP_COST

# A successor is (action taken, resulting state, step cost).
Successor = tuple[ElevatorAction, "State", float]


@dataclass(frozen=True, slots=True)
class State:
    """An immutable, hashable snapshot of the search problem.

    Instances should be built via :meth:`create`, which canonicalizes the
    representation (sorting) so that semantically equal states compare and
    hash equal.
    """

    elevator_floor: int
    onboard_dests: tuple[int, ...]
    waiting_by_floor: tuple[tuple[int, ...], ...]

    # -- construction ------------------------------------------------------
    @classmethod
    def create(
        cls,
        elevator_floor: int,
        onboard_dests: tuple[int, ...],
        waiting_by_floor: tuple[tuple[int, ...], ...],
    ) -> "State":
        """Build a canonicalized state with all destination tuples sorted."""
        return cls(
            elevator_floor=elevator_floor,
            onboard_dests=tuple(sorted(onboard_dests)),
            waiting_by_floor=tuple(tuple(sorted(f)) for f in waiting_by_floor),
        )

    # -- goal test ---------------------------------------------------------
    def is_goal(self) -> bool:
        """A state is a goal when no passenger is onboard or waiting anywhere."""
        if self.onboard_dests:
            return False
        return all(len(floor) == 0 for floor in self.waiting_by_floor)

    # -- derived helpers ---------------------------------------------------
    @property
    def num_waiting(self) -> int:
        """Total passengers still waiting across all floors."""
        return sum(len(floor) for floor in self.waiting_by_floor)

    @property
    def num_in_system(self) -> int:
        """Passengers neither delivered yet (onboard + waiting). Used by costs."""
        return len(self.onboard_dests) + self.num_waiting

    def targets(self) -> set[int]:
        """Floors the elevator still must visit (for heuristics).

        Includes onboard destinations, plus the origin *and* destination of
        every waiting passenger. Counting waiting destinations up-front keeps
        the interval-cover heuristic consistent under the zero-cost STOP action.
        """
        result: set[int] = set(self.onboard_dests)
        for floor, dests in enumerate(self.waiting_by_floor):
            if dests:
                result.add(floor)
                result.update(dests)
        return result

    # -- transitions -------------------------------------------------------
    def _stop_result(self) -> "State | None":
        """Apply a STOP (alight then board) at the current floor.

        Returns the resulting state, or ``None`` if STOP would be a no-op
        (nobody alights and nobody can board).
        """
        floor = self.elevator_floor
        # Alight: drop onboard riders whose destination is this floor.
        staying = [d for d in self.onboard_dests if d != floor]
        someone_alighted = len(staying) != len(self.onboard_dests)

        # Board: take waiting passengers here, up to remaining capacity.
        waiting_here = list(self.waiting_by_floor[floor])
        capacity_left = ELEVATOR_CAPACITY - len(staying)
        boarding = waiting_here[:capacity_left] if capacity_left > 0 else []
        remaining = waiting_here[len(boarding):]
        someone_boarded = bool(boarding)

        if not someone_alighted and not someone_boarded:
            return None

        new_onboard = tuple(staying + boarding)
        new_waiting = list(self.waiting_by_floor)
        new_waiting[floor] = tuple(remaining)
        return State.create(floor, new_onboard, tuple(new_waiting))

    @property
    def num_floors(self) -> int:
        """Number of floors this state spans (derived from its own layout)."""
        return len(self.waiting_by_floor)

    def successors(self) -> list[Successor]:
        """Generate all valid (action, next_state, cost) successors.

        Branching factor is at most 3 (MOVE_UP, MOVE_DOWN, STOP); useless
        STOPs are pruned. The upper floor bound is taken from this state's own
        size so the model works for any building height.
        """
        result: list[Successor] = []

        if self.elevator_floor + 1 < self.num_floors:
            up = State.create(
                self.elevator_floor + 1, self.onboard_dests, self.waiting_by_floor
            )
            result.append((ElevatorAction.MOVE_UP, up, MOVE_COST))

        if self.elevator_floor - 1 >= 0:
            down = State.create(
                self.elevator_floor - 1, self.onboard_dests, self.waiting_by_floor
            )
            result.append((ElevatorAction.MOVE_DOWN, down, MOVE_COST))

        stopped = self._stop_result()
        if stopped is not None:
            result.append((ElevatorAction.STOP, stopped, STOP_COST))

        return result

    # -- heuristics --------------------------------------------------------
    def heuristic(self, kind: str = "span") -> float:
        """Estimate of remaining moves to reach the goal.

        Args:
            kind: ``"zero"``, ``"farthest"``, or ``"span"`` (interval-cover,
                the admissible+consistent default for A*).
        """
        targets = self.targets()
        if not targets:
            return 0.0

        f = self.elevator_floor
        lo, hi = min(targets), max(targets)

        if kind == "zero":
            return 0.0
        if kind == "farthest":
            return float(max(abs(f - lo), abs(f - hi)))
        if kind == "span":
            return float((hi - lo) + min(abs(f - lo), abs(f - hi)))
        raise ValueError(f"Unknown heuristic kind: {kind!r}")
