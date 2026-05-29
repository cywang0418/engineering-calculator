from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_WAVEFORMS = ("Sinusoidal", "Square", "Triangle", "Arbitrary")
DEFAULT_ARBITRARY_POINTS = (0.0, 0.65, -0.35, 1.0, -0.9, 0.0)


@dataclass(frozen=True)
class PwgConfig:
    waveform: str
    amplitude_v: float
    bias_v: float
    frequency_hz: float
    cycles: int
    samples_per_cycle: int
    duty_percent: float = 50.0
    triangle_symmetry_percent: float = 50.0
    arbitrary_points: tuple[float, ...] = DEFAULT_ARBITRARY_POINTS
    phase_deg: float = 0.0
    output_load_ohms: float = 50.0

    @classmethod
    def default(cls) -> "PwgConfig":
        return cls(
            waveform="Sinusoidal",
            amplitude_v=12.0,
            bias_v=0.0,
            frequency_hz=10_000.0,
            cycles=5,
            samples_per_cycle=200,
            duty_percent=50.0,
            triangle_symmetry_percent=50.0,
            arbitrary_points=DEFAULT_ARBITRARY_POINTS,
            phase_deg=0.0,
            output_load_ohms=50.0,
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
    return generate_pwl(config)


def generate_pwl(config: PwgConfig) -> list[tuple[float, float]]:
    if config.waveform not in SUPPORTED_WAVEFORMS:
        raise ValueError(f"Unsupported waveform: {config.waveform}")
    if config.frequency_hz <= 0:
        raise ValueError("frequency_hz must be greater than zero")
    if config.cycles <= 0:
        raise ValueError("cycles must be greater than zero")
    if config.samples_per_cycle <= 0:
        raise ValueError("samples_per_cycle must be greater than zero")
    if not 0.0 < config.duty_percent < 100.0:
        raise ValueError("duty_percent must be greater than zero and less than 100")
    if not 0.0 < config.triangle_symmetry_percent < 100.0:
        raise ValueError("triangle_symmetry_percent must be greater than zero and less than 100")
    if config.output_load_ohms <= 0:
        raise ValueError("output_load_ohms must be greater than zero")
    arbitrary_points = parse_arbitrary_points(config.arbitrary_points)
    phase_offset = (config.phase_deg / 360.0) % 1.0

    step_s = config.period_s / config.samples_per_cycle
    samples: list[tuple[float, float]] = []

    for index in range(config.sample_count):
        time_s = index * step_s
        phase = (time_s * config.frequency_hz + phase_offset) % 1.0
        if config.waveform == "Sinusoidal":
            unit_value = math.sin(2.0 * math.pi * phase)
        else:
            unit_value = _unit_waveform_value(
                config.waveform,
                phase,
                config.duty_percent,
                config.triangle_symmetry_percent,
                arbitrary_points,
            )
        voltage_v = config.bias_v + config.amplitude_v * unit_value
        samples.append((_clean_number(time_s), _clean_number(voltage_v)))

    return samples


def _unit_waveform_value(
    waveform: str,
    phase: float,
    duty_percent: float = 50.0,
    triangle_symmetry_percent: float = 50.0,
    arbitrary_points: tuple[float, ...] = DEFAULT_ARBITRARY_POINTS,
) -> float:
    if waveform == "Sinusoidal":
        return math.sin(2.0 * math.pi * phase)
    if waveform == "Square":
        return 1.0 if phase < duty_percent / 100.0 else -1.0
    if waveform == "Triangle":
        return _triangle_wave_value(phase, triangle_symmetry_percent)
    if waveform == "Arbitrary":
        return _arbitrary_wave_value(phase, arbitrary_points)
    raise ValueError(f"Unsupported waveform: {waveform}")


def _triangle_wave_value(phase: float, symmetry_percent: float) -> float:
    peak_phase = symmetry_percent / 200.0
    negative_peak_phase = 0.5 + peak_phase
    if phase < peak_phase:
        return phase / peak_phase
    if phase < 0.5:
        return 1.0 - (phase - peak_phase) / (0.5 - peak_phase)
    if phase < negative_peak_phase:
        return -(phase - 0.5) / peak_phase
    return -1.0 + (phase - negative_peak_phase) / (0.5 - peak_phase)


def _arbitrary_wave_value(phase: float, points: tuple[float, ...]) -> float:
    if phase <= 0:
        return points[0]
    position = phase * (len(points) - 1)
    left_index = min(int(math.floor(position)), len(points) - 2)
    fraction = position - left_index
    left = points[left_index]
    right = points[left_index + 1]
    return left + (right - left) * fraction


def parse_arbitrary_points(value) -> tuple[float, ...]:
    if value in (None, ""):
        points = DEFAULT_ARBITRARY_POINTS
    elif isinstance(value, str):
        normalized = value.replace(",", " ").replace(";", " ")
        points = tuple(float(part) for part in normalized.split())
    else:
        points = tuple(float(point) for point in value)

    if len(points) < 2:
        raise ValueError("arbitrary_points must contain at least two values")
    for point in points:
        if not -1.0 <= point <= 1.0:
            raise ValueError("arbitrary_points values must be between -1 and 1")
    return points


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

    samples = generate_pwl(PwgConfig.default())
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
