#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "runtime"))
import m110b_palette_runtime as m110b


def synthetic_state(cram_words: list[int]) -> bytes:
    payload = bytearray()
    payload += bytes([m110b.VDP_STATE_VERSION, m110b.VDP_VRAM_KB])
    payload += bytes(m110b.VRAM_BYTES)
    for value in cram_words:
        payload += int(value).to_bytes(2, "big")
    section = m110b.VDP_SECTION_ID.to_bytes(2, "big") + len(payload).to_bytes(4, "big") + payload
    return m110b.SAVE_HEADER + section


class M110BPaletteRuntimeStaticTests(unittest.TestCase):
    def test_parse_vdp_cram_exact(self) -> None:
        words = [0] * m110b.CRAM_WORDS
        words[8] = 0x0464
        state = synthetic_state(words)
        parsed = m110b.parse_vdp_cram(state)
        self.assertEqual(parsed["section_id"], m110b.VDP_SECTION_ID)
        self.assertEqual(parsed["vdp_state_version"], m110b.VDP_STATE_VERSION)
        self.assertEqual(parsed["vram_kb"], 64)
        self.assertEqual(parsed["cram_words"], words)

    def test_expected_single_cram_edit_passes(self) -> None:
        parent = [0] * m110b.CRAM_WORDS
        candidate = [0] * m110b.CRAM_WORDS
        parent[m110b.PALETTE_INDEX] = m110b.PARENT_COLOR
        candidate[m110b.PALETTE_INDEX] = m110b.CANDIDATE_COLOR
        result = m110b.evaluate_cram(parent, candidate)
        self.assertTrue(result["pass"])
        self.assertEqual(result["differences"], [{"index": 8, "parent": 0x0464, "candidate": 0x0648}])

    def test_extra_cram_change_fails(self) -> None:
        parent = [0] * m110b.CRAM_WORDS
        candidate = [0] * m110b.CRAM_WORDS
        parent[8] = 0x0464
        candidate[8] = 0x0648
        candidate[9] = 0x0002
        self.assertFalse(m110b.evaluate_cram(parent, candidate)["pass"])

    def test_player_line_change_fails(self) -> None:
        parent = [0] * m110b.CRAM_WORDS
        candidate = [0] * m110b.CRAM_WORDS
        parent[8] = 0x0464
        candidate[8] = 0x0648
        candidate[32] = 0x0002
        result = m110b.evaluate_cram(parent, candidate)
        self.assertFalse(result["assertions"]["player_palette_line_exact"])

    def test_bad_state_header_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            m110b.parse_vdp_cram(b"not-a-state")


if __name__ == "__main__":
    unittest.main()
