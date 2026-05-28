from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.pwg_comparison_report import generate_pwg_comparison_report
from src.qspice_tools.pwg_generator import PwgConfig, SUPPORTED_WAVEFORMS, generate_pwl, write_pwl
from src.qspice_tools.waveform_report import generate_waveform_report


DEFAULT_CASE_DIR = Path("qspice-cli-validation/examples/pwg-lcr")
DEFAULT_REPORTS_DIR = Path("reports")
KNOWN_QSPICE_EXE_PATHS = (
    Path(r"C:\Program Files\QSPICE\QSPICE64.exe"),
    Path(r"C:\Program Files\QSPICE\QSPICE80.exe"),
)
KNOWN_QUX_EXE_PATHS = (Path(r"C:\Program Files\QSPICE\QUX.exe"),)
DEFAULT_EXPORT_TRACES = ("V(in)", "V(out)", "I(L1)", "I(Ro)")


@dataclass(frozen=True)
class PwgLcrWorkflowResult:
    case_dir: Path
    pwl_path: Path
    circuit_path: Path
    qraw_path: Path
    csv_path: Path | None
    waveform_report_path: Path
    comparison_report_path: Path
    qspice_exit_code: int | None
    csv_export_exit_code: int | None

    @property
    def reports_generated(self) -> bool:
        return self.waveform_report_path.exists() and self.comparison_report_path.exists()


def run_pwg_lcr_workflow(
    case_dir: Path,
    reports_dir: Path,
    csv_path: Path | None = None,
    qspice_exe: Path | None = None,
    qux_exe: Path | None = None,
    pwg_config: PwgConfig | None = None,
    run_qspice: bool = False,
    csv_export_command: list[str] | None = None,
) -> PwgLcrWorkflowResult:
    case_dir = Path(case_dir)
    reports_dir = Path(reports_dir)
    circuit_path = case_dir / "pwg_lcr.cir"
    pwl_path = case_dir / "pwg_input.pwl"
    qraw_path = case_dir / "pwg_lcr.qraw"
    waveform_report_path = reports_dir / "pwg_lcr_report.html"
    comparison_report_path = reports_dir / "pwg_lcr_comparison.html"

    if not circuit_path.exists():
        raise FileNotFoundError(f"Missing circuit file: {circuit_path}")

    config = pwg_config or PwgConfig.default()
    samples = generate_pwl(config)
    write_pwl(samples, pwl_path)

    qspice_exit_code: int | None = None
    if run_qspice:
        qspice_exe = qspice_exe or discover_qspice_exe()
        if qspice_exe is None:
            candidates = ", ".join(str(path) for path in KNOWN_QSPICE_EXE_PATHS)
            raise FileNotFoundError(
                "QSPICE executable was not found. Pass --qspice-exe or install QSPICE at "
                f"one of: {candidates}"
            )
        completed = subprocess.run(
            [str(qspice_exe), str(circuit_path.name)],
            cwd=case_dir,
            check=False,
        )
        qspice_exit_code = completed.returncode

    csv_export_exit_code: int | None = None
    if run_qspice and csv_path is None:
        if csv_export_command is not None:
            csv_export_exit_code = _run_csv_export_command(
                csv_export_command,
                case_dir=case_dir,
                qraw_path=qraw_path,
                csv_path=case_dir / "pwg_lcr.csv",
            )
        else:
            qux_exe = qux_exe or discover_qux_exe()
            if qux_exe is None:
                candidates = ", ".join(str(path) for path in KNOWN_QUX_EXE_PATHS)
                raise FileNotFoundError(
                    "QUX executable was not found. Pass --qux-exe or install QSPICE at "
                    f"one of: {candidates}"
                )
            csv_export_exit_code = export_qraw_to_csv(
                qux_exe=qux_exe,
                qraw_path=qraw_path,
                csv_path=case_dir / "pwg_lcr.csv",
                traces=DEFAULT_EXPORT_TRACES,
            )

    resolved_csv_path = _resolve_csv_path(case_dir, csv_path)
    if resolved_csv_path is None and csv_export_command is not None and not run_qspice:
        csv_export_exit_code = _run_csv_export_command(
            csv_export_command,
            case_dir=case_dir,
            qraw_path=qraw_path,
            csv_path=case_dir / "pwg_lcr.csv",
        )
        resolved_csv_path = _resolve_csv_path(case_dir, case_dir / "pwg_lcr.csv")

    if resolved_csv_path is not None:
        data = read_qspice_csv(resolved_csv_path)
        generate_waveform_report(
            data,
            waveform_report_path,
            title="PWG LCR QSPICE Result",
        )
        generate_pwg_comparison_report(
            data,
            comparison_report_path,
            frequency_hz=config.frequency_hz,
        )

    return PwgLcrWorkflowResult(
        case_dir=case_dir,
        pwl_path=pwl_path,
        circuit_path=circuit_path,
        qraw_path=qraw_path,
        csv_path=resolved_csv_path,
        waveform_report_path=waveform_report_path,
        comparison_report_path=comparison_report_path,
        qspice_exit_code=qspice_exit_code,
        csv_export_exit_code=csv_export_exit_code,
    )


