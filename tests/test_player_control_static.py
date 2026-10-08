#!/usr/bin/env python3
"""Local regression checks for the M0.6 player-control reconstruction.

The copyrighted ROM is never stored in the repository. Set TRUERECALL_BASE_ROM to
the user's canonical True Lies (World) dump before running this test.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import unittest

EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
ROM_ENV = "TRUERECALL_BASE_ROM"


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


class PlayerControlStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = os.environ.get(ROM_ENV)
        if not path:
            raise unittest.SkipTest(f"set {ROM_ENV} to the canonical ROM path")
        cls.rom_path = Path(path)
        cls.data = cls.rom_path.read_bytes()
        cls.assert_sha1 = hashlib.sha1(cls.data).hexdigest()
        if cls.assert_sha1 != EXPECTED_SHA1:
            raise AssertionError(
                f"wrong base ROM SHA-1: {cls.assert_sha1}; expected {EXPECTED_SHA1}"
            )

    def test_normalized_input_edge_pipeline(self) -> None:
        self.assertEqual(
            self.data[0x12B62:0x12B68],
            bytes.fromhex("31 F8 F6 EC F6 EA"),
        )
        self.assertEqual(
            self.data[0x82DA:0x82E2],
            bytes.fromhex("30 38 F6 EE 02 40 50 30"),
        )

    def test_dpad_facing_table(self) -> None:
        got = [u16(self.data, 0x147C4 + i * 2) for i in range(16)]
        self.assertEqual(got, [0, 0, 4, 0, 6, 7, 5, 0, 2, 1, 3, 0, 0, 0, 0, 0])

    def test_idle_walk_animation_tables(self) -> None:
        walk = [u16(self.data, 0x147E4 + i * 2) for i in range(6)]
        idle = [u16(self.data, 0x147F0 + i * 2) for i in range(6)]
        self.assertEqual(walk, [0x02, 0x12, 0x22, 0x32, 0x32, 0x42])
        self.assertEqual(idle, [0x52, 0x62, 0x72, 0x82, 0x82, 0x92])

    def test_action_word_landmarks(self) -> None:
        self.assertEqual(self.data[0x832A:0x832E], bytes.fromhex("42 78 FB 7C"))
        self.assertEqual(self.data[0x83A0:0x83A6], bytes.fromhex("31 FC 00 02 FB 7C"))
        self.assertEqual(self.data[0x8720:0x8726], bytes.fromhex("31 FC 00 04 FB 7C"))

    def test_roll_and_roll_fire(self) -> None:
        self.assertEqual(
            self.data[0x8600:0x8608],
            bytes.fromhex("30 38 F6 EC 02 40 00 0F"),
        )
        self.assertEqual(
            self.data[0x8614:0x861A],
            bytes.fromhex("00 78 00 01 FB 7E"),
        )
        self.assertEqual(
            self.data[0x86B0:0x86B8],
            bytes.fromhex("30 38 F6 EC 08 00 00 04"),
        )
        self.assertEqual(self.data[0x84BA:0x84BE], bytes.fromhex("30 38 FB 8C"))

    def test_invulnerability_overlay(self) -> None:
        self.assertEqual(
            self.data[0x9714:0x9724],
            bytes.fromhex("08 2D 00 05 00 07 67 02 4E 75 31 FC 00 18 FB 90"),
        )
        self.assertEqual(
            self.data[0x9CA0:0x9CAA],
            bytes.fromhex("32 78 F9 F8 3A 78 FB 6E 53 78 FB 90"),
        )

    def test_terminal_event_dispatch_is_not_pure_death(self) -> None:
        # External FC47 bit 5 and D7 bit 1 route to 0x96B6.
        self.assertEqual(
            self.data[0x9250:0x925E],
            bytes.fromhex("08 38 00 05 FC 47 67 06 4E F9 00 00 96 B6"),
        )
        self.assertEqual(
            self.data[0x925E:0x926A],
            bytes.fromhex("08 07 00 01 67 06 4E F9 00 00 96 B6"),
        )
        # D7 bit 5 routes to the life-loss variant 0x944E.
        self.assertEqual(
            self.data[0x926A:0x9276],
            bytes.fromhex("08 07 00 05 67 06 4E F9 00 00 94 4E"),
        )
        # D7 bit 0 routes to another life-loss variant 0x960C.
        self.assertEqual(
            self.data[0x9276:0x9282],
            bytes.fromhex("08 07 00 00 67 06 4E F9 00 00 96 0C"),
        )


if __name__ == "__main__":
    unittest.main()
