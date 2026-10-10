from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

import m10a_vertical_slice_composer as mod  # noqa: E402


class M10AVerticalSliceComposerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = bytes([0x5A]) * mod.BASE_SIZE
        self.original_sha1 = mod.BASE_SHA1
        mod.BASE_SHA1 = hashlib.sha1(self.raw).hexdigest()

    def tearDown(self) -> None:
        mod.BASE_SHA1 = self.original_sha1

    def test_exact_scene_noop_preserves_player_transform(self) -> None:
        base = bytearray(mod.canonical_4m(self.raw))
        player = bytearray(base)
        player[0x210000:0x210004] = b"PLAY"
        player[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = b"\x00\x00"
        player[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = mod.p16(mod.genesis_checksum(player))

        merged, report = mod.compose_outputs(self.raw, bytes(player), self.raw)
        self.assertEqual(merged, bytes(player))
        self.assertTrue(report["scene_is_exact_noop"])
        self.assertEqual(report["conflict_bytes"], 0)
        self.assertEqual(report["scene_changed_bytes"], 0)

    def test_disjoint_player_and_scene_transforms_merge(self) -> None:
        base = bytearray(mod.canonical_4m(self.raw))
        player = bytearray(base)
        scene = bytearray(base)
        player[0x210100] = 0x11
        scene[0x300100] = 0x22
        for candidate in (player, scene):
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = b"\x00\x00"
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = mod.p16(mod.genesis_checksum(candidate))

        merged, report = mod.compose_outputs(self.raw, bytes(player), bytes(scene))
        self.assertEqual(merged[0x210100], 0x11)
        self.assertEqual(merged[0x300100], 0x22)
        self.assertEqual(report["conflict_bytes"], 0)
        self.assertEqual(report["overlap_changed_bytes"], 0)

    def test_equal_overlap_is_allowed(self) -> None:
        base = bytearray(mod.canonical_4m(self.raw))
        player = bytearray(base)
        scene = bytearray(base)
        player[0x1A4:0x1A8] = mod.p32(mod.ROM_SIZE - 1)
        scene[0x1A4:0x1A8] = mod.p32(mod.ROM_SIZE - 1)
        player[0x200100] = scene[0x200100] = 0x33
        for candidate in (player, scene):
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = b"\x00\x00"
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = mod.p16(mod.genesis_checksum(candidate))

        merged, report = mod.compose_outputs(self.raw, bytes(player), bytes(scene))
        self.assertEqual(merged[0x200100], 0x33)
        self.assertEqual(report["conflict_bytes"], 0)
        self.assertEqual(report["overlap_changed_bytes"], 1)

    def test_conflicting_overlap_is_rejected(self) -> None:
        base = bytearray(mod.canonical_4m(self.raw))
        player = bytearray(base)
        scene = bytearray(base)
        player[0x200200] = 0x44
        scene[0x200200] = 0x55
        for candidate in (player, scene):
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = b"\x00\x00"
            candidate[mod.CHECKSUM_OFFSET:mod.CHECKSUM_OFFSET + 2] = mod.p16(mod.genesis_checksum(candidate))

        with self.assertRaisesRegex(ValueError, "transformation conflict"):
            mod.compose_outputs(self.raw, bytes(player), bytes(scene))

    def test_range_coalescing(self) -> None:
        self.assertEqual(
            mod.coalesce_offsets([5, 6, 7, 10, 12, 13]),
            [
                {"start": 5, "end_exclusive": 8, "size": 3},
                {"start": 10, "end_exclusive": 11, "size": 1},
                {"start": 12, "end_exclusive": 14, "size": 2},
            ],
        )


if __name__ == "__main__":
    unittest.main()
