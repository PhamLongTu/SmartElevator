from typing import List
import random
from controllers.scenario_row import ScenarioRow
from controllers.scenario_summary import ScenarioSummary
from models.enums import PassengerType
from models.passenger import Passenger
from models.request import Request
from simulation.scenario import Scenario
from utils.settings import NUM_FLOORS


class ScenarioTable:
    """Quản lý bảng cấu hình tối đa 15 hành khách."""

    def __init__(self):
        self.rows: List[ScenarioRow] = [ScenarioRow(i + 1) for i in range(15)]
        self.reset()

    def reset(self):
        for i, row in enumerate(self.rows):
            row.spawn_floor = 0
            row.spawn_side = "LEFT" if i % 2 == 0 else "RIGHT"
            row.destination = (i % 6) + 1
            row.spawn_time = i * 2
            row.passenger_type = PassengerType.NORMAL
            row.enabled = True
            row.is_valid = True
            row.error_message = ""

    def randomize(self, preset: str = "Medium"):
        max_time = 30
        urgent_prob = 0.2

        if preset == "Easy":
            max_time = 100
            urgent_prob = 0.1
        elif preset == "Hard":
            max_time = 40
            urgent_prob = 0.4
        elif preset == "Stress Test":
            max_time = 15
            urgent_prob = 0.6

        for i, row in enumerate(self.rows):
            row.spawn_floor = random.randint(0, NUM_FLOORS - 1)
            row.destination = random.randint(0, NUM_FLOORS - 1)
            while row.destination == row.spawn_floor:
                row.destination = random.randint(0, NUM_FLOORS - 1)

            row.spawn_side = random.choice(["LEFT", "RIGHT"])
            if i == 0:
                row.spawn_time = 0
            else:
                row.spawn_time = random.randint(0, max_time)
            row.passenger_type = PassengerType.URGENT if random.random() < urgent_prob else PassengerType.NORMAL

    def get_requests(self) -> List:
        """Chỉ trả về request của các dòng đang bật."""
        return [row.to_request() for row in self.rows if row.enabled]

    def export_data(self) -> List[dict]:
        """Xuất dữ liệu bảng thành danh sách dict."""
        return [{
            "spawn_floor": r.spawn_floor,
            "spawn_side": r.spawn_side,
            "destination": r.destination,
            "spawn_time": r.spawn_time,
            "passenger_type": r.passenger_type,
            "enabled": r.enabled
        } for r in self.rows]

    def import_data(self, data: List[dict]):
        """Khôi phục bảng từ danh sách dict."""
        if not data or len(data) != len(self.rows):
            return
        for i, d in enumerate(data):
            self.rows[i].spawn_floor = d["spawn_floor"]
            self.rows[i].spawn_side = d["spawn_side"]
            self.rows[i].destination = d["destination"]
            self.rows[i].spawn_time = d["spawn_time"]
            self.rows[i].passenger_type = d["passenger_type"]
            self.rows[i].enabled = d.get("enabled", True)

    def to_scenario(self, seed: int = 0) -> Scenario:
        """Chuyển dữ liệu bảng thành ``Scenario``."""
        summary = ScenarioSummary.calculate(self.rows)
        scenario = Scenario(
            seed=seed,
            num_floors=NUM_FLOORS,
            label="Custom Scenario",
            difficulty=summary["difficulty"]
        )
        for row in self.rows:
            if not row.enabled:
                continue
            req = row.to_request()
            scenario.passengers.append(Passenger(
                id=req.id,
                origin_floor=req.spawn_floor,
                dest_floor=req.destination,
                spawn_time=req.spawn_time,
                spawn_side=req.spawn_side,
                passenger_type=req.passenger_type
            ))
            scenario.requests.append(Request(
                id=req.id,
                origin=req.spawn_floor,
                destination=req.destination,
                request_time=req.spawn_time,
            ))
        return scenario