def discover_qspice_exe(candidates: tuple[Path, ...] = KNOWN_QSPICE_EXE_PATHS) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def discover_qux_exe(candidates: tuple[Path, ...] = KNOWN_QUX_EXE_PATHS) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def export_qraw_to_csv(
    qux_exe: Path,
    qraw_path: Path,
    csv_path: Path,
    traces: tuple[str, ...] = DEFAULT_EXPORT_TRACES,
    npoints: str = "all",
) -> int:
    if not qraw_path.exists():
        raise FileNotFoundError(f"Missing qraw file before CSV export: {qraw_path}")

    completed = subprocess.run(
        [
            str(qux_exe),
            "-Export",
            str(qraw_path),
            ",".join(traces),
            npoints,
            "CSV",
            "-stdout",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0:
        csv_path.write_text(completed.stdout, encoding="utf-8")
    return completed.returncode


def _resolve_csv_path(case_dir: Path, csv_path: Path | None) -> Path | None:
    if csv_path is not None:
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing CSV file: {csv_path}")
        return csv_path

    candidate = case_dir / "pwg_lcr.csv"
    if candidate.exists():
        return candidate
    return None


def _run_csv_export_command(
    command: list[str],
    case_dir: Path,
    qraw_path: Path,
    csv_path: Path,
) -> int:
    if not qraw_path.exists():
        raise FileNotFoundError(f"Missing qraw file before CSV export: {qraw_path}")

    expanded_command = [
        part.format(
            case_dir=str(case_dir),
            qraw=str(qraw_path),
            csv=str(csv_path),
        )
        for part in command
    ]
    completed = subprocess.run(expanded_command, cwd=case_dir, check=False)
    return completed.returncode


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate PWG input, optionally run QSPICE, and build PWG LCR reports."
    )
    parser.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--csv", type=Path, default=None, help="QSPICE-exported CSV file")
    parser.add_argument("--qspice-exe", type=Path, default=None, help="Path to QSPICE64.exe")
    parser.add_argument("--qux-exe", type=Path, default=None, help="Path to QUX.exe")
    parser.add_argument("--waveform", choices=SUPPORTED_WAVEFORMS, default=PwgConfig.default().waveform)
    parser.add_argument("--amplitude-v", type=float, default=PwgConfig.default().amplitude_v)
    parser.add_argument("--bias-v", type=float, default=PwgConfig.default().bias_v)
    parser.add_argument("--frequency-hz", type=float, default=PwgConfig.default().frequency_hz)
    parser.add_argument(
        "--run-qspice",
        action="store_true",
        help="Run QSPICE and export fresh CSV results with QUX",
    )
    parser.add_argument(
        "--csv-export-command",
        nargs=argparse.REMAINDER,
        help="Command to export CSV after QSPICE. Supports {qraw}, {csv}, and {case_dir}.",
    )
    args = parser.parse_args(argv[1:])

    result = run_pwg_lcr_workflow(
        case_dir=args.case_dir,
        reports_dir=args.reports_dir,
        csv_path=args.csv,
        qspice_exe=args.qspice_exe,
        qux_exe=args.qux_exe,
        pwg_config=PwgConfig(
            waveform=args.waveform,
            amplitude_v=args.amplitude_v,
            bias_v=args.bias_v,
            frequency_hz=args.frequency_hz,
            cycles=PwgConfig.default().cycles,
            samples_per_cycle=PwgConfig.default().samples_per_cycle,
        ),
        run_qspice=args.run_qspice,
        csv_export_command=args.csv_export_command,
    )

    _print_result(result)
    if result.qspice_exit_code not in (None, 0):
        return result.qspice_exit_code
    return 0


def _print_result(result: PwgLcrWorkflowResult) -> None:
    print("PWG LCR workflow complete")
    print(f"Generated PWL: {result.pwl_path}")
    if result.qspice_exit_code is not None:
        print(f"QSPICE exit code: {result.qspice_exit_code}")
        print(f"Found qraw: {'yes' if result.qraw_path.exists() else 'no'}")
    if result.csv_export_exit_code is not None:
        print(f"CSV export exit code: {result.csv_export_exit_code}")
    print(f"Imported CSV: {result.csv_path if result.csv_path else 'no CSV available yet'}")
    print(f"Waveform report: {result.waveform_report_path}")
    print(f"Comparison report: {result.comparison_report_path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
