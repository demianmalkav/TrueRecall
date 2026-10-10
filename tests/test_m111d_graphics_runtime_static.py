from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "runtime"))
import m111d_graphics_runtime as m


def synthetic_state(vram: bytes, cram_words: list[int]) -> bytes:
    if len(vram) != m.VRAM_BYTES:
        raise ValueError("wrong VRAM size")
    if len(cram_words) != m.CRAM_WORDS:
        raise ValueError("wrong CRAM word count")
    payload = bytearray([m.VDP_STATE_VERSION, 64])
    payload += vram
    for word in cram_words:
        payload += int(word).to_bytes(2, "big")
    section = m.VDP_SECTION_ID.to_bytes(2, "big") + len(payload).to_bytes(4, "big") + payload
    return m.SAVE_HEADER + section


class M111DGraphicsRuntimeStaticTests(unittest.TestCase):
    def test_parse_vdp_state_extracts_vram_and_cram(self) -> None:
        vram = bytes((index * 7) & 0xFF for index in range(m.VRAM_BYTES))
        cram = [(index * 2) & 0x0EEE for index in range(m.CRAM_WORDS)]
        parsed = m.parse_vdp_state(synthetic_state(vram, cram))
        self.assertEqual(parsed["section_id"], m.VDP_SECTION_ID)
        self.assertEqual(parsed["vdp_state_version"], m.VDP_STATE_VERSION)
        self.assertEqual(parsed["vram"], vram)
        self.assertEqual(parsed["cram_words"], cram)

    def test_byte_diff_ranges_coalesces_adjacent_bytes(self) -> None:
        before = bytes(16)
        after = bytearray(before)
        for index in (2, 3, 4, 9, 11, 12):
            after[index] = 1
        self.assertEqual(m.byte_diff_ranges(before, bytes(after)), [[2, 5], [9, 10], [11, 13]])

    def test_screenshot_diff_reports_exact_bbox(self) -> None:
        parent = Image.new("RGB", (8, 6), (0, 0, 0))
        candidate = parent.copy()
        pixels = candidate.load()
        pixels[2, 1] = (255, 255, 255)
        pixels[5, 4] = (255, 255, 255)
        a = io.BytesIO()
        b = io.BytesIO()
        parent.save(a, format="PNG")
        candidate.save(b, format="PNG")
        report = m.screenshot_diff(a.getvalue(), b.getvalue())
        self.assertEqual(report["size"], [8, 6])
        self.assertEqual(report["changed_pixels"], 2)
        self.assertEqual(report["bbox"], [2, 1, 6, 5])

    def test_tile2_vram_slot_is_exactly_one_genesis_tile(self) -> None:
        self.assertEqual(m.TILE_INDEX, 2)
        self.assertEqual(m.TILE_VRAM_START, 0x40)
        self.assertEqual(m.TILE_VRAM_END, 0x60)
        self.assertEqual(m.TILE_VRAM_END - m.TILE_VRAM_START, m.TILE_BYTES)
        self.assertEqual(len(m.AUTHORED_TILE_BYTES), m.TILE_BYTES)


if __name__ == "__main__":
    unittest.main()
