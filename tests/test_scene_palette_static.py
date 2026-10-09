#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import scene_palette as sp


def synthetic_rom() -> bytes:
    raw = bytearray(sp.BASE_SIZE)
    scene = 0x001000
    palette = 0x002000
    raw[sp.SCENE_TABLE:sp.SCENE_TABLE + 4] = sp.p32(scene)
    raw[scene + 0x02:scene + 0x06] = sp.p32(palette)
    raw[scene + 0x06:scene + 0x0A] = sp.p32(palette)
    colors = [0x0000] * sp.PALETTE_WORDS
    colors[1] = 0x0002
    colors[2] = 0x0020
    colors[3] = 0x0200
    colors[4] = 0x0EEE
    for index, value in enumerate(colors):
        raw[palette + index * 2:palette + index * 2 + 2] = sp.p16(value)
    return bytes(raw)


class ScenePaletteStaticTest(unittest.TestCase):
    def test_valid_cram_words_are_accepted(self) -> None:
        colors = [0x0000] * sp.PALETTE_WORDS
        colors[1] = 0x0002
        colors[2] = 0x0020
        colors[3] = 0x0200
        colors[4] = 0x0EEE
        self.assertEqual(sp.validate_colors(colors), colors)
        self.assertTrue(all((value & ~sp.CRAM_MASK) == 0 for value in colors))

    def test_invalid_cram_low_bit_is_rejected(self) -> None:
        colors = [0x0000] * sp.PALETTE_WORDS
        colors[7] = 0x0001
        with self.assertRaises(ValueError):
            sp.validate_colors(colors)

    def test_invalid_cram_high_bit_is_rejected(self) -> None:
        colors = [0x0000] * sp.PALETTE_WORDS
        colors[9] = 0x1000
        with self.assertRaises(ValueError):
            sp.validate_colors(colors)

    def test_palette_length_is_exact(self) -> None:
        with self.assertRaises(ValueError):
            sp.validate_colors([0x0000] * (sp.PALETTE_WORDS - 1))
        with self.assertRaises(ValueError):
            sp.validate_colors([0x0000] * (sp.PALETTE_WORDS + 1))

    def test_non_integer_color_is_rejected(self) -> None:
        colors = [0x0000] * sp.PALETTE_WORDS
        colors[0] = "0x0000"  # type: ignore[list-item]
        with self.assertRaises(TypeError):
            sp.validate_colors(colors)  # type: ignore[arg-type]

    def test_alignment_contract(self) -> None:
        self.assertEqual(sp.align(0x300000), 0x300000)
        self.assertEqual(sp.align(0x300001), 0x300010)
        self.assertEqual(sp.align(0x300010), 0x300010)

    def test_synthetic_noop_and_authored_relocation(self) -> None:
        raw = synthetic_rom()
        old_sha1 = sp.BASE_SHA1
        sp.BASE_SHA1 = hashlib.sha1(raw).hexdigest()
        try:
            source = sp.export_scene_palette(raw, 0)
            self.assertEqual(source["retail_pointer"], 0x002000)
            self.assertEqual(len(source["colors"]), sp.PALETTE_WORDS)

            no_op, no_op_report = sp.compile_palette(raw, dict(source))
            self.assertEqual(no_op, raw)
            self.assertTrue(no_op_report["noop"])

            edited = dict(source)
            edited["colors"] = list(source["colors"])
            edited["colors"][5] = 0x0222
            out, report = sp.compile_palette(raw, edited)

            self.assertFalse(report["noop"])
            self.assertEqual(len(out), sp.DEFAULT_ROM_SIZE)
            self.assertEqual(report["changed_color_indices"], [5])
            self.assertEqual(report["new_pointer"], sp.DEFAULT_ALLOCATION_BASE)
            scene = sp.scene_address(out, 0)
            self.assertEqual(sp.u32(out, scene + 0x02), sp.DEFAULT_ALLOCATION_BASE)
            self.assertEqual(sp.u32(out, scene + 0x06), sp.DEFAULT_ALLOCATION_BASE)
            self.assertEqual(sp.u16(out, sp.DEFAULT_ALLOCATION_BASE + 5 * 2), 0x0222)
            self.assertEqual(
                sp.u16(out, sp.CHECKSUM_OFFSET),
                sp.genesis_checksum(out),
            )
        finally:
            sp.BASE_SHA1 = old_sha1


if __name__ == "__main__":
    unittest.main()
