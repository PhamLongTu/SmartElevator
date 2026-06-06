"""Scenario generation for the Smart Elevator game.

A *scenario* is a reproducible set of passengers (and their corresponding hall
:class:`~models.request.Request` calls). Generation is seeded so the exact same
scenario can be replayed -- essential for Compare Mode and for benchmarking
algorithms against one another.

The :class:`ScenarioGenerator` abstraction keeps the *generation strategy*
pluggable. The default :class:`RandomScenarioGenerator` produces a static set
(all passengers present at tick 0). A future dynamic-arrival generator can
assign positive ``spawn_tick`` values without any change to the engine.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from models.passenger import Passenger
from models.request import Request
from utils.settings import NUM_FLOORS


@dataclass
class Scenario:
    """A reproducible batch of passengers and their hall-call requests.

    Attributes:
        seed: The RNG seed used, for reproducibility/logging.
        passengers: All passengers in the scenario, ordered by spawn time.
        requests: The corresponding hall calls (one per passenger).
    """

    seed: int
    num_floors: int = NUM_FLOORS
    passengers: list[Passenger] = field(default_factory=list)
    requests: list[Request] = field(default_factory=list)
    #: Optional difficulty/label metadata for benchmark datasets.
    label: str = ""
    difficulty: str = ""


class ScenarioGenerator(ABC):
    """Strategy interface for producing scenarios."""

    @abstractmethod
    def generate(self) -> Scenario:
        """Produce a fresh :class:`Scenario`."""
        raise NotImplementedError


class RandomScenarioGenerator(ScenarioGenerator):
    """Generate a static set of random passengers with distinct origin/dest.

    Args:
        num_passengers: How many passengers to create.
        num_floors: Number of floors in the building.
        seed: RNG seed; reused as the scenario's seed for reproducibility.
    """

    def __init__(
        self,
        num_passengers: int = 8,
        num_floors: int = NUM_FLOORS,
        seed: int = 0,
    ) -> None:
        if num_floors < 2:
            raise ValueError("Need at least 2 floors to generate passengers.")
        if num_passengers < 0:
            raise ValueError("num_passengers must be non-negative.")
        self.num_passengers = num_passengers
        self.num_floors = num_floors
        self.seed = seed

    def generate(self) -> Scenario:
        """Create the scenario deterministically from the configured seed."""
        rng = random.Random(self.seed)
        scenario = Scenario(seed=self.seed, num_floors=self.num_floors)

        for pid in range(1, self.num_passengers + 1):
            origin = rng.randrange(self.num_floors)
            destination = rng.randrange(self.num_floors)
            while destination == origin:
                destination = rng.randrange(self.num_floors)

            scenario.passengers.append(
                Passenger(
                    id=pid,
                    origin_floor=origin,
                    dest_floor=destination,
                    spawn_tick=0,
                )
            )
            scenario.requests.append(
                Request(
                    id=pid,
                    origin=origin,
                    destination=destination,
                    request_tick=0,
                )
            )

        scenario.passengers.sort(key=lambda p: p.spawn_tick)
        return scenario


class DistributionScenarioGenerator(ScenarioGenerator):
    """Generate scenarios with a controllable *request distribution*.

    The distribution shapes where passengers originate and where they want to
    go, modelling realistic elevator traffic patterns:

    * ``"uniform"`` -- origins and destinations chosen uniformly at random.
    * ``"lobby"`` -- morning up-peak: most passengers start at the ground floor
      heading up (and a few return down).
    * ``"peak"`` -- two-way rush: a mix of strong up traffic from the lobby and
      strong down traffic toward it.

    Args:
        num_passengers: Number of passengers to create.
        num_floors: Building height.
        seed: RNG seed for reproducibility.
        distribution: One of ``"uniform"``, ``"lobby"``, ``"peak"``.
        label: Optional scenario label (e.g. ``"E01"``).
        difficulty: Optional difficulty tag (e.g. ``"Easy"``).
    """

    VALID = ("uniform", "lobby", "peak")

    def __init__(
        self,
        num_passengers: int = 8,
        num_floors: int = NUM_FLOORS,
        seed: int = 0,
        distribution: str = "uniform",
        label: str = "",
        difficulty: str = "",
    ) -> None:
        if num_floors < 2:
            raise ValueError("Need at least 2 floors.")
        if num_passengers < 0:
            raise ValueError("num_passengers must be non-negative.")
        if distribution not in self.VALID:
            raise ValueError(
                f"Unknown distribution {distribution!r}. Valid: {self.VALID}."
            )
        self.num_passengers = num_passengers
        self.num_floors = num_floors
        self.seed = seed
        self.distribution = distribution
        self.label = label
        self.difficulty = difficulty

    def _pair(self, rng: random.Random) -> tuple[int, int]:
        """Return an (origin, destination) pair per the configured distribution."""
        top = self.num_floors - 1
        if self.distribution == "lobby":
            if rng.random() < 0.8:
                return 0, rng.randint(1, top)          # up from lobby
            return rng.randint(1, top), 0              # occasional return
        if self.distribution == "peak":
            if rng.random() < 0.5:
                return 0, rng.randint(1, top)          # up traffic
            return rng.randint(1, top), 0              # down traffic
        # uniform
        origin = rng.randrange(self.num_floors)
        destination = rng.randrange(self.num_floors)
        while destination == origin:
            destination = rng.randrange(self.num_floors)
        return origin, destination

    def generate(self) -> Scenario:
        """Create the scenario deterministically from the configured seed."""
        rng = random.Random(self.seed)
        scenario = Scenario(
            seed=self.seed,
            num_floors=self.num_floors,
            label=self.label,
            difficulty=self.difficulty,
        )

        for pid in range(1, self.num_passengers + 1):
            origin, destination = self._pair(rng)
            scenario.passengers.append(
                Passenger(
                    id=pid,
                    origin_floor=origin,
                    dest_floor=destination,
                    spawn_tick=0,
                )
            )
            scenario.requests.append(
                Request(id=pid, origin=origin, destination=destination, request_tick=0)
            )

        scenario.passengers.sort(key=lambda p: p.spawn_tick)
        return scenario
