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
from models.enums import Direction, ElevatorAction, GameMode
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
        tick: Simulation tick after the action.
        boarded: Passengers that boarded during this step.
        alighted: Passengers that were delivered during this step.
        finished: Whether the simulation is now complete.
    """

    action: ElevatorAction
    tick: int
    boarded: list[Passenger] = field(default_factory=list)
    alighted: list[Passenger] = field(default_factory=list)
    finished: bool = False


class SimulationEngine:
    """Authoritative tick engine bridging AI/player actions to the live world.

    Args:
        stats: Statistics collector; a fresh one is created if omitted.
        generator: Optional scenario generator for :meth:`new_scenario`.
        num_floors: Number of floors in the building.
    """

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
        self.tick: int = 0
        self.scenario: Scenario | None = None

        # Passengers not yet released into the building, ascending by spawn_tick.
        self._pending: list[Passenger] = []
        self._requests_by_id: dict[int, Request] = {}

    # ------------------------------------------------------------------
    # Scenario management (generate passengers + requests)
    # ------------------------------------------------------------------
    def new_scenario(self) -> Scenario:
        """Generate and load a fresh scenario using the injected generator.

        Raises:
            RuntimeError: If no generator was provided.
        """
        if self.generator is None:
            raise RuntimeError("No ScenarioGenerator configured on this engine.")
        scenario = self.generator.generate()
        self.load_scenario(scenario)
        return scenario

    def load_scenario(self, scenario: Scenario) -> None:
        """Load a specific scenario, resetting the world.

        Using the *same* scenario object on two engines is how Compare Mode
        guarantees the player and AI face an identical situation.
        """
        self.scenario = scenario
        # Adopt the scenario's building height (datasets may vary floors).
        self.num_floors = scenario.num_floors
        self.reset()

    def reset(self) -> None:
        """Reset the world and statistics to the start of the loaded scenario."""
        self.building = Building(num_floors=self.num_floors)
        self.tick = 0
        self.stats.reset()
        self._pending = []
        self._requests_by_id = {}

        if self.scenario is not None:
            # Copy passengers so re-runs start fresh (don't mutate the scenario).
            self._pending = sorted(
                (
                    Passenger(
                        id=p.id,
                        origin_floor=p.origin_floor,
                        dest_floor=p.dest_floor,
                        spawn_tick=p.spawn_tick,
                    )
                    for p in self.scenario.passengers
                ),
                key=lambda p: p.spawn_tick,
            )
            self._requests_by_id = {r.id: r for r in self.scenario.requests}

        self._release_due_passengers()

    # ------------------------------------------------------------------
    # Time + spawning
    # ------------------------------------------------------------------
    def _release_due_passengers(self) -> None:
        """Move passengers whose spawn_tick has arrived into the building."""
        while self._pending and self._pending[0].spawn_tick <= self.tick:
            self.building.add_passenger(self._pending.pop(0))

    # ------------------------------------------------------------------
    # Applying actions (update elevator state + advance time)
    # ------------------------------------------------------------------
    def apply(self, action: ElevatorAction) -> StepResult:
        """Apply one elevator action, updating world, time, and statistics."""
        result = StepResult(action=action, tick=self.tick)

        if action in (ElevatorAction.MOVE_UP, ElevatorAction.MOVE_DOWN):
            self._apply_move(action)
        elif action is ElevatorAction.STOP:
            self._apply_stop(result)
        # ElevatorAction.IDLE intentionally does nothing.

        self._release_due_passengers()
        result.tick = self.tick
        result.finished = self.is_finished()
        return result

    def _apply_move(self, action: ElevatorAction) -> None:
        """Move the elevator one floor and advance the clock by one tick."""
        direction = (
            Direction.UP if action is ElevatorAction.MOVE_UP else Direction.DOWN
        )
        self.building.elevator.move(direction)
        self.tick += 1
        self.stats.record_move(1)

    def _apply_stop(self, result: StepResult) -> None:
        """Serve the current floor: alight arrivals, then board (by destination)."""
        elevator: Elevator = self.building.elevator
        floor = elevator.current_floor

        # 1. Alight everyone whose destination is this floor.
        alighted = elevator.alight(floor, self.tick)
        for passenger in alighted:
            self.stats.record_delivery(passenger)
            request = self._requests_by_id.get(passenger.id)
            if request is not None:
                request.mark_served(self.tick)
        result.alighted = alighted

        # 2. Board waiting passengers, ascending by destination, up to capacity.
        #    Matches State._stop_result so AI plans execute faithfully.
        waiting = sorted(
            self.building.waiting_at(floor), key=lambda p: p.dest_floor
        )
        for passenger in waiting:
            if not elevator.can_board():
                break
            elevator.board(passenger, self.tick)
            self.building.remove_waiting(floor, passenger)
            self.stats.record_pickup(passenger)
            result.boarded.append(passenger)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    def is_finished(self) -> bool:
        """Whether all passengers are delivered and none remain to spawn."""
        return not self._pending and self.building.all_served()

    def snapshot(self) -> State:
        """Return an immutable :class:`State` of the current world for planning."""
        return self.building.to_state()
