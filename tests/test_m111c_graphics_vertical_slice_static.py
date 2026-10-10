from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import m111c_graphics_vertical_slice as m


class M111CGraphicsVerticalSliceStaticTests(unittest.TestCase):
    def test_authored_tile_is_exact_8x8_x_pattern(self) -> None:
        self.assertEqual(len(m.AUTHORED_TILE_BYTES), 32)
        rows = [m.AUTHORED_TILE_BYTES[i:i + 4] for i in range(0, 32, 4)]
        expected_pixels = [
            [0xE, 0, 0, 0, 0, 0, 0, 0xE],
            [0, 0xE, 0, 0, 0, 0, 0xE, 0],
            [0, 0, 0xE, 0, 0, 0xE, 0, 0],
            [0, 0, 0, 0xE, 0xE, 0, 0, 0],
            [0, 0, 0, 0xE, 0xE, 0, 0, 0],
            [0, 0, 0xE, 0, 0, 0xE, 0, 0],
            [0, 0xE, 0, 0, 0, 0, 0xE, 0],
            [0xE, 0, 0, 0, 0, 0, 0, 0xE],
        ]
        decoded = []
        for row in rows:
            pixels = []
            for byte in row:
                pixels.extend([byte >> 4, byte & 0x0F])
            decoded.append(pixels)
        self.assertEqual(decoded, expected_pixels)

    def test_edit_changes_only_tile_two(self) -> None:
        tiles = bytearray(4 * 32)
        tiles[2 * 32:3 * 32] = b"\xAA" * 32
        source = {
            "schema": "truerecall.scene_primary_graphics.v1",
            "scene_index": 0,
            "tile_count": 4,
            "tile_bytes_hex": bytes(tiles).hex(),
        }
        edited = m.edit_primary_source(source)
        before = bytes.fromhex(source["tile_bytes_hex"])
        after = bytes.fromhex(edited["tile_bytes_hex"])
        self.assertEqual(before[:64], after[:64])
        self.assertEqual(after[64:96], m.AUTHORED_TILE_BYTES)
        self.assertEqual(before[96:], after[96:])
        self.assertEqual(source["tile_bytes_hex"], bytes(tiles).hex())

    def test_graphics_allocation_is_after_closed_m110a_scene_ledger(self) -> None:
        closed_m110a_end = 0x303100
        self.assertGreaterEqual(m.GFX_ALLOCATION_BASE, m.align(closed_m110a_end))
        self.assertEqual(m.GFX_ALLOCATION_BASE, 0x304000)

    def test_candidate_fingerprints_are_pinned(self) -> None:
        self.assertEqual(m.EXPECTED_M110A_SHA1, "270e1d633db7883c9170bb1e4eb367abdf97a2bd")
        self.assertEqual(m.EXPECTED_GRAPHICS_SCENE_SHA1, "a26f74937233e155e025bcd45a220660c75e110f")
        self.assertEqual(m.EXPECTED_OUTPUT_SHA1, "b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0")
        self.assertEqual(m.EXPECTED_OUTPUT_CHECKSUM, "0xFAD7")


if __name__ == "__main__":
    unittest.main()
