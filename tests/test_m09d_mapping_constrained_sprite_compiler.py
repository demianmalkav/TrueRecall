from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

from m09d_mapping_constrained_sprite_compiler import (  # noqa: E402
    AUTHORED_DIRECTIONS,
    BANK_BYTES,
    CHUNK_BYTES,
    compile_banks,
)


CONTRACT_PATH = ROOT / "extracted_metadata" / "m09d_quaid_sprint_contract.json"


def indexed_frame(width: int, height: int, seed: int) -> Image.Image:
    img = Image.new("P", (width, height), 0)
    px = img.load()
    # Deterministic non-trivial original test pixels. Stay inside Genesis palette
    # indices 1..15 while leaving index 0 transparent.
    for y in range(height):
        for x in range(width):
            if ((x * 3 + y * 5 + seed) % 11) < 7:
                px[x, y] = 1 + ((x + y * 2 + seed) % 15)
    return img


def sources(contract: dict) -> dict[str, list[Image.Image]]:
    result: dict[str, list[Image.Image]] = {}
    for direction_index, direction in enumerate(AUTHORED_DIRECTIONS):
        family = contract["families"][direction]
        max_w = max(int(family["record_A"]["clip"][0]), int(family["record_B"]["clip"][0]))
        max_h = max(int(family["record_A"]["clip"][1]), int(family["record_B"]["clip"][1]))
        result[direction] = [
            indexed_frame(max_w, max_h, direction_index * 16 + phase_index)
            for phase_index in range(6)
        ]
    return result


class M09DMappingConstrainedSpriteCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_compiles_six_banks_with_production_budgets(self) -> None:
        banks, meta = compile_banks(self.contract, sources(self.contract))
        self.assertEqual(len(banks), 6)
        self.assertTrue(all(len(bank) == BANK_BYTES for bank in banks))
        self.assertEqual([p["used_chunk_slots"] for p in meta["phases"]], [17] * 6)
        self.assertEqual(max(p["max_frame_piece_count"] for p in meta["phases"]), 4)
        self.assertTrue(all(meta["assertions"].values()))

    def test_only_reserved_chunk_slot_range_receives_pixels(self) -> None:
        banks, _ = compile_banks(self.contract, sources(self.contract))
        lo = 0x68 * CHUNK_BYTES
        hi = 0x80 * CHUNK_BYTES
        for bank in banks:
            self.assertEqual(bank[:lo], b"\x00" * lo)
            self.assertEqual(bank[hi:], b"\x00" * (BANK_BYTES - hi))
            self.assertNotEqual(bank[lo:hi], b"\x00" * (hi - lo))

    def test_rejects_nonindexed_source(self) -> None:
        src = sources(self.contract)
        src["N"][0] = Image.new("RGB", src["N"][0].size, (1, 2, 3))
        with self.assertRaisesRegex(ValueError, "mode P"):
            compile_banks(self.contract, src)

    def test_rejects_palette_index_over_15(self) -> None:
        src = sources(self.contract)
        img = src["N"][0]
        img.putpixel((0, 0), 16)
        with self.assertRaisesRegex(ValueError, "palette index >15"):
            compile_banks(self.contract, src)

    def test_rejects_canvas_smaller_than_canonical_clip(self) -> None:
        src = sources(self.contract)
        src["N"][0] = indexed_frame(31, 63, 7)
        with self.assertRaisesRegex(ValueError, "smaller than clip"):
            compile_banks(self.contract, src)

    def test_native_mirror_policy_is_not_reauthored(self) -> None:
        _, meta = compile_banks(self.contract, sources(self.contract))
        self.assertEqual(meta["authored_direction_families"], ["N", "NE", "E", "SE", "S"])
        self.assertEqual(meta["mirrored_direction_families"], {"SW": "SE", "W": "E", "NW": "NE"})
        self.assertTrue(meta["assertions"]["eight_runtime_facings_via_native_mirroring"])


if __name__ == "__main__":
    unittest.main()
