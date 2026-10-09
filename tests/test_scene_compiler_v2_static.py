#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))

import scene_compiler as sc
import scene_compiler_v2 as sc2
from lzbeam_codec import decode_stream, encode_stream


def synthetic_rom() -> bytes:
    raw = bytearray(sc.BASE_SIZE)
    scene = 0x001000
    palette = 0x002000
    map_desc = 0x003000
    map_lz = 0x004000

    raw[sc.SCENE_TABLE:sc.SCENE_TABLE + 4] = sc.p32(scene)

    raw[scene + 0x02:scene + 0x06] = sc.p32(palette)
    raw[scene + 0x06:scene + 0x0A] = sc.p32(palette)
    colors = [0x0000] * 64
    colors[1] = 0x0002
    colors[2] = 0x0020
    colors[3] = 0x0200
    colors[4] = 0x0EEE
    for index, value in enumerate(colors):
        raw[palette + index * 2:palette + index * 2 + 2] = sc.p16(value)

    decoded_map = sc.p16(1) + sc.p16(2)
    encoded_map = encode_stream(decoded_map)
    raw[scene + 0x1A:scene + 0x1E] = sc.p32(map_desc)
    raw[map_desc:map_desc + 8] = sc.p32(map_lz) + sc.p16(2) + sc.p16(1)
    raw[map_lz:map_lz + len(encoded_map)] = encoded_map
    return bytes(raw)


def empty_scene_patch() -> dict:
    return {
        "schema": "truerecall.scene_patch.v1",
        "scene_index": 0,
        "map_operations": [],
        "object_operations": [],
        "world_operations": [],
    }


def palette_operation(raw: bytes) -> dict:
    colors = [sc.u16(raw, 0x002000 + index * 2) for index in range(64)]
    colors[1] = 0x0222
    return {
        "op": "replace_palette",
        "retail_pointer": 0x002000,
        "changed_indices": [1],
        "colors": colors,
    }


class SceneCompilerV2StaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = synthetic_rom()
        self.old_sc_sha1 = sc.BASE_SHA1
        self.old_sc2_sha1 = sc2.BASE_SHA1
        digest = hashlib.sha1(self.raw).hexdigest()
        sc.BASE_SHA1 = digest
        sc2.BASE_SHA1 = digest

    def tearDown(self) -> None:
        sc.BASE_SHA1 = self.old_sc_sha1
        sc2.BASE_SHA1 = self.old_sc2_sha1

    def test_noop_is_exact_after_base_validation(self) -> None:
        patch = {
            "schema": "truerecall.scene_patch.v2",
            "scene_index": 0,
            "scene_patch": empty_scene_patch(),
            "palette_operation": None,
        }
        out, report = sc2.build_v2(self.raw, patch)
        self.assertEqual(out, self.raw)
        self.assertTrue(report["noop"])
        self.assertEqual(report["allocations"], [])

    def test_wrong_base_is_rejected_even_for_noop(self) -> None:
        patch = {
            "schema": "truerecall.scene_patch.v2",
            "scene_index": 0,
            "scene_patch": empty_scene_patch(),
            "palette_operation": None,
        }
        bad = bytearray(self.raw)
        bad[0x5000] ^= 1
        with self.assertRaises(ValueError):
            sc2.build_v2(bytes(bad), patch)

    def test_palette_changed_indices_must_match_payload(self) -> None:
        operation = palette_operation(self.raw)
        operation["changed_indices"] = [2]
        patch = {
            "schema": "truerecall.scene_patch.v2",
            "scene_index": 0,
            "scene_patch": empty_scene_patch(),
            "palette_operation": operation,
        }
        with self.assertRaises(ValueError):
            sc2.build_v2(self.raw, patch)

    def test_combined_map_and_palette_transaction(self) -> None:
        scene_patch = empty_scene_patch()
        scene_patch["map_operations"] = [
            {"op": "set_tile", "plane": "C000", "x": 1, "y": 0, "value": 3}
        ]
        patch = {
            "schema": "truerecall.scene_patch.v2",
            "scene_index": 0,
            "scene_patch": scene_patch,
            "palette_operation": palette_operation(self.raw),
        }

        out, report = sc2.build_v2(self.raw, patch)
        self.assertFalse(report["noop"])
        self.assertEqual(len(out), 0x400000)
        self.assertEqual(report["scene_stage"]["maps"]["C000"]["changed_words"], 1)
        self.assertEqual(report["palette"]["changed_color_indices"], [1])

        scene = sc.u32(out, sc.SCENE_TABLE)
        new_map_desc = sc.u32(out, scene + 0x1A)
        new_map_lz = sc.u32(out, new_map_desc)
        rebuilt_map = decode_stream(out, new_map_lz)
        self.assertEqual(rebuilt_map, sc.p16(1) + sc.p16(3))

        new_palette = report["palette"]["new_pointer"]
        self.assertEqual(sc.u32(out, scene + 0x02), new_palette)
        self.assertEqual(sc.u32(out, scene + 0x06), new_palette)
        self.assertEqual(sc.u16(out, new_palette + 2), 0x0222)

        allocations = sorted(report["allocations"], key=lambda row: row["address"])
        for left, right in zip(allocations, allocations[1:]):
            self.assertLessEqual(left["address"] + left["size"], right["address"])
        self.assertEqual(allocations[-1]["name"], "scene_palette")

        self.assertEqual(sc.u16(out, sc.CHECKSUM_OFFSET), sc.genesis_checksum(out))
        self.assertEqual(report["output_sha1"], hashlib.sha1(out).hexdigest())
        self.assertTrue(set(report["scene_record_changed_offsets"]) <= set(range(0x02, 0x0A)) | set(range(0x1A, 0x1E)))


if __name__ == "__main__":
    unittest.main()
