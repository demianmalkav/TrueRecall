from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "build"))

import scene_compiler as sc
import scene_overlay as so


def synthetic_source() -> dict:
    graphics = bytes([0]) * 32 + bytes([0x11]) * 32 + bytes([0x22]) * 32 + bytes([0x33]) * 32
    return {
        "schema": "truerecall.scene_source.v3", "scene_index": 0, "immutable": {},
        "palette": {"retail_pointer": 0x2000, "colors": [0] * 64},
        "planes": {
            "C000": {"graphics_descriptor": 0x2200, "width": 4, "height": 3, "tile_words": list(range(12))},
            "E000": {"graphics_descriptor": 0, "width": 4, "height": 3, "tile_words": list(range(12, 24))},
        },
        "objects": {"prefix_hex": "", "records": [{"id": "retail_0000", "type_id": 1, "status_flags": 0, "stride": 6, "x": 10, "y": 20, "param": None}]},
        "world": {"grid": [4, 4], "records": [{"id": "retail_0000", "type": 9, "rect": [0, 0, 8, 8]}]},
        "primary_graphics": {
            "retail_descriptor": 0x2200, "retail_primary_lz": 0x2300,
            "secondary_pointer": 0x80001234, "aux_pointer": 0x4567,
            "secondary_plane_descriptor": 0,
            "retail_decoded_sha256": hashlib.sha256(graphics).hexdigest(),
            "tile_count": 4, "tile_bytes_hex": graphics.hex(),
        },
    }


def synthetic_overlay(source: dict) -> dict:
    tile1 = bytes.fromhex(source["primary_graphics"]["tile_bytes_hex"])[32:64]
    return {
        "schema": "truerecall.scene_overlay.v1", "id": "synthetic", "scene_index": 0,
        "identity": {
            "base_sha1": sc.BASE_SHA1, "palette_retail_pointer": 0x2000,
            "primary_graphics": {
                "retail_descriptor": 0x2200, "retail_primary_lz": 0x2300,
                "secondary_pointer": 0x80001234, "aux_pointer": 0x4567,
                "secondary_plane_descriptor": 0,
                "retail_decoded_sha256": source["primary_graphics"]["retail_decoded_sha256"],
            },
        },
        "palette": [{"index": 1, "expect": 0, "value": 0x0002}],
        "maps": [{"plane": "C000", "x": 1, "y": 0, "expect": 1, "value": 7}],
        "objects": [{"op": "add", "id": "authored_object", "type_id": 69, "status_flags": 0x7800, "stride": 6, "x": 30, "y": 40, "param": None}],
        "world": [{"op": "add", "id": "authored_wall", "type": 9, "rect": [8, 8, 16, 16]}],
        "primary_graphics": [{"tile_index": 1, "expect_sha256": hashlib.sha256(tile1).hexdigest(), "tile_hex": (bytes([0xEE]) * 32).hex()}],
    }


class SceneOverlayStaticTests(unittest.TestCase):
    def test_all_supported_delta_domains_apply_without_mutating_base(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source)
        edited = so.apply_overlay_to_source(source, overlay)
        self.assertEqual(source["palette"]["colors"][1], 0)
        self.assertEqual(edited["palette"]["colors"][1], 2)
        self.assertEqual(edited["planes"]["C000"]["tile_words"][1], 7)
        self.assertEqual(edited["objects"]["records"][-1]["id"], "authored_object")
        self.assertEqual(edited["world"]["records"][-1]["id"], "authored_wall")
        self.assertEqual(bytes.fromhex(edited["primary_graphics"]["tile_bytes_hex"])[32:64], bytes([0xEE]) * 32)

    def test_replace_rect_uses_hash_guard_and_authored_words(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source); plane = source["planes"]["E000"]
        words = [plane["tile_words"][y * 4 + x] for y in range(1, 3) for x in range(1, 3)]
        blob = b"".join(word.to_bytes(2, "big") for word in words)
        overlay["maps"] = [{"op": "replace_rect", "plane": "E000", "x": 1, "y": 1, "width": 2, "height": 2, "expect_sha256": hashlib.sha256(blob).hexdigest(), "tile_words": [101, 102, 103, 104]}]
        edited = so.apply_overlay_to_source(source, overlay)
        actual = [edited["planes"]["E000"]["tile_words"][y * 4 + x] for y in range(1, 3) for x in range(1, 3)]
        self.assertEqual(actual, [101, 102, 103, 104])

    def test_replace_rect_hash_mismatch_is_rejected(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source)
        overlay["maps"] = [{"op": "replace_rect", "plane": "E000", "x": 0, "y": 0, "width": 1, "height": 1, "expect_sha256": "0" * 64, "tile_words": [1]}]
        with self.assertRaises(ValueError): so.apply_overlay_to_source(source, overlay)

    def test_identity_mismatch_is_rejected(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source)
        overlay["identity"]["primary_graphics"]["retail_descriptor"] = 0x2202
        with self.assertRaises(ValueError): so.apply_overlay_to_source(source, overlay)

    def test_duplicate_palette_edits_are_rejected(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source)
        overlay["palette"].append(copy.deepcopy(overlay["palette"][0]))
        with self.assertRaises(ValueError): so.apply_overlay_to_source(source, overlay)

    def test_graphics_expectation_is_enforced(self) -> None:
        source = synthetic_source(); overlay = synthetic_overlay(source)
        overlay["primary_graphics"][0]["expect_sha256"] = "0" * 64
        with self.assertRaises(ValueError): so.apply_overlay_to_source(source, overlay)

    def test_closed_proof_manifest_contains_only_authored_delta_payload(self) -> None:
        manifest = json.loads((ROOT / "tools/build/examples/m120a_scene0_closed_proof_overlay.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "truerecall.scene_overlay.v1")
        self.assertNotIn("planes", manifest)
        self.assertEqual(len(manifest["primary_graphics"]), 1)
        self.assertEqual(len(bytes.fromhex(manifest["primary_graphics"][0]["tile_hex"])), 32)

    def test_l3_starter_uses_verified_resident_tiles_and_hashed_rect(self) -> None:
        manifest = json.loads((ROOT / "tools/build/examples/m120b_l3_urban_subway_starter_overlay.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "PROTOTYPE_VISUAL_PASS_NOT_ART_FREEZE")
        self.assertEqual([row["tile_index"] for row in manifest["primary_graphics"]], list(range(2, 17)))
        self.assertTrue(all(len(bytes.fromhex(row["tile_hex"])) == 32 for row in manifest["primary_graphics"]))
        self.assertEqual(len(manifest["maps"]), 1)
        rect = manifest["maps"][0]
        self.assertEqual(rect["op"], "replace_rect")
        self.assertEqual((rect["x"], rect["y"], rect["width"], rect["height"]), (0, 12, 27, 11))
        self.assertEqual(len(rect["tile_words"]), 27 * 11)
        self.assertEqual(len(rect["expect_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
