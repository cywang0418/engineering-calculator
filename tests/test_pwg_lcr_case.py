import unittest
from pathlib import Path


class PwgLcrCaseTest(unittest.TestCase):
    def test_pwg_lcr_case_files_match_spec(self):
        case_dir = Path("qspice-cli-validation/examples/pwg-lcr")
        pwl_path = case_dir / "pwg_input.pwl"
        cir_path = case_dir / "pwg_lcr.cir"

        self.assertTrue(pwl_path.exists())
        self.assertTrue(cir_path.exists())

        pwl_lines = pwl_path.read_text(encoding="utf-8").splitlines()
        cir_text = cir_path.read_text(encoding="utf-8")

        self.assertEqual(len(pwl_lines), 1001)
        self.assertEqual(pwl_lines[0], "0 0")
        self.assertEqual(pwl_lines[50], "2.5e-05 12")
        self.assertEqual(pwl_lines[-1], "0.0005 0")
        self.assertIn('Vinput in 0 PWL FILE="pwg_input.pwl"', cir_text)
        self.assertIn("f=10k Hz", cir_text)
        self.assertIn("L1 in n_l 100u", cir_text)
        self.assertIn("Cout n_c 0 2.4u", cir_text)
        self.assertIn("Ro out 0 1.25", cir_text)
        self.assertIn(".save V(in) V(out) I(L1) I(Ro)", cir_text)


if __name__ == "__main__":
    unittest.main()
