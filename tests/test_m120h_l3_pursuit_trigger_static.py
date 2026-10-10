from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "build"))

import m120h_l3_pursuit_trigger as buildmod


class M120HL3PursuitTriggerStaticTests(unittest.TestCase):
    def test_pinned_candidate_contract(self) -> None:
        self.assertEqual(buildmod.EXPECTED_M120G_SHA1, "150373a312283f5c89e5fa00e99f19d7a83bff44")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_SHA1, "acfecb2fdb5cc6c55a5c89ae172dd58d8444e1e3")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_CHECKSUM, "0xD0C0")
        self.assertEqual(buildmod.SIGNAL_TYPE, 87)
        self.assertEqual(buildmod.CHASE_TYPE, 24)
        self.assertEqual(buildmod.SCRIPT_ADDRESS, 0x308000)

    def test_source_insertion_is_immediately_after_private_latch_clear(self) -> None:
        source = (
            "L_A:\n"
            "  LOAD_ABS_W_D2 0xFFFFFC56\n"
            "  STORE_ABS_W_D2 0xFFFFFC56\n"
            "  MOVI_W_D2 0x0036\n"
            "  NATIVE ShowMessage\n"
        )
        authored = buildmod.author_type87_source(source)
        expected = buildmod.FC56_STORE + buildmod.SPAWN_SOURCE
        self.assertIn(expected, authored)
        self.assertEqual(authored.count("NATIVE SpawnLinkedObject"), 1)
        self.assertIn("MOVI_W_D2 0x0018", authored)

    def test_non_unique_fc56_store_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            buildmod.author_type87_source("no latch here\n")
        with self.assertRaises(ValueError):
            buildmod.author_type87_source(buildmod.FC56_STORE * 2)


if __name__ == "__main__":
    unittest.main()
