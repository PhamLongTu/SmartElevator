"""Bộ máy mô phỏng luật chạy của Smart Elevator."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.building import Building
from models.elevator import Elevator
from models.enums import Direction, ElevatorAction, GameMode, PassengerStatus, PassengerType
from models.passenger import Passenger
from models.passenger_request import PassengerRequest
from models.request import Request
from models.state import State
from simulation.scenario import Scenario, ScenarioGenerator
from statistics.statistics_manager import StatisticsManager
from utils.settings import NUM_FLOORS


@dataclass
class StepResult:
    """Kết quả sau khi thực hiện một hành động mô phỏng."""

    action: ElevatorAction
    time: float
    boarded: list[Passenger] = field(default_factory=list)
    alighted: list[Passenger] = field(default_factory=list)
    left: list[Passenger] = field(default_factory=list)
    duration: float = 0.0
    finished: bool = False


class SimulationEngine:
    """Kết nối hành động của AI/người chơi với trạng thái thế giới."""

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

        self._pending: list[PassengerRequest] = []
        self._walking: list[PassengerRequest] = []
        self._requests_by_id: dict[int, Request] = {}
        self.extra_finished_check: callable[[], bool] | None = None

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
        """Đặt lại thế giới và thống kê cho scenario đã nạp."""
        self.building = Building(num_floors=self.num_floors)
        self.time = 0.0
        self.stats.reset()
        self._pending = []
        self._walking = []
        self.delivered_passengers: list[Passenger] = []

        if self.scenario is not None:
            self._pending = sorted(
                (
                    PassengerRequest(
                        id=p.id,
                        spawn_floor=p.origin_floor,
                        destination=p.dest_floor,
                        spawn_time=getattr(p, "spawn_time", p.spawn_tick if hasattr(p, "spawn_tick") else 0.0),
                        spawn_side=getattr(p, "spawn_side", "LEFT"),
                        passenger_type=getattr(p, "passenger_type", PassengerType.NORMAL)
                    )
                    for p in self.scenario.passengers
                ),
                key=lambda p: p.spawn_time,
            )
            self._requests_by_id = {r.id: r for r in self.scenario.requests}

        self._release_due_passengers()

    def _release_due_passengers(self) -> None:
        """Chuyển khách đã tới giờ spawn sang trạng thái đang đi vào."""
        while self._pending and self._pending[0].spawn_time <= self.time:
            req = self._pending.pop(0)
            req.status = "WALKING"
            req.walking_progress = 0.0
            self._walking.append(req)

    def _advance_walking(self, dt: float) -> None:
        """Cập nhật tiến trình đi vào cửa thang của hành khách."""
        walk_duration = 1.0
        if dt <= 0:
            return

        completed = []
        for npc in self._walking:
            npc.walking_progress += dt / walk_duration
            if npc.walking_progress >= 1.0:
                npc.walking_progress = 1.0
                npc.status = "ARRIVED"
                completed.append(npc)

        for npc in completed:
            self._walking.remove(npc)
            p = Passenger(
                id=npc.id,
                origin_floor=npc.spawn_floor,
                dest_floor=npc.destination,
                spawn_time=self.time,
                spawn_side=npc.spawn_side,
                passenger_type=npc.passenger_type,
                status=PassengerStatus.WAITING
            )
            self.building.add_passenger(p)

    def _purge_expired_passengers(self, result: StepResult) -> None:
        """Loại khách chờ đã hết hạn khỏi các tầng."""
        for floor in range(self.num_floors):
            waiters = self.building.waiting_at(floor)
            expired = [p for p in waiters if p.status == PassengerStatus.LEFT]
            for p in expired:
                self.building.remove_waiting(floor, p)
                result.left.append(p)
                self.stats.record_failure(p)

    def apply(self, action: ElevatorAction) -> StepResult:
        """Thực hiện một hành động của thang và cập nhật thế giới."""
        result = StepResult(action=action, time=self.time)

        if action in (ElevatorAction.MOVE_UP, ElevatorAction.MOVE_DOWN):
            self._apply_move(action, result)
        elif action is ElevatorAction.STOP:
            self._apply_stop(result)
        elif action is ElevatorAction.IDLE:
            dt = 1.0
            self.time += dt
            result.duration = dt
            self.building.update_time(dt)
            self._advance_walking(dt)
            self._purge_expired_passengers(result)
            self.stats.record_move(0)

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

        dt = 1.0
        elevator.move(direction)
        self.time += dt
        result.duration = dt
        self.building.update_time(dt)
        self._advance_walking(dt)
        self._purge_expired_passengers(result)
        self.stats.record_move(1)

    def _apply_stop(self, result: StepResult) -> None:
        """Phục vụ tầng hiện tại: cho khách xuống rồi đón khách lên."""
        elevator: Elevator = self.building.elevator
        floor = elevator.current_floor

        alighted = elevator.alight(floor, self.time)
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

        interactions = len(alighted) + len(newly_boarded)
        dt = max(1.0, interactions * 0.5)

        self.time += dt
        result.duration = dt
        self.building.update_time(dt)
        self._advance_walking(dt)
        self._purge_expired_passengers(result)

        for p in alighted:
            self.stats.record_delivery(p)
            self.delivered_passengers.append(p)
        for p in newly_boarded:
            self.stats.record_pickup(p)

        result.alighted = alighted
        result.boarded = newly_boarded

    def is_finished(self) -> bool:
        ext_check = self.extra_finished_check() if self.extra_finished_check else True
        return not self._pending and not self._walking and self.building.all_served() and ext_check

    def snapshot(self) -> State:
        return self.building.to_state(self.time)
