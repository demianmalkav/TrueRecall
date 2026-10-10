from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import scene_compiler as sc
import scene_compiler_v2 as sc2
import scene_compiler_v3 as sc3
from lzbeam_codec import decode_stream, encode_stream


def synthetic_rom() -> bytes:
    raw = bytearray(sc.BASE_SIZE)
    scene = 0x1000
    palette = 0x2000
    graphics_desc = 0x2200
    graphics_lz = 0x2300
    c_desc, c_lz = 0x3000, 0x3100
    e_desc, e_lz = 0x3200, 0x3300
    raw[sc.SCENE_TABLE:sc.SCENE_TABLE + 4] = sc.p32(scene)
    raw[scene + 2:scene + 6] = sc.p32(palette)
    raw[scene + 6:scene + 10] = sc.p32(palette)
    raw[scene + 0x16:scene + 0x1A] = sc.p32(graphics_desc)
    raw[scene + 0x22:scene + 0x26] = sc.p32(0)
    raw[graphics_desc:graphics_desc + 12] = sc.p32(graphics_lz) + sc.p32(0x80001234) + sc.p32(0x4567)
    graphics = bytes([0]) * 32 + bytes([0x11]) * 32 + bytes([0x22]) * 32 + bytes([0x33]) * 32
    encoded_graphics = encode_stream(graphics)
    raw[graphics_lz:graphics_lz + len(encoded_graphics)] = encoded_graphics
    for index in range(64):
        raw[palette + index*2:palette + index*2 + 2] = sc.p16((index & 7) << 1)
    raw[scene + 0x1A:scene + 0x1E] = sc.p32(c_desc)
    raw[c_desc:c_desc + 8] = sc.p32(c_lz) + sc.p16(2) + sc.p16(1)
    c_map = sc.p16(1) + sc.p16(2)
    encoded_c = encode_stream(c_map)
    raw[c_lz:c_lz + len(encoded_c)] = encoded_c
    raw[scene + 0x26:scene + 0x2A] = sc.p32(e_desc)
    raw[e_desc:e_desc + 8] = sc.p32(e_lz) + sc.p16(2) + sc.p16(1)
    e_map = sc.p16(2) + sc.p16(3)
    encoded_e = encode_stream(e_map)
    raw[e_lz:e_lz + len(encoded_e)] = encoded_e
    return bytes(raw)


def noop_v2_patch() -> dict:
    return {
        "schema": "truerecall.scene_patch.v2",
        "scene_index": 0,
        "scene_patch": {
            "schema": "truerecall.scene_patch.v1",
            "scene_index": 0,
            "map_operations": [],
            "object_operations": [],
            "world_operations": [],
        },
        "palette_operation": None,
    }


class SceneCompilerV3StaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = synthetic_rom()
        digest = hashlib.sha1(self.raw).hexdigest()
        self.old = (sc.BASE_SHA1, sc2.BASE_SHA1, sc3.BASE_SHA1)
        sc.BASE_SHA1 = sc2.BASE_SHA1 = sc3.BASE_SHA1 = digest

    def tearDown(self) -> None:
        sc.BASE_SHA1, sc2.BASE_SHA1, sc3.BASE_SHA1 = self.old

    def graphics_operation(self) -> dict:
        original = decode_stream(self.raw, 0x2300)
        edited = bytearray(original)
        edited[64:96] = bytes([0xEE]) * 32
        return {
            "op": "replace_primary_graphics",
            "retail_descriptor": 0x2200,
            "retail_primary_lz": 0x2300,
            "secondary_pointer": 0x80001234,
            "aux_pointer": 0x4567,
            "secondary_plane_descriptor": 0,
            "retail_decoded_sha256": hashlib.sha256(original).hexdigest(),
            "changed_tile_indices": [2],
            "tile_count": 4,
            "tile_bytes_hex": bytes(edited).hex(),
        }

    def test_noop_is_exact(self) -> None:
        patch = {"schema": "truerecall.scene_patch.v3", "scene_index": 0, "scene_patch_v2": noop_v2_patch(), "graphics_operation": None}
        out, report = sc3.build_v3(self.raw, patch)
        self.assertEqual(out, self.raw)
        self.assertTrue(report["noop"])

    def test_graphics_only_transaction_uses_v3_floor_and_preserves_identity(self) -> None:
        patch = {"schema": "truerecall.scene_patch.v3", "scene_index": 0, "scene_patch_v2": noop_v2_patch(), "graphics_operation": self.graphics_operation()}
        out, report = sc3.build_v3(self.raw, patch)
        graphics = report["primary_graphics"]
        self.assertEqual(len(out), sc3.DEFAULT_ROM_SIZE)
        self.assertEqual(graphics["new_descriptor"], sc3.GRAPHICS_ALLOCATION_FLOOR)
        self.assertEqual(graphics["new_primary_lz"], sc3.GRAPHICS_ALLOCATION_FLOOR + 0x10)
        self.assertEqual(graphics["changed_tile_indices"], [2])
        self.assertEqual(sc.u32(out, graphics["new_descriptor"] + 4), 0x80001234)
        self.assertEqual(sc.u32(out, graphics["new_descriptor"] + 8), 0x4567)
        self.assertEqual(decode_stream(out, graphics["new_primary_lz"])[64:96], bytes([0xEE]) * 32)
        self.assertEqual(sc.u16(out, sc.CHECKSUM_OFFSET), sc.genesis_checksum(out))

    def test_graphics_allocation_moves_after_existing_v2_ledger(self) -> None:
        self.assertEqual(sc3._next_graphics_address([{"name": "p", "address": 0x304100, "size": 0x80}]), 0x304180)

    def test_declared_changed_tiles_must_match_payload(self) -> None:
        operation = self.graphics_operation()
        operation["changed_tile_indices"] = [1]
        patch = {"schema": "truerecall.scene_patch.v3", "scene_index": 0, "scene_patch_v2": noop_v2_patch(), "graphics_operation": operation}
        with self.assertRaises(ValueError):
            sc3.build_v3(self.raw, patch)


if __name__ == "__main__":
    unittest.main()
