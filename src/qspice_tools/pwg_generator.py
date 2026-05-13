from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PwgConfig:
    waveform: str
    amplitude_v: float
    bias_v: float
    frequency_hz: float
    cycles: int
    samples_per_cycle: int

    @classmethod
    def default(cls) -> "PwgConfig":
        return cls(
            waveform="Sinusoidal",
            amplitude_v=12.0,
            bias_v=0.0,
            frequency_hz=10_000.0,
            cycles=5,
            samples_per_cycle=200,
        )

    @property
    def period_s(self) -> float:
        return 1.0 / self.frequency_hz

    @property
    def duration_s(self) -> float:
        return self.cycles * self.period_s

    @property
    def sample_count(self) -> int:
        return self.cycles * self.samples_per_cycle + 1


def generate_sine_pwl(config: PwgConfig) -> list[tuple[float, float]]:
    if config.waveform != "Sinusoidal":
        raise ValueError(f"Unsupported waveform: {config.waveform}")
    if config.frequency_hz <= 0:
        raise ValueError("frequency_hz must be greater than zero")
    if config.cycles <= 0:
        raise ValueError("cycles must be greater than zero")
    if config.samples_per_cycle <= 0:
        raise ValueError("samples_per_cycle must be greater than zero")

    step_s = config.period_s / config.samples_per_cycle
    samples: list[tuple[float, float]] = []

    for index in range(config.sample_count):
        time_s = index * step_s
        voltage_v = config.bias_v + config.amplitude_v * math.sin(
            2.0 * math.pi * config.frequency_hz * time_s
        )
        samples.append((_clean_number(time_s), _clean_number(voltage_v)))

    return samples


def write_pwl(samples: list[tuple[float, float]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{_format_number(time_s)} {_format_number(value)}" for time_s, value in samples]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _clean_number(value: float) -> float:
    if abs(value) < 1e-12:
        return 0.0
    return value


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python -m src.qspice_tools.pwg_generator <output.pwl>")
        return 2

    samples = generate_sine_pwl(PwgConfig.default())
    write_pwl(samples, Path(argv[1]))
    print(f"wrote {argv[1]}")
    print("waveform: Sinusoidal")
    print("amplitude: Vp = 12 V")
    print("bias: Vbias = 0 V")
    print("frequency: 10k Hz")
    print(f"samples: {len(samples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
