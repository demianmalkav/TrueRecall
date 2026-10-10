from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

from m09d_mapping_constrained_sprite_compiler import compile_banks, load_sources  # noqa: E402
from m09d_quaid_sprint_source import (  # noqa: E402
    AUTHORED_DIRECTIONS,
    PHASE_DELTAS,
    generate,
)

CONTRACT_PATH = ROOT / "extracted_metadata" / "m09d_quaid_sprint_contract.json"


class M09DQuaidSprintSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_generates_thirty_original_indexed_frames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            report = generate(self.contract, out)
            self.assertEqual(report["assertions"]["frame_count"], 30)
            self.assertEqual(report["assertions"]["authored_direction_count"], 5)
            self.assertTrue(all(report["assertions"].values()))
            self.assertEqual(set(report["directions"]), set(AUTHORED_DIRECTIONS))
            for direction in AUTHORED_DIRECTIONS:
                rows = [f for f in report["frames"] if f["direction"] == direction]
                self.assertEqual(len(rows), 6)
                self.assertEqual([r["phase_delta"] for r in rows], list(PHASE_DELTAS))
                self.assertEqual(len({r["png_sha1"] for r in rows}), 6)
                self.assertTrue(all((out / r["image"]).exists() for r in rows))

    def test_generated_source_compiles_through_closed_mapping_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            report = generate(self.contract, out)
            manifest = out / "source_manifest.json"
            source_frames = load_sources(manifest, self.contract)
            banks, compiled = compile_banks(self.contract, source_frames)
            self.assertEqual(len(banks), 6)
            self.assertEqual([p["used_chunk_slots"] for p in compiled["phases"]], [17] * 6)
            self.assertTrue(all(compiled["assertions"].values()))
            self.assertEqual(compiled["authored_direction_families"], list(AUTHORED_DIRECTIONS))
            self.assertEqual(report["schema"], "truerecall.m09d.quaid_sprint_source.v1")

    def test_generated_pixels_stay_inside_genesis_palette_range(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            report = generate(self.contract, Path(td))
            for frame in report["frames"]:
                self.assertGreater(frame["nonzero_pixels"], 0)
                self.assertLessEqual(max(frame["palette_indices"]), 15)
                self.assertIn(0, frame["palette_indices"])


if __name__ == "__main__":
    unittest.main()
