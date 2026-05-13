import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.pwg_spec_report import generate_pwg_spec_report


class PwgSpecReportTest(unittest.TestCase):
    def test_generates_pwg_spec_report_matching_reference_diagram_terms(self):
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "pwg.html"
            generate_pwg_spec_report(output_path)

            html = output_path.read_text(encoding="utf-8")

        self.assertIn("<title>PWG Display Panel Specification</title>", html)
        self.assertIn("Open-CtrLab V0.1", html)
        self.assertIn("Programmable Waveform Generator (PWG)", html)
        self.assertIn("Display Panel", html)
        self.assertIn("Man-Machine Interface and Optimization", html)
        self.assertIn("Digital Power Electronics Simulation", html)
        self.assertIn("Qspice", html)
        self.assertIn("CLI", html)
        self.assertIn("Waveform", html)
        self.assertIn("Sinusoidal", html)
        self.assertIn("Amplitude", html)
        self.assertIn("V<sub>p</sub> = 12 V", html)
        self.assertIn("V<sub>bias</sub> = 0 V", html)
        self.assertIn("Frequency", html)
        self.assertIn("10k Hz", html)
        self.assertIn("L = 100 uH", html)
        self.assertIn("C<sub>out</sub> = 2.4 uF", html)
        self.assertIn("R<sub>o</sub> = 1.25 Ω", html)
        self.assertIn("v<tspan baseline-shift=\"sub\">s</tspan>", html)
        self.assertIn("v<tspan baseline-shift=\"sub\">o</tspan>", html)


if __name__ == "__main__":
    unittest.main()
