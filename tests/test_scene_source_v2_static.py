#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
from scene_source_v2 import (
    downgrade_v2_source,
    palette_source_from_v2,
    patch_v2_is_noop,
    source_v2_to_patch,
    upgrade_v1_source,
    validate_v2_source,
)


def fixture_v1() -> dict:
    return {
        "schema": "truerecall.scene_source.v1",
        "scene_index": 3,
        "immutable": {
            "scene_flags": 3,
            "palette_0": 0x1234,
            "palette_1": 0x1234,
            "collision_resource_mode": 1,
            "primary_plane_state_ram": 0xFA62,
        },
        "planes": {
            "C000": {
                "graphics_descriptor": 0x1000,
                "width": 2,
                "height": 1,
                "tile_words": [1, 2],
            },
            "E000": {
                "graphics_descriptor": 0,
                "width": 1,
                "height": 2,
                "tile_words": [3, 4],
            },
        },
        "objects": {
            "prefix_hex": "abcd",
            "records": [
                {
                    "id": "retail_0000",
                    "type_id": 54,
                    "status_flags": 0x7800,
                    "stride": 6,
                    "x": 10,
                    "y": 20,
                    "param": None,
                },
                {
                    "id": "retail_0001",
                    "type_id": 12,
                    "status_flags": 0x7800,
                    "stride": 8,
                    "x": 30,
                    "y": 40,
                    "param": 7,
                },
            ],
        },
        "world": {
            "grid": [2, 2],
            "records": [
                {"id": "retail_000", "type": 9, "rect": [0, 0, 16, 16]},
            ],
        },
    }


def fixture_palette() -> dict:
    colors = [0x0000] * 64
    colors[1] = 0x0002
    colors[2] = 0x0020
    colors[3] = 0x0200
    colors[4] = 0x0EEE
    return {
        "schema": "truerecall.scene_palette.v1",
        "scene_index": 3,
        "retail_pointer": 0x1234,
        "colors": colors,
    }


class SceneSourceV2StaticTest(unittest.TestCase):
    def test_upgrade_downgrade_is_lossless(self) -> None:
        source_v1 = fixture_v1()
        palette = fixture_palette()
        source_v2 = upgrade_v1_source(source_v1, palette)
        self.assertEqual(source_v2["schema"], "truerecall.scene_source.v2")
        self.assertNotIn("palette_0", source_v2["immutable"])
        self.assertNotIn("palette_1", source_v2["immutable"])
        self.assertEqual(downgrade_v2_source(source_v2), source_v1)
        self.assertEqual(palette_source_from_v2(source_v2), palette)

    def test_unchanged_v2_is_noop(self) -> None:
        source_v2 = upgrade_v1_source(fixture_v1(), fixture_palette())
        patch = source_v2_to_patch(source_v2, copy.deepcopy(source_v2))
        self.assertTrue(patch_v2_is_noop(patch))
        self.assertIsNone(patch["palette_operation"])

    def test_palette_edit_is_isolated(self) -> None:
        base = upgrade_v1_source(fixture_v1(), fixture_palette())
        edited = copy.deepcopy(base)
        edited["palette"]["colors"][1] = 0x0222
        patch = source_v2_to_patch(base, edited)
        self.assertEqual(patch["scene_patch"]["map_operations"], [])
        self.assertEqual(patch["scene_patch"]["object_operations"], [])
        self.assertEqual(patch["scene_patch"]["world_operations"], [])
        self.assertEqual(patch["palette_operation"]["op"], "replace_palette")
        self.assertEqual(patch["palette_operation"]["changed_indices"], [1])
        self.assertEqual(patch["palette_operation"]["colors"][1], 0x0222)

    def test_existing_v1_semantics_pass_through(self) -> None:
        base = upgrade_v1_source(fixture_v1(), fixture_palette())
        edited = copy.deepcopy(base)
        edited["planes"]["C000"]["tile_words"][1] = 0x55
        edited["objects"]["records"][0]["x"] = 11
        edited["world"]["records"][0]["type"] = 11
        patch = source_v2_to_patch(base, edited)
        self.assertEqual(
            patch["scene_patch"]["map_operations"],
            [{"op": "set_tile", "plane": "C000", "x": 1, "y": 0, "value": 0x55}],
        )
        self.assertEqual(
            patch["scene_patch"]["object_operations"],
            [{"op": "replace", "base_index": 0, "x": 11}],
        )
        self.assertEqual(
            patch["scene_patch"]["world_operations"],
            [{"op": "replace", "id": "retail_000", "type": 11}],
        )
        self.assertIsNone(patch["palette_operation"])

    def test_retail_palette_identity_is_immutable(self) -> None:
        base = upgrade_v1_source(fixture_v1(), fixture_palette())
        edited = copy.deepcopy(base)
        edited["palette"]["retail_pointer"] += 2
        with self.assertRaises(ValueError):
            source_v2_to_patch(base, edited)

    def test_invalid_palette_word_is_rejected(self) -> None:
        source_v2 = upgrade_v1_source(fixture_v1(), fixture_palette())
        source_v2["palette"]["colors"][0] = 0x0001
        with self.assertRaises(ValueError):
            validate_v2_source(source_v2)

    def test_palette_pointer_not_duplicated_in_v2_immutable_metadata(self) -> None:
        source_v2 = upgrade_v1_source(fixture_v1(), fixture_palette())
        source_v2["immutable"]["palette_0"] = 0x1234
        with self.assertRaises(ValueError):
            validate_v2_source(source_v2)


if __name__ == "__main__":
    unittest.main()
