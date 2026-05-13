import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.csv_reader import read_qspice_csv
from src.qspice_tools.waveform_report import generate_waveform_report


class WaveformReportTest(unittest.TestCase):
    def test_generates_html_report_with_traces_and_stats(self):
        data = read_qspice_csv(Path("fixtures/qspice/rc_lowpass_small.csv"))

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.html"
            generate_waveform_report(data, output_path, title="RC Low-pass Validation")

            html = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>RC Low-pass Validation</title>", html)
        self.assertIn("QSPICE Waveform Report", html)
        self.assertIn("V(out)", html)
        self.assertIn("V(in)", html)
        self.assertIn("I(R1)", html)
        self.assertIn("RMS", html)
        self.assertIn("<svg", html)
        self.assertIn("polyline", html)


if __name__ == "__main__":
    unittest.main()
