import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.pwg_comparison_report import generate_pwg_comparison_report


class PwgComparisonReportTest(unittest.TestCase):
    def test_generates_input_output_comparison_report(self):
        data = read_qspice_csv(Path("qspice-cli-validation/examples/pwg-lcr/pwg_lcr.csv"))

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "comparison.html"
            generate_pwg_comparison_report(data, output_path)

            html = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>PWG Input Output Comparison</title>", html)
        self.assertIn("PWG Input Output Comparison", html)
        self.assertIn("V(in)", html)
        self.assertIn("V(out)", html)
        self.assertIn("Peak Gain", html)
        self.assertIn("RMS Gain", html)
        self.assertIn("10k Hz", html)
        self.assertIn("<svg", html)
        self.assertIn("polyline", html)


if __name__ == "__main__":
    unittest.main()
