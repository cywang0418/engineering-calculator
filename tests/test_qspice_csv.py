import unittest
from pathlib import Path

from src.qspice_tools.csv_reader import read_qspice_csv


class QspiceCsvReaderTest(unittest.TestCase):
    def test_reads_qspice_csv_columns_and_samples(self):
        data = read_qspice_csv(Path("fixtures/qspice/rc_lowpass_small.csv"))

        self.assertEqual(data.columns, ["Time", "V(out)", "V(in)", "I(R1)"])
        self.assertEqual(data.sample_count, 5)
        self.assertEqual(data.time, [0.0, 1e-05, 0.001, 0.00101, 0.002])
        self.assertEqual(data.trace("V(out)"), [0.0, 0.0, 0.0, 0.049751, 3.160603])

    def test_calculates_basic_trace_statistics(self):
        data = read_qspice_csv(Path("fixtures/qspice/rc_lowpass_small.csv"))

        stats = data.stats("V(out)")

        self.assertEqual(stats.minimum, 0.0)
        self.assertEqual(stats.maximum, 3.160603)
        self.assertEqual(round(stats.average, 6), 0.642071)
        self.assertEqual(round(stats.rms, 6), 1.41364)


if __name__ == "__main__":
    unittest.main()
