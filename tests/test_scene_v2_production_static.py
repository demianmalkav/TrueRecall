from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

from scene_compiler_v2 import _next_allocation_address  # noqa: E402
from scene_palette import CRAM_MASK, PALETTE_WORDS, validate_colors  # noqa: E402
from scene_source_v2 import (  # noqa: E402
    SCHEMA_V1,
    SCHEMA_V2,
    downgrade_v2_source,
    patch_v2_is_noop,
    source_v2_to_patch,
    upgrade_v1_source,
)


class SceneV2ProductionStaticTests(unittest.TestCase):
    def synthetic_v1(self):
        return {
            "schema": SCHEMA_V1,
            "scene_index": 18,
            "immutable": {
                "scene_flags": 3,
                "palette_0": 0x09B420,
                "palette_1": 0x09B420,
                "collision_resource_mode": 1,
                "primary_plane_state_ram": 0xFA62,
            },
            "planes": {
                "C000": {"graphics_descriptor": 0, "width": 2, "height": 1, "tile_words": [0, 0]},
                "E000": {"graphics_descriptor": 0, "width": 2, "height": 1, "tile_words": [0, 0]},
            },
            "objects": {"prefix_hex": "", "records": []},
            "world": {"grid": [1, 1], "records": []},
        }

    def palette(self):
        return {
            "schema": "truerecall.scene_palette.v1",
            "scene_index": 18,
            "retail_pointer": 0x09B420,
            "colors": [0] * PALETTE_WORDS,
        }

    def test_valid_palette_contract(self):
        colors = [0, 0x0222, 0x0EEE] + [0] * (PALETTE_WORDS - 3)
        self.assertEqual(validate_colors(colors), colors)
        self.assertTrue(all((value & ~CRAM_MASK) == 0 for value in colors))
        bad = colors[:]
        bad[1] = 0x0001
        with self.assertRaises(ValueError):
            validate_colors(bad)

    def test_v1_v2_upgrade_downgrade_is_lossless_for_scene_semantics(self):
        v1 = self.synthetic_v1()
        v2 = upgrade_v1_source(v1, self.palette())
        self.assertEqual(v2["schema"], SCHEMA_V2)
        self.assertNotIn("palette_0", v2["immutable"])
        self.assertEqual(downgrade_v2_source(v2), v1)

    def test_v2_noop_and_palette_operation_are_distinct(self):
        base = upgrade_v1_source(self.synthetic_v1(), self.palette())
        noop = source_v2_to_patch(base, copy.deepcopy(base))
        self.assertTrue(patch_v2_is_noop(noop))
        edited = copy.deepcopy(base)
        edited["palette"]["colors"][1] = 0x0EEE
        patch = source_v2_to_patch(base, edited)
        self.assertFalse(patch_v2_is_noop(patch))
        self.assertEqual(patch["palette_operation"]["changed_indices"], [1])
        self.assertEqual(patch["scene_patch"]["map_operations"], [])

    def test_palette_allocates_after_highest_scene_resource(self):
        scene_patch = {"allocation_base": 0x300000}
        report = {
            "allocations": [
                {"name": "map", "address": 0x300000, "size": 0x11A},
                {"name": "world", "address": 0x300300, "size": 0x1A0},
            ]
        }
        self.assertEqual(_next_allocation_address(scene_patch, report), 0x3004A0)


if __name__ == "__main__":
    unittest.main()
