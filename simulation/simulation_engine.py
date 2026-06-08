"""The :class:`SimulationEngine`.

The engine is the authoritative rule/tick engine for the game. It owns the
mutable :class:`~models.building.Building`, advances simulation time, applies
elevator actions (updating passenger timelines and the elevator), generates
scenarios (passengers + hall-call requests), and feeds the
:class:`~statistics.statistics_manager.StatisticsManager`.

Design notes:

* **Time model** follows the cost design: a ``MOVE`` advances the clock by one
  tick; a ``STOP`` (serve) is instantaneous (0 ticks). This keeps measured
  waiting/journey times consistent with the search cost.
* **Boarding order** at a ``STOP`` is by ascending destination floor, matching
  ``State._stop_result`` so that an AI plan computed over :class:`State`
  executes identically in the live simulation (the capacity-overflow
  determinism rule from the state-space design).
* **Extensibility**: scenario generation is injected via a
  :class:`~simulation.scenario.ScenarioGenerator`. Passengers carry a
  ``spawn_tick`` and are released when due, so a dynamic-arrival generator
  works with no engine changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.building import Building
from models.elevator import Elevator
from models.enums import Direction, ElevatorAction, GameMode, PassengerStatus, PassengerType
from models.passenger import Passenger
from models.request import Request
from models.state import State
from simulation.scenario import Scenario, ScenarioGenerator
from statistics.statistics_manager import StatisticsManager
from utils.settings import NUM_FLOORS


@dataclass
class StepResult:
    """Outcome of applying a single action, for views/controllers to react to.

    Attributes:
        action: The action that was applied.
        time: Simulation time after the action.
        boarded: Passengers that boarded during this step.
        alighted: Passengers that were delivered during this step.
        left: Passengers who left the floor during this step (deadline expired).
        finished: Whether the simulation is now complete.
    """

    action: ElevatorAction
    time: float
    boarded: list[Passenger] = field(default_factory=list)
    alighted: list[Passenger] = field(default_factory=list)
    left: list[Passenger] = field(default_factory=list)
    finished: bool = False


class SimulationEngine:
    """Authoritative dynamic engine bridging AI/player actions to the world."""

    def __init__(
        self,
        stats: StatisticsManager | None = None,
        generator: ScenarioGenerator | None = None,
        num_floors: int = NUM_FLOORS,
    ) -> None:
        self.num_floors = num_floors
        self.stats = stats if stats is not None else StatisticsManager()
        self.generator = generator
        self.mode: GameMode = GameMode.MANUAL

        self.building: Building = Building(num_floors=num_floors)
        self.time: float = 0.0
        self.scenario: Scenario | None = None

        self._pending: list[Passenger] = []
        self._requests_by_id: dict[int, Request] = {}

    def new_scenario(self) -> Scenario:
        if self.generator is None:
            raise RuntimeError("No ScenarioGenerator configured on this engine.")
        scenario = self.generator.generate()
        self.load_scenario(scenario)
        return scenario

    def load_scenario(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.num_floors = scenario.num_floors
        self.reset()

    def reset(self) -> None:
        """Reset the world and statistics to the start of the loaded scenario."""
        self.building = Building(num_floors=self.num_floors)
        self.time = 0.0
        self.stats.reset()
        self._pending = []
        self._requests_by_id = {}
        self.delivered_passengers: list[Passenger] = []

        if self.scenario is not None:
            self._pending = sorted(
                (
                    Passenger(
                        id=p.id,
                        origin_floor=p.origin_floor,
                        dest_floor=p.dest_floor,
                        spawn_time=getattr(p, 'spawn_time', p.spawn_tick if hasattr(p, 'spawn_tick') else 0.0),
                        passenger_type=getattr(p, 'passenger_type', PassengerType.NORMAL)
                    )
                    for p in self.scenario.passengers
                ),
                key=lambda p: p.spawn_time,
            )
            self._requests_by_id = {r.id: r for r in self.scenario.requests}

        self._release_due_passengers()

    def _release_due_passengers(self) -> None:
        """Move passengers whose spawn_time has arrived into the building."""
        while self._pending and self._pending[0].spawn_time <= self.time:
            self.building.add_passenger(self._pending.pop(0))

    def _purge_expired_passengers(self, result: StepResult) -> None:
        """Remove passengers from floors or elevator who have expired."""
        # 1. From floors (WAITING -> LEFT)
        for floor in range(self.num_floors):
            waiters = self.building.waiting_at(floor)
            expired = [p for p in waiters if p.status == PassengerStatus.LEFT]
            for p in expired:
                self.building.remove_waiting(floor, p)
                result.left.append(p)
                self.stats.record_failure(p)

        # 2. On-board passengers remain in the cab even if they become ANGRY.
        # They will count toward 'angry_count' upon delivery instead of disappearing.
        pass

    def apply(self, action: ElevatorAction) -> StepResult:
        """Apply one elevator action, updating world, time, and statistics."""
        result = StepResult(action=action, time=self.time)

        if action in (ElevatorAction.MOVE_UP, ElevatorAction.MOVE_DOWN):
            self._apply_move(action, result)
        elif action is ElevatorAction.STOP:
            self._apply_stop(result)

        self._release_due_passengers()
        result.time = self.time
        result.finished = self.is_finished()
        return result

    def _apply_move(self, action: ElevatorAction, result: StepResult) -> None:
        direction = (
            Direction.UP if action is ElevatorAction.MOVE_UP else Direction.DOWN
        )
        elevator = self.building.elevator
        target = elevator.current_floor + direction.value
        if not 0 <= target < elevator.num_floors:
            return

        dt = 1.0 # 1.0 time unit per floor
        elevator.move(direction)
        self.time += dt
        self.building.update_time(dt)
        self._purge_expired_passengers(result)
        self.stats.record_move(1)

    def _apply_stop(self, result: StepResult) -> None:
        """Serve the current floor: alight arrivals, then board."""
        elevator: Elevator = self.building.elevator
        floor = elevator.current_floor

        # 1. Alight
        alighted = elevator.alight(floor, self.time)
        
        # 2. Board
        #    Sorted by destination to match AI expectations
        waiting = sorted(
            self.building.waiting_at(floor), key=lambda p: p.dest_floor
        )
        newly_boarded = []
        for passenger in waiting:
            if not elevator.can_board():
                break
            elevator.board(passenger, self.time)
            self.building.remove_waiting(floor, passenger)
            newly_boarded.append(passenger)

        # Time cost for STOP in v2: 0.5 per passenger interaction
        interactions = len(alighted) + len(newly_boarded)
        dt = interactions * 0.5
        
        if dt > 0:
            self.time += dt
            self.building.update_time(dt)
            # After time update, some people might have LEFT or became ANGRY
            self._purge_expired_passengers(result)

        # Records
        for p in alighted:
            self.stats.record_delivery(p)
            self.delivered_passengers.append(p)
        for p in newly_boarded:
            self.stats.record_pickup(p)
        
        result.alighted = alighted
        result.boarded = newly_boarded

    def is_finished(self) -> bool:
        return not self._pending and self.building.all_served()

    def snapshot(self) -> State:
        return self.building.to_state(self.time)
