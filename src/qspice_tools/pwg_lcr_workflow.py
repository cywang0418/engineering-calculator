from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.pwg_comparison_report import generate_pwg_comparison_report
from src.qspice_tools.pwg_generator import PwgConfig, generate_sine_pwl, write_pwl
from src.qspice_tools.waveform_report import generate_waveform_report


DEFAULT_CASE_DIR = Path("qspice-cli-validation/examples/pwg-lcr")
DEFAULT_REPORTS_DIR = Path("reports")


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

    @property
    def reports_generated(self) -> bool:
        return self.waveform_report_path.exists() and self.comparison_report_path.exists()


def run_pwg_lcr_workflow(
    case_dir: Path,
    reports_dir: Path,
    csv_path: Path | None = None,
    qspice_exe: Path | None = None,
    run_qspice: bool = False,
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

    samples = generate_sine_pwl(PwgConfig.default())
    write_pwl(samples, pwl_path)

    qspice_exit_code: int | None = None
    if run_qspice:
        if qspice_exe is None:
            raise ValueError("qspice_exe is required when run_qspice is enabled")
        completed = subprocess.run(
            [str(qspice_exe), str(circuit_path.name)],
            cwd=case_dir,
            check=False,
        )
        qspice_exit_code = completed.returncode

    resolved_csv_path = _resolve_csv_path(case_dir, csv_path)
    if resolved_csv_path is not None:
        data = read_qspice_csv(resolved_csv_path)
        generate_waveform_report(
            data,
            waveform_report_path,
            title="PWG LCR QSPICE Result",
        )
        generate_pwg_comparison_report(data, comparison_report_path)

    return PwgLcrWorkflowResult(
        case_dir=case_dir,
        pwl_path=pwl_path,
        circuit_path=circuit_path,
        qraw_path=qraw_path,
        csv_path=resolved_csv_path,
        waveform_report_path=waveform_report_path,
        comparison_report_path=comparison_report_path,
        qspice_exit_code=qspice_exit_code,
    )


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


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate PWG input, optionally run QSPICE, and build PWG LCR reports."
    )
    parser.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--csv", type=Path, default=None, help="QSPICE-exported CSV file")
    parser.add_argument("--qspice-exe", type=Path, default=None, help="Path to QSPICE64.exe")
    parser.add_argument(
        "--run-qspice",
        action="store_true",
        help="Run QSPICE before importing CSV results",
    )
    args = parser.parse_args(argv[1:])

    result = run_pwg_lcr_workflow(
        case_dir=args.case_dir,
        reports_dir=args.reports_dir,
        csv_path=args.csv,
        qspice_exe=args.qspice_exe,
        run_qspice=args.run_qspice,
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
    print(f"Imported CSV: {result.csv_path if result.csv_path else 'no CSV available yet'}")
    print(f"Waveform report: {result.waveform_report_path}")
    print(f"Comparison report: {result.comparison_report_path}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
