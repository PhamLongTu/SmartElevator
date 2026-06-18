from typing import List
from models.passenger_request import PassengerRequest
from models.passenger import Passenger
from models.enums import PassengerStatus


class SpawnController:
    """Quản lý vòng đời hành khách từ cấu hình spawn đến hàng chờ trong tòa nhà."""

    def __init__(self, engine):
        self.engine = engine
        self.pending_requests: List[PassengerRequest] = []
        self.walking_npcs: List[PassengerRequest] = []
        self.walk_duration = 1.0

    def load_scenario(self, requests: List[PassengerRequest]):
        self.pending_requests = sorted(requests, key=lambda r: r.spawn_time)
        self.walking_npcs = []

    def update(self, dt: float):
        while self.pending_requests and self.pending_requests[0].spawn_time <= self.engine.time:
            req = self.pending_requests.pop(0)
            req.status = "WALKING"
            req.walking_progress = 0.0
            self.walking_npcs.append(req)

        completed = []
        for npc in self.walking_npcs:
            npc.walking_progress += dt / self.walk_duration
            if npc.walking_progress >= 1.0:
                npc.walking_progress = 1.0
                npc.status = "ARRIVED"
                completed.append(npc)

        for npc in completed:
            self.walking_npcs.remove(npc)
            p = Passenger(
                id=npc.id,
                origin_floor=npc.spawn_floor,
                dest_floor=npc.destination,
                spawn_time=self.engine.time,
                spawn_side=npc.spawn_side,
                passenger_type=npc.passenger_type,
                status=PassengerStatus.WAITING
            )
            self.engine.building.add_passenger(p)
            npc.status = "SERVED"

    def is_finished(self) -> bool:
        """Trả về True khi không còn hành khách đang chờ spawn hoặc đang đi vào."""
        return not self.pending_requests and not self.walking_npcs
