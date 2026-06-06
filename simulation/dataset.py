"""Structured benchmark dataset: 30 scenarios across three difficulty levels.

The dataset is defined declaratively as a list of :class:`ScenarioSpec` entries
and materialized into reproducible :class:`~simulation.scenario.Scenario`
objects via :func:`build_dataset`. Each spec fully specifies the three required
fields:

* **floors** -- building height.
* **passenger count** -- number of passengers.
* **request distribution** -- traffic pattern (``uniform`` / ``lobby`` / ``peak``).

Difficulty is shaped by all three axes together:

============  ======  ==========  ==============================================
Difficulty    Floors  Passengers  Character
============  ======  ==========  ==============================================
Easy          5-6     2-4         small building, light, simple traffic
Medium        8-10    5-8         full building, moderate, mixed traffic
Hard          12-15   10-16       tall building, heavy, peak two-way traffic
============  ======  ==========  ==============================================

Seeds are fixed so the dataset is identical on every machine and run.
"""

from __future__ import annotations

from dataclasses import dataclass

from simulation.scenario import DistributionScenarioGenerator, Scenario


@dataclass(frozen=True)
class ScenarioSpec:
    """Declarative specification of one benchmark scenario.

    Attributes:
        label: Unique short id, e.g. ``"E01"``.
        difficulty: ``"Easy"``, ``"Medium"`` or ``"Hard"``.
        floors: Building height.
        passengers: Passenger count.
        distribution: Request distribution pattern.
        seed: RNG seed for reproducibility.
    """

    label: str
    difficulty: str
    floors: int
    passengers: int
    distribution: str
    seed: int

    def build(self) -> Scenario:
        """Materialize this spec into a reproducible :class:`Scenario`."""
        return DistributionScenarioGenerator(
            num_passengers=self.passengers,
            num_floors=self.floors,
            seed=self.seed,
            distribution=self.distribution,
            label=self.label,
            difficulty=self.difficulty,
        ).generate()


# --- The 30-scenario dataset (10 Easy, 10 Medium, 10 Hard) ----------------
DATASET: tuple[ScenarioSpec, ...] = (
    # Easy: small buildings, few passengers, simple traffic.
    ScenarioSpec("E01", "Easy", 5, 2, "uniform", 101),
    ScenarioSpec("E02", "Easy", 5, 3, "uniform", 102),
    ScenarioSpec("E03", "Easy", 6, 3, "lobby", 103),
    ScenarioSpec("E04", "Easy", 5, 4, "uniform", 104),
    ScenarioSpec("E05", "Easy", 6, 2, "lobby", 105),
    ScenarioSpec("E06", "Easy", 6, 4, "uniform", 106),
    ScenarioSpec("E07", "Easy", 5, 3, "lobby", 107),
    ScenarioSpec("E08", "Easy", 6, 4, "lobby", 108),
    ScenarioSpec("E09", "Easy", 5, 2, "uniform", 109),
    ScenarioSpec("E10", "Easy", 6, 3, "uniform", 110),
    # Medium: full-size building, moderate load, mixed traffic.
    ScenarioSpec("M01", "Medium", 8, 5, "uniform", 201),
    ScenarioSpec("M02", "Medium", 10, 6, "lobby", 202),
    ScenarioSpec("M03", "Medium", 10, 7, "uniform", 203),
    ScenarioSpec("M04", "Medium", 8, 6, "peak", 204),
    ScenarioSpec("M05", "Medium", 10, 8, "lobby", 205),
    ScenarioSpec("M06", "Medium", 9, 5, "uniform", 206),
    ScenarioSpec("M07", "Medium", 10, 7, "peak", 207),
    ScenarioSpec("M08", "Medium", 8, 8, "uniform", 208),
    ScenarioSpec("M09", "Medium", 10, 6, "peak", 209),
    ScenarioSpec("M10", "Medium", 9, 7, "lobby", 210),
    # Hard: tall buildings, heavy load, demanding peak two-way traffic.
    ScenarioSpec("H01", "Hard", 12, 10, "peak", 301),
    ScenarioSpec("H02", "Hard", 12, 12, "uniform", 302),
    ScenarioSpec("H03", "Hard", 14, 12, "peak", 303),
    ScenarioSpec("H04", "Hard", 15, 14, "lobby", 304),
    ScenarioSpec("H05", "Hard", 14, 14, "uniform", 305),
    ScenarioSpec("H06", "Hard", 15, 16, "peak", 306),
    ScenarioSpec("H07", "Hard", 12, 13, "peak", 307),
    ScenarioSpec("H08", "Hard", 14, 15, "lobby", 308),
    ScenarioSpec("H09", "Hard", 15, 12, "uniform", 309),
    ScenarioSpec("H10", "Hard", 13, 16, "peak", 310),
)


def build_dataset() -> list[Scenario]:
    """Materialize all 30 specs into reproducible scenarios."""
    return [spec.build() for spec in DATASET]


def specs_by_difficulty(difficulty: str) -> list[ScenarioSpec]:
    """Return the specs matching a difficulty level (case-insensitive)."""
    target = difficulty.lower()
    return [s for s in DATASET if s.difficulty.lower() == target]


def dataset_table() -> str:
    """Return an aligned text table describing the full dataset."""
    headers = ("Label", "Difficulty", "Floors", "Passengers", "Distribution", "Seed")
    rows: list[tuple[str, ...]] = [headers]
    for s in DATASET:
        rows.append(
            (s.label, s.difficulty, str(s.floors), str(s.passengers), s.distribution, str(s.seed))
        )
    widths = [max(len(r[i]) for r in rows) for i in range(len(headers))]
    sep = "-+-".join("-" * w for w in widths)

    def fmt(row: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    out = [fmt(rows[0]), sep]
    out.extend(fmt(r) for r in rows[1:])
    return "\n".join(out)
