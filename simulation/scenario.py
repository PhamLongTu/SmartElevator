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
    passengers: list[Passenger] = field(default_factory=list)
    requests: list[Request] = field(default_factory=list)


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
        scenario = Scenario(seed=self.seed)

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
