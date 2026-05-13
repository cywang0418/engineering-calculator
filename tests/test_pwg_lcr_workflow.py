import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.pwg_lcr_workflow import run_pwg_lcr_workflow


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
            fake_qspice = workspace / "fake-qspice.sh"
            case_dir.mkdir()
            (case_dir / "pwg_lcr.cir").write_text("* test circuit\n.end\n", encoding="utf-8")
            fake_qspice.write_text("#!/bin/sh\ntouch pwg_lcr.qraw\nexit 0\n", encoding="utf-8")
            fake_qspice.chmod(0o755)

            result = run_pwg_lcr_workflow(
                case_dir=case_dir,
                reports_dir=reports_dir,
                qspice_exe=fake_qspice,
                run_qspice=True,
            )

            self.assertEqual(result.qspice_exit_code, 0)
            self.assertTrue(result.qraw_path.exists())
            self.assertIsNone(result.csv_path)


if __name__ == "__main__":
    unittest.main()
