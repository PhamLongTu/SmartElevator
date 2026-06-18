from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from models.passenger import Passenger
from models.request import Request
from models.enums import PassengerType
from utils.settings import NUM_FLOORS

@dataclass
class Scenario:
    """Một lượt scenario có thể tái lập gồm hành khách và request gọi thang."""

    seed: int
    num_floors: int = NUM_FLOORS
    passengers: list[Passenger] = field(default_factory=list)
    requests: list[Request] = field(default_factory=list)
    label: str = ""
    difficulty: str = ""


class ScenarioGenerator(ABC):
    """Interface chiến lược để sinh scenario."""

    @abstractmethod
    def generate(self) -> Scenario:
        """Sinh một :class:`Scenario` mới."""
        raise NotImplementedError


class RandomScenarioGenerator(ScenarioGenerator):
    """Sinh hành khách ngẫu nhiên với thời điểm spawn và loại khách động."""

    def __init__(
        self,
        num_passengers: int = 8,
        num_floors: int = NUM_FLOORS,
        seed: int = 0,
        urgent_prob: float = 0.2,
        spawn_interval: float = 12.0,
    ) -> None:
        self.num_passengers = num_passengers
        self.num_floors = num_floors
        self.seed = seed
        self.urgent_prob = urgent_prob
        self.spawn_interval = spawn_interval

    def generate(self) -> Scenario:
        rng = random.Random(self.seed)
        scenario = Scenario(seed=self.seed, num_floors=self.num_floors)
        current_spawn_time = 0.0

        for pid in range(1, self.num_passengers + 1):
            origin = rng.randrange(self.num_floors)
            destination = rng.randrange(self.num_floors)
            while destination == origin:
                destination = rng.randrange(self.num_floors)

            p_type = PassengerType.URGENT if rng.random() < self.urgent_prob else PassengerType.NORMAL
            
            scenario.passengers.append(
                Passenger(
                    id=pid,
                    origin_floor=origin,
                    dest_floor=destination,
                    spawn_time=current_spawn_time,
                    passenger_type=p_type,
                )
            )
            scenario.requests.append(
                Request(
                    id=pid,
                    origin=origin,
                    destination=destination,
                    request_time=current_spawn_time,
                )
            )
            current_spawn_time += rng.uniform(0, self.spawn_interval)

        return scenario


class DistributionScenarioGenerator(ScenarioGenerator):
    """Sinh các mẫu traffic có cấu trúc."""

    VALID = ("uniform", "lobby", "peak")

    def __init__(
        self,
        num_passengers: int = 8,
        num_floors: int = NUM_FLOORS,
        seed: int = 0,
        distribution: str = "uniform",
        urgent_prob: float = 0.2,
        spawn_interval: float = 5.0,
        label: str = "",
        difficulty: str = "",
    ) -> None:
        self.num_passengers = num_passengers
        self.num_floors = num_floors
        self.seed = seed
        self.distribution = distribution
        self.urgent_prob = urgent_prob
        self.spawn_interval = spawn_interval
        self.label = label
        self.difficulty = difficulty

    def _pair(self, rng: random.Random) -> tuple[int, int]:
        top = self.num_floors - 1
        if self.distribution == "lobby":
            if rng.random() < 0.8:
                return 0, rng.randint(1, top)
            return rng.randint(1, top), 0
        if self.distribution == "peak":
            if rng.random() < 0.5:
                return 0, rng.randint(1, top)
            return rng.randint(1, top), 0
        origin = rng.randrange(self.num_floors)
        destination = rng.randrange(self.num_floors)
        while destination == origin:
            destination = rng.randrange(self.num_floors)
        return origin, destination

    def generate(self) -> Scenario:
        rng = random.Random(self.seed)
        scenario = Scenario(
            seed=self.seed,
            num_floors=self.num_floors,
            label=self.label,
            difficulty=self.difficulty,
        )
        current_spawn_time = 0.0

        for pid in range(1, self.num_passengers + 1):
            origin, destination = self._pair(rng)
            p_type = PassengerType.URGENT if rng.random() < self.urgent_prob else PassengerType.NORMAL
            
            scenario.passengers.append(
                Passenger(
                    id=pid,
                    origin_floor=origin,
                    dest_floor=destination,
                    spawn_time=current_spawn_time,
                    passenger_type=p_type,
                )
            )
            scenario.requests.append(
                Request(
                    id=pid,
                    origin=origin,
                    destination=destination,
                    request_time=current_spawn_time
                )
            )
            current_spawn_time += rng.uniform(0, self.spawn_interval)

        return scenario
