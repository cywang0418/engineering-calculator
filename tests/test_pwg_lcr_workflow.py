import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.pwg_lcr_workflow import (
    discover_qspice_exe,
    discover_qux_exe,
    run_pwg_lcr_workflow,
)
from src.qspice_tools.pwg_generator import PwgConfig


class PwgLcrWorkflowTest(unittest.TestCase):
    def test_generates_pwg_input_and_reports_from_exported_csv(self):
        source_csv = Path("qspice-cli-validation/examples/pwg-lcr/pwg_lcr.csv")

        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            case_dir = workspace / "case"
            reports_dir = workspace / "reports"
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                csv_path=source_csv,
            )

            self.assertTrue(result.pwl_path.exists())
            self.assertEqual(result.pwl_path.name, "pwg_input.pwl")
            self.assertTrue(result.waveform_report_path.exists())
            self.assertTrue(result.comparison_report_path.exists())
            self.assertIsNone(result.qspice_exit_code)

            comparison_html = result.comparison_report_path.read_text(encoding="utf-8")
            waveform_html = result.waveform_report_path.read_text(encoding="utf-8")

        self.assertIn("PWG Input Output Comparison", comparison_html)
        self.assertIn("Peak Gain", comparison_html)
        self.assertIn("PWG LCR QSPICE Result", waveform_html)

    def test_can_launch_qspice_executable_and_detect_qraw(self):
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            case_dir = workspace / "case"
            reports_dir = workspace / "reports"
            fake_qspice = _write_fake_executable(workspace, "fake-qspice", "touch-qraw")
            fake_qux = _write_fake_executable(workspace, "fake-qux", "export-csv-stdout")
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                qspice_exe=fake_qspice,
                qux_exe=fake_qux,
                run_qspice=True,
            )

            self.assertEqual(result.qspice_exit_code, 0)
            self.assertTrue(result.qraw_path.exists())
            self.assertTrue(result.csv_path.exists())

    def test_detects_first_available_qspice_executable(self):
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            missing = workspace / "missing.exe"
            available = workspace / "QSPICE64.exe"
            available.write_text("", encoding="utf-8")

            self.assertEqual(discover_qspice_exe((missing, available)), available)

    def test_uses_custom_pwg_config_for_generated_input(self):
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            case_dir = workspace / "case"
            reports_dir = workspace / "reports"
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                pwg_config=PwgConfig(
                    waveform="Triangle",
                    amplitude_v=6.0,
                    bias_v=1.0,
                    frequency_hz=5_000.0,
                    cycles=1,
                    samples_per_cycle=4,
                ),
            )

            lines = result.pwl_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(lines[0], "0 1")
        self.assertEqual(lines[1], "5e-05 7")
        self.assertEqual(lines[-1], "0.0002 1")

    def test_detects_first_available_qux_executable(self):
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            missing = workspace / "missing.exe"
            available = workspace / "QUX.exe"
            available.write_text("", encoding="utf-8")

            self.assertEqual(discover_qux_exe((missing, available)), available)

    def test_run_qspice_exports_fresh_csv_with_qux(self):
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            case_dir = workspace / "case"
            reports_dir = workspace / "reports"
            fake_qspice = _write_fake_executable(workspace, "fake-qspice", "touch-qraw")
            fake_qux = _write_fake_executable(workspace, "fake-qux", "export-csv-stdout")
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                qspice_exe=fake_qspice,
                qux_exe=fake_qux,
                run_qspice=True,
            )

            self.assertEqual(result.qspice_exit_code, 0)
            self.assertEqual(result.csv_export_exit_code, 0)
            self.assertTrue(result.csv_path.exists())
            self.assertTrue(result.reports_generated)

    def test_can_run_external_csv_export_command_after_qspice(self):
        source_csv = Path("qspice-cli-validation/examples/pwg-lcr/pwg_lcr.csv").resolve()

        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            case_dir = workspace / "case"
            reports_dir = workspace / "reports"
            fake_qspice = _write_fake_executable(workspace, "fake-qspice", "touch-qraw")
            fake_exporter = _write_fake_executable(workspace, "fake-exporter", "copy-first-to-third")
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                qspice_exe=fake_qspice,
                run_qspice=True,
                csv_export_command=[
                    str(fake_exporter),
                    str(source_csv),
                    "{qraw}",
                    "{csv}",
                ],
            )

            self.assertEqual(result.qspice_exit_code, 0)
            self.assertEqual(result.csv_export_exit_code, 0)
            self.assertTrue(result.csv_path.exists())
            self.assertTrue(result.reports_generated)


def _write_fake_executable(workspace: Path, name: str, action: str) -> Path:
    path = workspace / f"{name}.bat"
    if action == "touch-qraw":
        path.write_text("@echo off\ntype nul > pwg_lcr.qraw\nexit /b 0\n", encoding="utf-8")
    elif action == "copy-first-to-third":
        path.write_text("@echo off\ncopy /Y \"%~1\" \"%~3\" > nul\nexit /b 0\n", encoding="utf-8")
    elif action == "export-csv-stdout":
        path.write_text(
            "@echo off\n"
            "echo \"Time\",\"V(in)\",\"V(out)\",\"I(L1)\",\"I(Ro)\"\n"
            "echo 0,0,0,0,0\n"
            "echo 1e-6,1,0.5,0.1,0.4\n"
            "exit /b 0\n",
            encoding="utf-8",
        )
    else:
        raise ValueError(action)
    return path


if __name__ == "__main__":
    unittest.main()
