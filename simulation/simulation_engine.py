"""Thực thể :class:`SimulationEngine` (Bộ máy Mô phỏng).

Bộ máy này là trung tâm điều hành các quy tắc/nhịp (tick) của trò chơi. Nó sở hữu 
:class:`~models.building.Building` có thể thay đổi, thúc đẩy thời gian mô phỏng, áp dụng 
các hành động của thang máy (cập nhật tiến trình của hành khách và thang máy), tạo ra 
các kịch bản (hành khách + yêu cầu gọi thang), và cung cấp dữ liệu cho 
:class:`~statistics.statistics_manager.StatisticsManager`.

Ghi chú thiết kế:

* **Mô hình thời gian** tuân theo thiết kế chi phí: một thao tác ``MOVE`` (Di chuyển) sẽ cộng 
  một nhịp vào đồng hồ; một thao tác ``STOP`` (Dừng/Phục vụ) diễn ra tức thì (0 nhịp). Điều này 
  giúp đo lường thời gian chờ/hành trình nhất quán với chi phí tìm kiếm.
* **Thứ tự lên thang** tại một điểm ``STOP`` dựa trên tầng đích tăng dần, khớp với 
  ``State._stop_result`` để kế hoạch AI được tính toán trên :class:`State` sẽ 
  thực thi giống hệt trong mô phỏng thực tế (quy tắc định mệnh khi tràn sức chứa từ thiết kế 
  không gian trạng thái).
* **Khả năng mở rộng**: việc tạo kịch bản được đưa vào thông qua 
  :class:`~simulation.scenario.ScenarioGenerator`. Hành khách mang theo 
  ``spawn_tick`` và được giải phóng khi đến hạn, vì vậy bộ tạo lượt khách đến động 
  có thể hoạt động mà không cần thay đổi bộ máy.
"""

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
    """Kết quả của việc thực hiện một hành động duy nhất, để views/controllers phản hồi.

    Thuộc tính:
        action: Hành động đã được thực hiện.
        time: Thời gian mô phỏng sau hành động.
        boarded: Các hành khách đã lên thang trong bước này.
        alighted: Các hành khách đã xuống thang (được giao) trong bước này.
        left: Các hành khách đã rời khỏi tầng trong bước này (hết hạn chờ).
        finished: Mô phỏng đã hoàn thành hay chưa.
    """

    action: ElevatorAction
    time: float
    boarded: list[Passenger] = field(default_factory=list)
    alighted: list[Passenger] = field(default_factory=list)
    left: list[Passenger] = field(default_factory=list)
    duration: float = 0.0
    finished: bool = False


class SimulationEngine:
    """Bộ máy động đóng vai trò là trung tâm kết nối các hành động của AI/người chơi với thế giới."""

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
        """Đặt lại thế giới và số liệu thống kê về thời điểm bắt đầu của kịch bản đã nạp."""
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
                        spawn_time=getattr(p, 'spawn_time', p.spawn_tick if hasattr(p, 'spawn_tick') else 0.0),
                        spawn_side=getattr(p, 'spawn_side', "LEFT"),
                        passenger_type=getattr(p, 'passenger_type', PassengerType.NORMAL)
                    )
                    for p in self.scenario.passengers
                ),
                key=lambda p: p.spawn_time,
            )
            self._requests_by_id = {r.id: r for r in self.scenario.requests}

        self._release_due_passengers()

    def _release_due_passengers(self) -> None:
        """Chuyển các hành khách từ trạng thái chờ sang trạng thái ĐANG ĐI BỘ (WALKING)."""
        while self._pending and self._pending[0].spawn_time <= self.time:
            req = self._pending.pop(0)
            req.status = "WALKING"
            req.walking_progress = 0.0
            self._walking.append(req)

    def _advance_walking(self, dt: float) -> None:
        """Cập nhật tiến trình đi bộ của hành khách dựa trên bước thời gian mô phỏng."""
        WALK_DURATION = 1.0 # 1.0 đơn vị mô phỏng để đến cửa thang
        if dt <= 0: return

        completed = []
        for npc in self._walking:
            npc.walking_progress += dt / WALK_DURATION
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
                spawn_time=self.time, # Thời gian họ thực sự đến cửa thang
                spawn_side=npc.spawn_side,
                passenger_type=npc.passenger_type,
                status=PassengerStatus.WAITING
            )
            self.building.add_passenger(p)

    def _purge_expired_passengers(self, result: StepResult) -> None:
        """Loại bỏ các hành khách đã hết hạn khỏi các tầng hoặc thang máy."""
        # 1. Từ các tầng (WAITING -> LEFT)
        for floor in range(self.num_floors):
            waiters = self.building.waiting_at(floor)
            expired = [p for p in waiters if p.status == PassengerStatus.LEFT]
            for p in expired:
                self.building.remove_waiting(floor, p)
                result.left.append(p)
                self.stats.record_failure(p)

        # 2. Hành khách đã ở trên thang máy vẫn được giữ lại kể cả khi họ trở nên GIẬN DỮ (ANGRY).
        # Họ sẽ được tính vào 'angry_count' khi xuống thang thay vì biến mất.
        pass

    def apply(self, action: ElevatorAction) -> StepResult:
        """Thực hiện một hành động của thang máy, cập nhật thế giới, thời gian và thống kê."""
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
            self.stats.record_move(0) # IDLE được tính là di chuyển 0 đơn vị

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

        dt = 1.0 # 1.0 đơn vị thời gian cho mỗi tầng
        elevator.move(direction)
        self.time += dt
        result.duration = dt
        self.building.update_time(dt)
        self._advance_walking(dt)
        self._purge_expired_passengers(result)
        self.stats.record_move(1)

    def _apply_stop(self, result: StepResult) -> None:
        """Phục vụ tầng hiện tại: cho khách xuống, sau đó đón khách lên."""
        elevator: Elevator = self.building.elevator
        floor = elevator.current_floor

        # 1. Xuống thang
        alighted = elevator.alight(floor, self.time)
        
        # 2. Lên thang
        #    Được sắp xếp theo tầng đích để khớp với kỳ vọng của AI
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

        # Chi phí thời gian cho lệnh STOP ở v2: 0.5 giây cho mỗi tương tác với hành khách
        # Tối thiểu 1.0 để mở/đóng cửa
        interactions = len(alighted) + len(newly_boarded)
        dt = max(1.0, interactions * 0.5)
        
        self.time += dt
        result.duration = dt
        self.building.update_time(dt)
        self._advance_walking(dt)
        # Sau khi cập nhật thời gian, một số người có thể đã RỜI ĐI (LEFT) hoặc trở nên GIẬN DỮ (ANGRY)
        self._purge_expired_passengers(result)

        # Ghi chép
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
