from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import scene_source_v3 as s3


def fixture_v2() -> dict:
    return {
        "schema": "truerecall.scene_source.v2",
        "scene_index": 3,
        "immutable": {"scene_flags": 3, "collision_resource_mode": 1, "primary_plane_state_ram": 0xFA62},
        "planes": {
            "C000": {"graphics_descriptor": 0x1000, "width": 2, "height": 1, "tile_words": [1, 2]},
            "E000": {"graphics_descriptor": 0, "width": 1, "height": 2, "tile_words": [3, 4]},
        },
        "objects": {"prefix_hex": "abcd", "records": []},
        "world": {"grid": [2, 2], "records": []},
        "palette": {"retail_pointer": 0x1234, "colors": [0] * 64},
    }


def fixture_graphics() -> dict:
    payload = bytes(range(32)) + bytes([0xAA]) * 32 + bytes([0x55]) * 32 + bytes([0x11]) * 32 + bytes([0x22]) * 32
    return {
        "schema": "truerecall.scene_primary_graphics.v1",
        "scene_index": 3,
        "retail_descriptor": 0x2200,
        "retail_primary_lz": 0x2300,
        "secondary_pointer": 0x80001234,
        "aux_pointer": 0x4567,
        "secondary_plane_descriptor": 0,
        "tile_count": len(payload) // 32,
        "tile_bytes_hex": payload.hex(),
        "decoded_sha256": hashlib.sha256(payload).hexdigest(),
    }


class SceneSourceV3StaticTests(unittest.TestCase):
    def test_upgrade_downgrade_is_lossless_and_v2_untouched(self) -> None:
        v2 = fixture_v2()
        original = copy.deepcopy(v2)
        v3 = s3.upgrade_v2_source(v2, fixture_graphics())
        self.assertEqual(v2, original)
        self.assertEqual(v3["schema"], s3.SCHEMA_V3)
        self.assertEqual(s3.downgrade_v3_source(v3), v2)
        rebuilt = s3.graphics_source_from_v3(v3)
        for key, value in fixture_graphics().items():
            self.assertEqual(rebuilt[key], value)

    def test_unchanged_v3_is_noop(self) -> None:
        v3 = s3.upgrade_v2_source(fixture_v2(), fixture_graphics())
        patch = s3.source_v3_to_patch(v3, copy.deepcopy(v3))
        self.assertTrue(s3.patch_v3_is_noop(patch))
        self.assertIsNone(patch["graphics_operation"])

    def test_graphics_edit_is_isolated_and_reports_tile(self) -> None:
        base = s3.upgrade_v2_source(fixture_v2(), fixture_graphics())
        edited = copy.deepcopy(base)
        payload = bytearray.fromhex(edited["primary_graphics"]["tile_bytes_hex"])
        payload[64:96] = bytes([0xE0]) * 32
        edited["primary_graphics"]["tile_bytes_hex"] = bytes(payload).hex()
        patch = s3.source_v3_to_patch(base, edited)
        self.assertEqual(patch["scene_patch_v2"]["scene_patch"]["map_operations"], [])
        self.assertIsNone(patch["scene_patch_v2"]["palette_operation"])
        self.assertEqual(patch["graphics_operation"]["changed_tile_indices"], [2])

    def test_graphics_identity_is_immutable(self) -> None:
        base = s3.upgrade_v2_source(fixture_v2(), fixture_graphics())
        for field in s3.IDENTITY_FIELDS:
            edited = copy.deepcopy(base)
            edited["primary_graphics"][field] = "0" * 64 if field == "retail_decoded_sha256" else edited["primary_graphics"][field] + 2
            with self.assertRaises(ValueError):
                s3.source_v3_to_patch(base, edited)

    def test_invalid_payload_alignment_rejected(self) -> None:
        v3 = s3.upgrade_v2_source(fixture_v2(), fixture_graphics())
        v3["primary_graphics"]["tile_bytes_hex"] = "00"
        with self.assertRaises(ValueError):
            s3.validate_v3_source(v3)


if __name__ == "__main__":
    unittest.main()
