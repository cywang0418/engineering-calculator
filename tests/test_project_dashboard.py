import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.project_dashboard import generate_project_dashboard


class ProjectDashboardTest(unittest.TestCase):
    def test_generates_project_dashboard_with_workflow_and_report_link(self):
        data = read_qspice_csv(Path("fixtures/qspice/rc_lowpass_small.csv"))

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "index.html"
            generate_project_dashboard(
                data=data,
                output_path=output_path,
                waveform_report_path=Path("rc_lowpass_report.html"),
                circuit_path=Path("qspice-cli-validation/examples/rc-lowpass/rc_lowpass.cir"),
                csv_path=Path("qspice-cli-validation/examples/rc-lowpass/rc_lowpass.csv"),
            )

            html = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>QSPICE Engineering Calculator</title>", html)
        self.assertIn("QSPICE Engineering Calculator", html)
        self.assertIn("QSPICE CLI", html)
        self.assertIn("CSV Import", html)
        self.assertIn("Waveform Report", html)
        self.assertIn("rc_lowpass_report.html", html)
        self.assertIn("scripts\\run-qspice-circuit.bat", html)
        self.assertIn("V(out)", html)
        self.assertIn("I(R1)", html)
        self.assertIn("MVP Status", html)
        self.assertIn("PWG Display Panel", html)
        self.assertIn("pwg_display_panel_spec.html", html)
        self.assertIn("examples\\pwg-lcr\\pwg_lcr.cir", html)


if __name__ == "__main__":
    unittest.main()
