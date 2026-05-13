import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.qspice_tools.pwg_generator import (
    PwgConfig,
    generate_sine_pwl,
    write_pwl,
)


class PwgGeneratorTest(unittest.TestCase):
    def test_default_config_matches_pwg_spec(self):
        config = PwgConfig.default()

        self.assertEqual(config.waveform, "Sinusoidal")
        self.assertEqual(config.amplitude_v, 12.0)
        self.assertEqual(config.bias_v, 0.0)
        self.assertEqual(config.frequency_hz, 10_000.0)
        self.assertEqual(config.cycles, 5)
        self.assertEqual(config.samples_per_cycle, 200)

    def test_generates_sine_pwl_samples_for_qspice(self):
        config = PwgConfig.default()
        samples = generate_sine_pwl(config)

        self.assertEqual(len(samples), 1001)
        self.assertEqual(samples[0], (0.0, 0.0))
        self.assertAlmostEqual(samples[-1][0], 0.0005)
        self.assertAlmostEqual(samples[-1][1], 0.0, places=9)

        quarter_cycle_index = 50
        self.assertAlmostEqual(samples[quarter_cycle_index][0], 0.000025)
        self.assertAlmostEqual(samples[quarter_cycle_index][1], 12.0, places=9)

    def test_writes_qspice_pwl_file(self):
        samples = generate_sine_pwl(PwgConfig.default())

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "pwg_input.pwl"
            write_pwl(samples, output_path)
            lines = output_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(lines[0], "0 0")
        self.assertEqual(lines[50], "2.5e-05 12")
        self.assertEqual(lines[-1], "0.0005 0")


if __name__ == "__main__":
    unittest.main()
