from __future__ import annotations

import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TraceStats:
    minimum: float
    maximum: float
    average: float
    rms: float


@dataclass(frozen=True)
class QspiceCsvData:
    columns: list[str]
    rows: list[dict[str, float]]

    @property
    def sample_count(self) -> int:
        return len(self.rows)

    @property
    def time(self) -> list[float]:
        return self.trace("Time")

    def trace(self, name: str) -> list[float]:
        if name not in self.columns:
            raise KeyError(f"Trace not found: {name}")
        return [row[name] for row in self.rows]

    def stats(self, name: str) -> TraceStats:
        values = self.trace(name)
        if not values:
            raise ValueError(f"Trace has no samples: {name}")

        average = sum(values) / len(values)
        rms = math.sqrt(sum(value * value for value in values) / len(values))

        return TraceStats(
            minimum=min(values),
            maximum=max(values),
            average=average,
            rms=rms,
        )


def read_qspice_csv(path: Path) -> QspiceCsvData:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        columns = [column.strip() for column in reader.fieldnames]
        rows: list[dict[str, float]] = []

        for line_number, raw_row in enumerate(reader, start=2):
            row: dict[str, float] = {}
            for column in columns:
                raw_value = raw_row.get(column)
                if raw_value is None or raw_value == "":
                    raise ValueError(f"Missing value for {column} on line {line_number}")
                row[column] = float(raw_value)
            rows.append(row)

    return QspiceCsvData(columns=columns, rows=rows)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python -m src.qspice_tools.csv_reader <qspice-export.csv>")
        return 2

    data = read_qspice_csv(Path(argv[1]))
    print(f"samples: {data.sample_count}")
    print(f"columns: {', '.join(data.columns)}")

    for column in data.columns:
        if column == "Time":
            continue
        stats = data.stats(column)
        print(
            f"{column}: min={stats.minimum:.9g}, max={stats.maximum:.9g}, "
            f"avg={stats.average:.9g}, rms={stats.rms:.9g}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
