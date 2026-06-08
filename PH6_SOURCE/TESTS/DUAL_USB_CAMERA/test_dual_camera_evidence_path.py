#!/usr/bin/env python3
"""
Regression guard: dual_camera_test.py must never hardcode a historical
evidence-run timestamp as its output directory (evidence overwrite defect).
PROPOSED artifact. Ratified_by: null.
"""

import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parent / "dual_camera_test.py"
FORBIDDEN_PATH_FRAGMENT = "20260603_055215"


class TestDualCameraEvidencePath(unittest.TestCase):

    def test_no_hardcoded_historical_run_directory(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            FORBIDDEN_PATH_FRAGMENT, text,
            "dual_camera_test.py must not hardcode a historical evidence-run "
            "timestamp; output directories must be generated fresh per run "
            "(evidence overwrite defect — see recovered_overwrite_*)."
        )

    def test_output_dir_derived_from_current_utc_time(self):
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("datetime.now(timezone.utc)", text)
        self.assertIn("EVIDENCE_DIRECTORY_ALREADY_EXISTS", text)


if __name__ == "__main__":
    unittest.main()
