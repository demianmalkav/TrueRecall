from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

import m100a_vertical_slice_baseline as m100a  # noqa: E402


class M100AVerticalSliceBaselineStaticTests(unittest.TestCase):
    def make_buffers(self):
        canonical = bytes([0x55]) * m100a.BASE_SIZE
        base4 = canonical + bytes([0xFF]) * (m100a.OUTPUT_SIZE - m100a.BASE_SIZE)
        player = bytearray(base4)
        scene = bytearray(base4)
        return canonical, player, scene

    def compose_with_synthetic_base(self, canonical, player, scene):
        old = m100a.BASE_SHA1
        m100a.BASE_SHA1 = hashlib.sha1(canonical).hexdigest()
        try:
            return m100a.compose(canonical, bytes(player), bytes(scene))
        finally:
            m100a.BASE_SHA1 = old

    def test_disjoint_deltas_merge_and_preserve_each_parent(self) -> None:
        canonical, player, scene = self.make_buffers()
        player[0x1000] = 0x11
        scene[0x2000] = 0x22
        output, report = self.compose_with_synthetic_base(canonical, player, scene)
        self.assertEqual(output[0x1000], 0x11)
        self.assertEqual(output[0x2000], 0x22)
        self.assertTrue(all(report["assertions"].values()))

    def test_identical_shared_write_is_allowed(self) -> None:
        canonical, player, scene = self.make_buffers()
        player[0x1A4:0x1A8] = (m100a.OUTPUT_SIZE - 1).to_bytes(4, "big")
        scene[0x1A4:0x1A8] = (m100a.OUTPUT_SIZE - 1).to_bytes(4, "big")
        _output, report = self.compose_with_synthetic_base(canonical, player, scene)
        self.assertEqual(report["shared_nonchecksum_bytes"], 4)
        self.assertTrue(report["assertions"]["no_incompatible_overlap"])

    def test_conflicting_shared_write_is_rejected(self) -> None:
        canonical, player, scene = self.make_buffers()
        player[0x1234] = 0x11
        scene[0x1234] = 0x22
        with self.assertRaisesRegex(ValueError, "incompatible parent deltas"):
            self.compose_with_synthetic_base(canonical, player, scene)

    def test_scene0_manifest_is_minimal_and_semantically_pinned(self) -> None:
        manifest = json.loads(
            (BUILD / "examples" / "m100a_scene0_baseline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["schema"], "truerecall.scene_patch.v1")
        self.assertEqual(manifest["scene_index"], 0)
        self.assertEqual(manifest["map_operations"], [])
        self.assertEqual(len(manifest["object_operations"]), 1)
        pickup = manifest["object_operations"][0]
        self.assertEqual(pickup["type_id"], 69)
        self.assertEqual(pickup["stride"], 6)
        self.assertEqual((pickup["x"], pickup["y"]), (690, 558))
        self.assertEqual(len(manifest["world_operations"]), 1)
        wall = manifest["world_operations"][0]
        self.assertEqual(wall["type"], 9)
        self.assertEqual(wall["rect"], [668, 540, 676, 580])

    def test_runtime_baseline_fingerprints_are_pinned(self) -> None:
        self.assertEqual(m100a.SCENE_INDEX, 0)
        self.assertEqual(m100a.FROZEN_SCENE_PARENT_SHA1, "fe2d8f7bbffba42379aa72d697b91364f9734c96")
        self.assertEqual(m100a.EXPECTED_M100A_SHA1, "84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027")
        self.assertEqual(m100a.EXPECTED_M100A_CHECKSUM, "0x6E6A")


if __name__ == "__main__":
    unittest.main()
