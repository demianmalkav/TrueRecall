#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "rom_probe"))
from m09c_native_sequence_seam_probe import call_target, ff_runs, find_calls_to


class M09CNativeSequenceSeamStaticTest(unittest.TestCase):
    def test_jsr_absolute_long(self) -> None:
        buf = bytes.fromhex("4EB90000FDDC4E75")
        self.assertEqual(call_target(buf, 0), (6, 0x0000FDDC))
        self.assertEqual(find_calls_to(buf, 0x0000FDDC), [
            {
                "pc": 0,
                "size": 6,
                "context_sha1": __import__("hashlib").sha1(buf).hexdigest(),
                "context_start": 0,
                "context_end": len(buf),
            }
        ])

    def test_jsr_absolute_word_sign_extension(self) -> None:
        positive = bytes.fromhex("4EB81234")
        self.assertEqual(call_target(positive, 0), (4, 0x00001234))
        negative = bytes.fromhex("4EB8FF00")
        self.assertEqual(call_target(negative, 0), (4, 0xFFFFFF00))

    def test_bsr_short_uses_pc_plus_two(self) -> None:
        # pc=0, base PC=2, displacement +6 -> target 8.
        buf = bytes.fromhex("61064E714E714E714E75")
        self.assertEqual(call_target(buf, 0), (2, 8))

    def test_bsr_word_uses_pc_plus_two(self) -> None:
        # Motorola 68000 defines the displacement base PC as opcode address + 2.
        # pc=0, disp=+6 -> target 8 even though the instruction occupies 4 bytes.
        buf = bytes.fromhex("610000064E714E714E75")
        self.assertEqual(call_target(buf, 0), (4, 8))

    def test_bsr_word_negative(self) -> None:
        prefix = bytes.fromhex("4E714E714E71")
        call = bytes.fromhex("6100FFF8")  # pc=6, base=8, -8 -> target 0
        buf = prefix + call
        self.assertEqual(call_target(buf, 6), (4, 0))

    def test_ff_run_inventory(self) -> None:
        buf = b"\x00" + b"\xFF" * 0x20 + b"\x01" + b"\xFF" * 0x21 + b"\x02"
        self.assertEqual(
            ff_runs(buf, 0, len(buf), 0x20),
            [
                {"start": 1, "end": 0x21, "size": 0x20},
                {"start": 0x22, "end": 0x43, "size": 0x21},
            ],
        )

    def test_short_ff_run_is_not_candidate(self) -> None:
        buf = b"\xFF" * 0x1F
        self.assertEqual(ff_runs(buf, 0, len(buf), 0x20), [])


if __name__ == "__main__":
    unittest.main()
