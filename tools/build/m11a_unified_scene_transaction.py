#!/usr/bin/env python3
"""M0.11A: edit map, placements and world collision in one scene transaction."""
from __future__ import annotations
import argparse, hashlib, json
from dataclasses import replace
from pathlib import Path

from lzbeam_codec import decode_stream, encode_stream
from object_stream_codec import parse_scene, Placement, serialize_compiled, build_descriptor
from world_collision_manifest import export_scene, apply_ops, compile_manifest

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
SCENE_TABLE = 0x013B4A
SCENE_INDEX = 18
ROM_END_OFF = 0x01A4
CHECKSUM_OFF = 0x018E

MAP_DESC = 0x300000
MAP_LZ = 0x300010
OBJECT_DESC = 0x310000
OBJECT_LZ = 0x310020
WORLD_BASE = 0x320000
WORLD_POOL = 0x0180
WORLD_RECORD = 0x0200

EXPECTED_OUTPUT_SHA1 = "c16829235a57d9e88cfe51936b2b4b04f7188f49"
EXPECTED_CHECKSUM = 0x39F4


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+2], "big")


def u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+4], "big")


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + u16(buf, off)) & 0xFFFF
    return total


def build(raw: bytes):
    assert len(raw) == OLD_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    scene = u32(raw, SCENE_TABLE + SCENE_INDEX * 4)
    assert scene == 0x013ED6
    retail_scene = raw[scene:scene+0x2E]

    out = bytearray(raw) + bytearray([0xFF]) * (NEW_SIZE - OLD_SIZE)
    out[ROM_END_OFF:ROM_END_OFF+4] = p32(NEW_SIZE - 1)

    # 1. C000 gameplay map: one controlled tile-word edit.
    block = 0x16
    retail_map_desc = u32(raw, scene + block + 4)
    retail_map_lz = u32(raw, retail_map_desc)
    width = u16(raw, retail_map_desc + 4)
    height = u16(raw, retail_map_desc + 6)
    assert (width, height) == (18, 40)
    original_map = decode_stream(raw, retail_map_lz)
    edited_map = bytearray(original_map)
    assert u16(edited_map, 0) == 0x00CD
    edited_map[0:2] = p16(0x0001)
    encoded_map = encode_stream(bytes(edited_map))
    out[MAP_DESC:MAP_DESC+8] = p32(MAP_LZ) + p16(width) + p16(height)
    out[MAP_LZ:MAP_LZ+len(encoded_map)] = encoded_map
    out[scene+block+4:scene+block+8] = p32(MAP_DESC)

    # 2. Persistent placements: insert one stride-6 health pickup into a retail
    #    stride-8 stream, forcing mixed run regeneration.
    stream = parse_scene(raw, SCENE_INDEX)
    assert stream.placement_count == 40 and stream.stride_runs == [(8, 40)]
    rows = [(replace(p), p.index) for p in stream.placements]
    status = 0x7800 | 54
    rows.append((Placement(-1, 6, status, 128, 120, None, -1), len(rows)))
    rows.sort(key=lambda item: (item[0].y, item[1]))
    placements = [replace(p, index=i) for i, (p, _order) in enumerate(rows)]
    decoded_objects, runs = serialize_compiled(stream.prefix, placements)
    assert runs == [(8, 2), (6, 1), (8, 38)]
    encoded_objects = encode_stream(decoded_objects)
    descriptor = build_descriptor(
        count=len(placements),
        start=len(stream.prefix),
        end=len(decoded_objects),
        source_lz=OBJECT_LZ,
        runs=runs,
    )
    assert len(descriptor) <= 0x20
    out[OBJECT_DESC:OBJECT_DESC+len(descriptor)] = descriptor
    out[OBJECT_LZ:OBJECT_LZ+len(encoded_objects)] = encoded_objects
    out[scene+0x0A:scene+0x0E] = p32(OBJECT_DESC)

    # 3. World collision: scene 18 is retail-empty. Add one completely new wall.
    world_manifest = export_scene(raw, SCENE_INDEX)
    assert world_manifest["grid"] == [9, 20] and world_manifest["records"] == []
    world_manifest = apply_ops(world_manifest, [{
        "op": "add",
        "id": "authored_wall_0",
        "offset": WORLD_RECORD,
        "type": 9,
        "rect": [64, 64, 80, 256],
    }])
    world = compile_manifest(world_manifest, pool_start=WORLD_POOL)
    changed_cells = [i for i, refs in enumerate(world["memberships"]) if refs]
    assert changed_cells == [10, 19, 28]
    assert len(world["pool"]) == 2
    assert world["record_bytes"][WORLD_RECORD] == bytes.fromhex("00090040004000500100")

    sentinel = WORLD_POOL + len(world["pool"])
    out[WORLD_BASE:WORLD_BASE+len(world["grid"])] = world["grid"]
    out[WORLD_BASE+len(world["grid"]):WORLD_BASE+WORLD_POOL] = b"\x00" * (WORLD_POOL - len(world["grid"]))
    out[WORLD_BASE+WORLD_POOL:WORLD_BASE+sentinel] = world["pool"]
    out[WORLD_BASE+sentinel:WORLD_BASE+sentinel+2] = b"\xFF\xFF"
    out[WORLD_BASE+sentinel+2:WORLD_BASE+WORLD_RECORD] = b"\x00" * (WORLD_RECORD - sentinel - 2)
    out[WORLD_BASE+WORLD_RECORD:WORLD_BASE+WORLD_RECORD+10] = world["record_bytes"][WORLD_RECORD]
    out[scene+0x0E:scene+0x12] = p32(WORLD_BASE)

    # Checksum and post-build reparse.
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = p16(checksum)

    new_map_desc = u32(out, scene + block + 4)
    assert new_map_desc == MAP_DESC
    rebuilt_map = decode_stream(out, u32(out, new_map_desc))
    map_diffs = [i for i in range(0, len(original_map), 2) if original_map[i:i+2] != rebuilt_map[i:i+2]]
    assert map_diffs == [0] and u16(rebuilt_map, 0) == 0x0001

    rebuilt_objects = parse_scene(bytes(out), SCENE_INDEX)
    assert rebuilt_objects.placement_count == 41
    assert rebuilt_objects.stride_runs == [(8, 2), (6, 1), (8, 38)]
    inserted = [p for p in rebuilt_objects.placements if p.type_id == 54 and p.x == 128 and p.y == 120 and p.stride == 6]
    assert len(inserted) == 1

    after_scene = bytes(out[scene:scene+0x2E])
    scene_diffs = [i for i, (a, b) in enumerate(zip(retail_scene, after_scene)) if a != b]
    allowed = set(range(0x0A, 0x12)) | set(range(0x1A, 0x1E))
    assert set(scene_diffs) <= allowed

    digest = hashlib.sha1(out).hexdigest()
    assert checksum == EXPECTED_CHECKSUM
    assert digest == EXPECTED_OUTPUT_SHA1

    report = {
        "schema": "truerecall.m11a.unified_scene_transaction.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "map": {
            "plane": "C000",
            "dimensions": [width, height],
            "edit": {"x": 0, "y": 0, "from": "0x00CD", "to": "0x0001"},
            "new_descriptor": f"0x{MAP_DESC:06X}",
            "new_lz": f"0x{MAP_LZ:06X}",
            "encoded_bytes": len(encoded_map),
            "changed_words": 1,
        },
        "objects": {
            "base_count": stream.placement_count,
            "new_count": rebuilt_objects.placement_count,
            "inserted": {"type_id": 54, "x": 128, "y": 120, "stride": 6},
            "stride_runs": [list(x) for x in runs],
            "new_descriptor": f"0x{OBJECT_DESC:06X}",
            "new_lz": f"0x{OBJECT_LZ:06X}",
            "encoded_bytes": len(encoded_objects),
        },
        "world": {
            "base_records": 0,
            "new_records": 1,
            "new_base": f"0x{WORLD_BASE:06X}",
            "record_offset": f"0x{WORLD_RECORD:04X}",
            "record": {"type": 9, "rect": [64, 64, 80, 256]},
            "pool_start": f"0x{WORLD_POOL:04X}",
            "pool_bytes": len(world["pool"]),
            "changed_cells": changed_cells,
            "changed_cell_xy": [[i % 9, i // 9] for i in changed_cells],
        },
        "scene_record_changed_pointer_fields_only": True,
        "rom_size": len(out),
        "checksum": f"0x{checksum:04X}",
        "output_sha1": digest,
        "runtime_validation": "pending",
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    out, report = build(args.rom.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
