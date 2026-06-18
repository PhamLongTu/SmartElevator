"""Dataset benchmark gồm 30 scenario chia theo ba mức độ khó."""

from __future__ import annotations

from dataclasses import dataclass

from simulation.scenario import DistributionScenarioGenerator, Scenario


@dataclass(frozen=True)
class ScenarioSpec:
    """Đặc tả khai báo của một scenario benchmark."""

    label: str
    difficulty: str
    floors: int
    passengers: int
    distribution: str
    seed: int

    def build(self) -> Scenario:
        """Dựng đặc tả này thành một :class:`Scenario` có thể tái lập."""
        return DistributionScenarioGenerator(
            num_passengers=self.passengers,
            num_floors=self.floors,
            seed=self.seed,
            distribution=self.distribution,
            label=self.label,
            difficulty=self.difficulty,
        ).generate()


DATASET: tuple[ScenarioSpec, ...] = (
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
    """Dựng toàn bộ 30 đặc tả thành các scenario có thể tái lập."""
    return [spec.build() for spec in DATASET]


def specs_by_difficulty(difficulty: str) -> list[ScenarioSpec]:
    """Trả về các đặc tả khớp mức độ khó, không phân biệt hoa thường."""
    target = difficulty.lower()
    return [s for s in DATASET if s.difficulty.lower() == target]


def dataset_table() -> str:
    """Trả về bảng text mô tả toàn bộ dataset."""
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
