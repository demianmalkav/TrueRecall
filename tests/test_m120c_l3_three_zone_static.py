from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools.build import m120c_l3_three_zone_build as buildmod

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "tools/build/examples/m120c_l3_three_zone_overlay.json"


class M120CL3ThreeZoneStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
        self.mapop = self.overlay["maps"][0]
        self.words = [int(v) for v in self.mapop["tile_words"]]

    def test_overlay_identity_and_status(self) -> None:
        self.assertEqual(self.overlay["id"], "m120c_l3_three_zone_refinement")
        self.assertEqual(self.overlay["status"], "PROTOTYPE_VISUAL_PASS_NOT_ART_FREEZE")
        self.assertEqual(self.overlay["scene_index"], 0)

    def test_map_rect_is_exact_and_uses_only_runtime_verified_slots(self) -> None:
        self.assertEqual((self.mapop["plane"], self.mapop["x"], self.mapop["y"]), ("E000", 0, 12))
        self.assertEqual((self.mapop["width"], self.mapop["height"]), (27, 11))
        self.assertEqual(len(self.words), 27 * 11)
        self.assertTrue(set(self.words).issubset(set(range(2, 17))))

    def test_three_zone_separators_and_distinct_vocabularies(self) -> None:
        rows = [self.words[y * 27:(y + 1) * 27] for y in range(11)]
        for y in range(1, 11):
            self.assertEqual(rows[y][8], 7)
            self.assertEqual(rows[y][19], 7)
        left = {v for row in rows for v in row[0:8]}
        middle = {v for row in rows for v in row[9:19]}
        right = {v for row in rows for v in row[20:27]}
        self.assertNotEqual(left, middle)
        self.assertNotEqual(middle, right)
        self.assertIn(14, middle)
        self.assertIn(15, right)
        self.assertIn(16, left)

    def test_authored_graphics_contract_is_exact_15_slots(self) -> None:
        rows = self.overlay["primary_graphics"]
        self.assertEqual([int(row["tile_index"]) for row in rows], list(range(2, 17)))
        for row in rows:
            self.assertEqual(len(bytes.fromhex(row["tile_hex"])), 32)
            self.assertEqual(len(row["expect_sha256"]), 64)

    def test_pinned_candidate_fingerprints(self) -> None:
        self.assertEqual(buildmod.EXPECTED_SCENE_SHA1, "be091e8e76af5d685d1ba2760ad821149141fcff")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_SHA1, "7bd2144c22074bce5eebdf3e6e15f2f2c7db4ebe")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_CHECKSUM, "0x029E")
        self.assertEqual(buildmod.FROZEN_M09D_SHA1, "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021")


if __name__ == "__main__":
    unittest.main()
