import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from experiments import compare_tables


class ComparisonExperimentTests(unittest.TestCase):
    def test_main_writes_all_load_factors_and_two_page_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            with patch.object(compare_tables, "OUTPUT_DIR", output_dir):
                with contextlib.redirect_stdout(io.StringIO()):
                    compare_tables.main()

            with (output_dir / "comparison_results.csv").open(
                newline="", encoding="utf-8"
            ) as output:
                rows = list(csv.DictReader(output))

            expected_loads = [step / 10 for step in range(1, 10)]
            self.assertEqual(
                [float(row["load_factor"]) for row in rows], expected_loads
            )
            for row, load_factor in zip(rows, expected_loads):
                self.assertAlmostEqual(
                    float(row["chaining_success_theoretical"]),
                    1 + load_factor / 2,
                )
                self.assertAlmostEqual(
                    float(row["chaining_unsuccessful_theoretical"]),
                    load_factor,
                )
                self.assertAlmostEqual(
                    float(row["linear_success_theoretical"]),
                    0.5 * (1 + 1 / (1 - load_factor)),
                )
                self.assertAlmostEqual(
                    float(row["linear_unsuccessful_theoretical"]),
                    0.5 * (1 + 1 / (1 - load_factor) ** 2),
                )

            ElementTree.parse(output_dir / "comparison_results.svg")
            report = (output_dir / "comparison_report.pdf").read_bytes()
            self.assertEqual(report.count(b"/Type /Page "), 2)


if __name__ == "__main__":
    unittest.main()
