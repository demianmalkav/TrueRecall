#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
from scene_palette import CRAM_MASK, PALETTE_WORDS, align, validate_colors


class ScenePaletteStaticTest(unittest.TestCase):
    def test_valid_cram_words_are_accepted(self) -> None:
        colors = [0x0000] * PALETTE_WORDS
        colors[1] = 0x0002
        colors[2] = 0x0020
        colors[3] = 0x0200
        colors[4] = 0x0EEE
        self.assertEqual(validate_colors(colors), colors)
        self.assertTrue(all((value & ~CRAM_MASK) == 0 for value in colors))

    def test_invalid_cram_low_bit_is_rejected(self) -> None:
        colors = [0x0000] * PALETTE_WORDS
        colors[7] = 0x0001
        with self.assertRaises(ValueError):
            validate_colors(colors)

    def test_invalid_cram_high_bit_is_rejected(self) -> None:
        colors = [0x0000] * PALETTE_WORDS
        colors[9] = 0x1000
        with self.assertRaises(ValueError):
            validate_colors(colors)

    def test_palette_length_is_exact(self) -> None:
        with self.assertRaises(ValueError):
            validate_colors([0x0000] * (PALETTE_WORDS - 1))
        with self.assertRaises(ValueError):
            validate_colors([0x0000] * (PALETTE_WORDS + 1))

    def test_non_integer_color_is_rejected(self) -> None:
        colors = [0x0000] * PALETTE_WORDS
        colors[0] = "0x0000"  # type: ignore[list-item]
        with self.assertRaises(TypeError):
            validate_colors(colors)  # type: ignore[arg-type]

    def test_alignment_contract(self) -> None:
        self.assertEqual(align(0x300000), 0x300000)
        self.assertEqual(align(0x300001), 0x300010)
        self.assertEqual(align(0x300010), 0x300010)


if __name__ == "__main__":
    unittest.main()
