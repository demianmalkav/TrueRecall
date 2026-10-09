#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "build"))

from m09c_native_phase_pixel_sequence import (
    Assembler,
    BANKS,
    CACHE_NAMESPACES,
    PLAYER_DESC,
    RAW_PHASE_DELTAS,
    key_trampoline,
    render_trampoline,
)


class M09CNativePhasePixelSequenceStaticTest(unittest.TestCase):
    def test_canonical_six_phase_contract(self) -> None:
        self.assertEqual(RAW_PHASE_DELTAS, [0, 2, 4, 6, 8, 10])
        self.assertEqual(BANKS, [0x210000, 0x218000, 0x220000, 0x228000, 0x230000, 0x238000])
        self.assertEqual(CACHE_NAMESPACES, [0x3A00, 0x3B00, 0x3C00, 0x3D00, 0x3E00, 0x3F00])
        self.assertEqual(PLAYER_DESC, 0x000A0000)

    def test_zero_short_branch_is_rejected(self) -> None:
        asm = Assembler()
        asm.branch_short(0x60, "next")
        asm.label("next")
        with self.assertRaises(ValueError):
            asm.finish()

    def test_phase_five_falls_directly_into_restore(self) -> None:
        render = render_trampoline()
        key = key_trampoline()
        self.assertIn(bytes.fromhex("223C00238000241F"), render)
        self.assertIn(bytes.fromhex("00403F00241F"), key)
        self.assertNotIn(bytes.fromhex("223C002380006000241F"), render)
        self.assertNotIn(bytes.fromhex("00403F006000241F"), key)

    def test_trampolines_fit_reserved_windows(self) -> None:
        self.assertLess(len(render_trampoline()), 0x100)
        self.assertLess(len(key_trampoline()), 0x100)


if __name__ == "__main__":
    unittest.main()
