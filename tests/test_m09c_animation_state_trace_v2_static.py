#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "runtime"))

from m09c_animation_state_trace_v2 import (
    EXPECTED_F9F8_DESCRIPTOR,
    sign_extend_pointer_word,
)


class M09CAnimationStateTraceV2StaticTest(unittest.TestCase):
    def test_signed_ram_pointer_word(self) -> None:
        self.assertEqual(sign_extend_pointer_word(0xC632), 0xFFFFC632)
        self.assertEqual(sign_extend_pointer_word(0xC7FA), 0xFFFFC7FA)

    def test_positive_pointer_word(self) -> None:
        self.assertEqual(sign_extend_pointer_word(0x1234), 0x00001234)

    def test_pointer_is_not_combined_with_adjacent_word(self) -> None:
        self.assertNotEqual(sign_extend_pointer_word(0xC632), 0xC6320000)
        self.assertNotEqual(sign_extend_pointer_word(0xC7FA), 0xC7FA000F)

    def test_canonical_f9f8_descriptor(self) -> None:
        self.assertEqual(EXPECTED_F9F8_DESCRIPTOR, 0x000A0000)


if __name__ == "__main__":
    unittest.main()
