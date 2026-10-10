#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "build"))
import scene_graphics as sg
from lzbeam_codec import encode_stream


def synthetic_rom() -> bytes:
    raw = bytearray(sg.BASE_SIZE)
    scene = 0x001000
    descriptor = 0x002000
    primary_lz = 0x003000
    c_desc = 0x004000
    c_lz = 0x004100
    e_desc = 0x005000
    e_lz = 0x005100

    raw[sg.SCENE_TABLE:sg.SCENE_TABLE + 4] = sg.p32(scene)
    raw[scene + sg.PRIMARY_PLANE_OFFSET:scene + sg.PRIMARY_PLANE_OFFSET + 4] = sg.p32(descriptor)
    raw[scene + sg.SECONDARY_PLANE_OFFSET:scene + sg.SECONDARY_PLANE_OFFSET + 4] = sg.p32(0)
    raw[descriptor:descriptor + 12] = sg.p32(primary_lz) + sg.p32(0x80006000) + sg.p32(0x00007000)

    tiles = bytes(range(32)) + bytes(reversed(range(32))) + bytes([0x55] * 32)
    encoded_tiles = encode_stream(tiles)
    raw[primary_lz:primary_lz + len(encoded_tiles)] = encoded_tiles

    for block, map_desc, map_lz, words in (
        (sg.PRIMARY_PLANE_OFFSET, c_desc, c_lz, [0x0000, 0x0001]),
        (sg.SECONDARY_PLANE_OFFSET, e_desc, e_lz, [0x0002, 0x0001]),
    ):
        raw[scene + block + 4:scene + block + 8] = sg.p32(map_desc)
        decoded = b"".join(sg.p16(word) for word in words)
        encoded = encode_stream(decoded)
        raw[map_desc:map_desc + 8] = sg.p32(map_lz) + sg.p16(2) + sg.p16(1)
        raw[map_lz:map_lz + len(encoded)] = encoded
    return bytes(raw)


class SceneGraphicsStaticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = synthetic_rom()
        self.old_sha1 = sg.BASE_SHA1
        sg.BASE_SHA1 = hashlib.sha1(self.raw).hexdigest()

    def tearDown(self) -> None:
        sg.BASE_SHA1 = self.old_sha1

    def test_export_recovers_primary_and_map_bounds(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        self.assertEqual(source["tile_count"], 3)
        self.assertEqual(source["secondary_pointer"], 0x80006000)
        self.assertEqual(source["aux_pointer"], 0x7000)
        self.assertEqual(source["secondary_plane_descriptor"], 0)
        self.assertEqual(source["map_reference_stats"]["C000"]["max_tile_index"], 1)
        self.assertEqual(source["map_reference_stats"]["E000"]["max_tile_index"], 2)

    def test_exact_noop_returns_original_bytes(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        out, report = sg.compile_primary_graphics(self.raw, copy.deepcopy(source))
        self.assertEqual(out, self.raw)
        self.assertTrue(report["noop"])
        self.assertEqual(report["changed_tile_indices"], [])

    def test_force_relocation_preserves_decoded_bytes_and_side_pointers(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        out, report = sg.compile_primary_graphics(self.raw, source, force_relocate=True)
        self.assertFalse(report["noop"])
        self.assertEqual(len(out), sg.DEFAULT_ROM_SIZE)
        self.assertEqual(report["new_descriptor"], sg.DEFAULT_ALLOCATION_BASE)
        self.assertEqual(report["new_primary_lz"], sg.DEFAULT_ALLOCATION_BASE + 0x10)
        self.assertEqual(report["secondary_pointer"], 0x80006000)
        self.assertEqual(report["aux_pointer"], 0x7000)
        self.assertEqual(report["changed_tile_indices"], [])
        scene = sg.scene_address(out, 0)
        self.assertEqual(sg.u32(out, scene + sg.PRIMARY_PLANE_OFFSET), sg.DEFAULT_ALLOCATION_BASE)
        self.assertEqual(sg.u32(out, sg.DEFAULT_ALLOCATION_BASE + 4), 0x80006000)
        self.assertEqual(sg.u32(out, sg.DEFAULT_ALLOCATION_BASE + 8), 0x7000)
        self.assertEqual(sg.u16(out, sg.CHECKSUM_OFFSET), sg.genesis_checksum(out))

    def test_one_tile_edit_is_reported(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        edited = copy.deepcopy(source)
        payload = bytearray.fromhex(edited["tile_bytes_hex"])
        payload[32:64] = bytes([0xAA] * 32)
        edited["tile_bytes_hex"] = payload.hex()
        out, report = sg.compile_primary_graphics(self.raw, edited)
        self.assertNotEqual(out, self.raw)
        self.assertEqual(report["changed_tile_indices"], [1])

    def test_identity_change_is_rejected(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        source["secondary_pointer"] ^= 2
        with self.assertRaises(ValueError):
            sg.compile_primary_graphics(self.raw, source)

    def test_resource_cannot_shrink_below_map_references(self) -> None:
        source = sg.export_primary_graphics(self.raw, 0)
        source["tile_bytes_hex"] = bytes.fromhex(source["tile_bytes_hex"])[:64].hex()
        source["tile_count"] = 2
        with self.assertRaises(ValueError):
            sg.compile_primary_graphics(self.raw, source)


if __name__ == "__main__":
    unittest.main()
