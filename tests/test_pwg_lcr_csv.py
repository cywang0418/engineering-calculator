import unittest
from pathlib import Path

from src.qspice_tools.csv_reader import read_qspice_csv


class PwgLcrCsvTest(unittest.TestCase):
    def test_reads_exported_pwg_lcr_csv(self):
        data = read_qspice_csv(Path("qspice-cli-validation/examples/pwg-lcr/pwg_lcr.csv"))

        self.assertEqual(data.columns, ["Time", "I(RO)", "V(in)", "V(out)", "I(L1)"])
        self.assertEqual(data.sample_count, 1001)
        self.assertEqual(data.time[0], 0.0)
        self.assertAlmostEqual(data.time[-1], 0.0005)

        vin_stats = data.stats("V(in)")
        vout_stats = data.stats("V(out)")
        il1_stats = data.stats("I(L1)")
        iro_stats = data.stats("I(RO)")

        self.assertAlmostEqual(vin_stats.maximum, 12.0, places=2)
        self.assertAlmostEqual(vin_stats.minimum, -12.0, places=2)
        self.assertGreater(vout_stats.maximum, 3.0)
        self.assertLess(vout_stats.minimum, -2.0)
        self.assertGreater(il1_stats.rms, 1.0)
        self.assertGreater(iro_stats.rms, 1.0)


if __name__ == "__main__":
    unittest.main()
