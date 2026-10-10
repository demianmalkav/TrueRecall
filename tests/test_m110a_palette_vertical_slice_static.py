#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import m110a_palette_vertical_slice as m110a


def fixture() -> dict:
    colors = [0] * 64
    colors[m110a.PALETTE_INDEX] = m110a.PALETTE_BEFORE
    return {
        "schema": "truerecall.scene_source.v2",
        "scene_index": 0,
        "immutable": {},
        "palette": {"retail_pointer": 0x1234, "colors": colors},
        "planes": {},
        "objects": {"prefix_hex": "", "records": []},
        "world": {"grid": [1, 1], "records": []},
    }


class M110APaletteVerticalSliceStaticTests(unittest.TestCase):
    def test_palette_edit_stays_outside_frozen_player_line(self) -> None:
        self.assertNotIn(m110a.PALETTE_INDEX, m110a.PLAYER_PALETTE_RANGE)
        self.assertEqual(m110a.PALETTE_INDEX, 8)
        self.assertEqual(m110a.PALETTE_BEFORE, 0x0464)
        self.assertEqual(m110a.PALETTE_AFTER, 0x0648)

    def test_scene_edit_is_minimal_and_semantically_pinned(self) -> None:
        base = fixture()
        edited = m110a.edit_scene_source(base)
        self.assertEqual(base["palette"]["colors"][8], 0x0464)
        self.assertEqual(edited["palette"]["colors"][8], 0x0648)
        self.assertEqual(len(edited["objects"]["records"]), 1)
        self.assertEqual(edited["objects"]["records"][0]["type_id"], 69)
        self.assertEqual((edited["objects"]["records"][0]["x"], edited["objects"]["records"][0]["y"]), (690, 558))
        self.assertEqual(len(edited["world"]["records"]), 1)
        self.assertEqual(edited["world"]["records"][0]["type"], 9)
        self.assertEqual(edited["world"]["records"][0]["rect"], [668, 540, 676, 580])

    def test_source_edit_does_not_mutate_input(self) -> None:
        base = fixture()
        snapshot = copy.deepcopy(base)
        m110a.edit_scene_source(base)
        self.assertEqual(base, snapshot)

    def test_wrong_palette_baseline_is_rejected(self) -> None:
        base = fixture()
        base["palette"]["colors"][m110a.PALETTE_INDEX] ^= 0x0002
        with self.assertRaises(ValueError):
            m110a.edit_scene_source(base)

    def test_wrong_scene_is_rejected(self) -> None:
        base = fixture()
        base["scene_index"] = 1
        with self.assertRaises(ValueError):
            m110a.edit_scene_source(base)


if __name__ == "__main__":
    unittest.main()
