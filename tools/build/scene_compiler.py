#!/usr/bin/env python3
"""Compile one declarative TrueRecall scene patch across maps, placements and world collision.

Schema: truerecall.scene_patch.v1

The compiler expands the canonical ROM when needed, allocates edited resources in a
single monotonic expanded-ROM arena, patches only the scene-record pointers for
resource families actually edited, repairs the Genesis checksum and emits a build
manifest describing every relocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from lzbeam_codec import decode_stream, encode_stream
from object_stream_codec import parse_scene, Placement, serialize_compiled, build_descriptor
from world_collision_codec import SCENE_COUNT, discover_scene_layout, parse_index
from world_collision_manifest import export_scene, apply_ops as apply_world_ops, compile_manifest

SCENE_TABLE = 0x013B4A
BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 0x200000
DEFAULT_ROM_SIZE = 0x400000
DEFAULT_ALLOCATION_BASE = 0x300000
ROM_END_OFFSET = 0x01A4
CHECKSUM_OFFSET = 0x018E
TYPE_MASK = 0x03FF

PLANE_BLOCKS = {
    "C000": 0x16,
    "E000": 0x22,
}


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+2], "big")


def u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+4], "big")


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def parse_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(value)


def align(value: int, alignment: int = 2) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + u16(buf, off)) & 0xFFFF
    return total


class ExpandedAllocator:
    def __init__(self, start: int, end: int):
        self.cursor = start
        self.end = end
        self.allocations: list[dict[str, int | str]] = []

    def alloc(self, name: str, size: int, alignment: int = 0x10) -> int:
        address = align(self.cursor, alignment)
        if address + size > self.end:
            raise ValueError(f"expanded allocation overflow for {name}")
        self.allocations.append({"name": name, "address": address, "size": size})
        self.cursor = address + size
        return address


def apply_object_operations(base: list[Placement], operations: list[dict[str, Any]]) -> list[Placement]:
    rows = [(replace(p), p.index) for p in base]
    next_order = max((order for _p, order in rows), default=-1) + 1

    for op_number, op in enumerate(operations):
        kind = op["op"]
        if kind == "add":
            stride = parse_int(op.get("stride", 6))
            param = op.get("param")
            param = None if param is None else parse_int(param)
            if stride == 8 and param is None:
                raise ValueError("8-byte add requires param")
            if stride == 6 and param is not None:
                raise ValueError("6-byte add cannot carry param")
            if stride not in (6, 8):
                raise ValueError("stride must be 6 or 8")
            type_id = parse_int(op["type_id"])
            flags = parse_int(op.get("status_flags", "0x7800"))
            placement = Placement(
                -1,
                stride,
                (flags & ~TYPE_MASK) | type_id,
                parse_int(op["x"]),
                parse_int(op["y"]),
                param,
                -1,
            )
            rows.append((placement, next_order))
            next_order += 1
            continue

        if kind not in ("replace", "remove"):
            raise ValueError(f"unknown object operation {kind}")

        base_index = parse_int(op["base_index"])
        hits = [i for i, (p, order) in enumerate(rows) if p.index == base_index and order == base_index]
        if len(hits) != 1:
            raise ValueError(f"base_index {base_index} not uniquely present at operation {op_number}")
        pos = hits[0]

        if kind == "remove":
            rows.pop(pos)
            continue

        p, order = rows[pos]
        stride = parse_int(op.get("stride", p.stride))
        param = op.get("param", p.param)
        param = None if param is None else parse_int(param)
        if stride == 8 and param is None:
            raise ValueError("8-byte replace requires param")
        if stride == 6:
            param = None
        if stride not in (6, 8):
            raise ValueError("stride must be 6 or 8")
        type_id = parse_int(op.get("type_id", p.type_id))
        flags = parse_int(op.get("status_flags", p.status_flags))
        rows[pos] = (
            Placement(
                p.index,
                stride,
                (flags & ~TYPE_MASK) | type_id,
                parse_int(op.get("x", p.x)),
                parse_int(op.get("y", p.y)),
                param,
                -1,
            ),
            order,
        )

    rows.sort(key=lambda item: (item[0].y, item[1]))
    return [replace(p, index=i) for i, (p, _order) in enumerate(rows)]


def world_payload_length(raw: bytes, scene_index: int, layout: dict[str, Any]) -> tuple[int, str]:
    """Choose a conservative retail payload boundary.

    The next higher world-resource base is used when one exists, preserving any
    unknown trailing retail bytes. Only the highest-address world resource falls
    back to the recovered structural end.
    """
    base = layout["world_base"]
    world_bases = []
    for i in range(SCENE_COUNT):
        scene = u32(raw, SCENE_TABLE + i * 4)
        world_bases.append(u32(raw, scene + 0x0E))
    higher = [candidate for candidate in world_bases if candidate > base]
    if higher:
        return min(higher) - base, "next_world_base"
    return max(layout["record_end"], layout["sentinel"] + 2), "structural_fallback"


def assign_world_offsets(operations: list[dict[str, Any]], payload_length: int) -> list[dict[str, Any]]:
    cursor = align(payload_length, 0x10)
    result = []
    for operation in operations:
        op = dict(operation)
        if op["op"] == "add" and "offset" not in op:
            op["offset"] = cursor
            cursor = align(cursor + 10, 0x10)
        result.append(op)
    return result


def build(raw: bytes, manifest: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")
    if manifest.get("schema") != "truerecall.scene_patch.v1":
        raise ValueError("unsupported scene manifest schema")

    scene_index = parse_int(manifest["scene_index"])
    if not 0 <= scene_index < SCENE_COUNT:
        raise ValueError(scene_index)
    scene = u32(raw, SCENE_TABLE + scene_index * 4)
    retail_scene_record = bytes(raw[scene:scene+0x2E])

    rom_size = parse_int(manifest.get("rom_size", DEFAULT_ROM_SIZE))
    if rom_size < BASE_SIZE:
        raise ValueError("output ROM cannot shrink below canonical base")
    allocation_base = parse_int(manifest.get("allocation_base", DEFAULT_ALLOCATION_BASE))
    if allocation_base < BASE_SIZE:
        raise ValueError("scene compiler allocations must live in expanded ROM")

    out = bytearray(raw) + bytearray([0xFF]) * (rom_size - len(raw))
    out[ROM_END_OFFSET:ROM_END_OFFSET+4] = p32(rom_size - 1)
    allocator = ExpandedAllocator(allocation_base, rom_size)

    report: dict[str, Any] = {
        "schema": "truerecall.scene_build.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "maps": {},
        "objects": None,
        "world": None,
    }
    allowed_scene_offsets: set[int] = set()

    # Gameplay planes.
    map_operations = manifest.get("map_operations", [])
    for plane_name, block_offset in PLANE_BLOCKS.items():
        operations = [op for op in map_operations if op["plane"] == plane_name]
        if not operations:
            continue

        retail_map_desc = u32(raw, scene + block_offset + 4)
        retail_lz = u32(raw, retail_map_desc)
        width = u16(raw, retail_map_desc + 4)
        height = u16(raw, retail_map_desc + 6)
        original = decode_stream(raw, retail_lz)
        edited = bytearray(original)
        edits = []

        for op in operations:
            if op["op"] != "set_tile":
                raise ValueError(f"unsupported map operation {op['op']}")
            x = parse_int(op["x"])
            y = parse_int(op["y"])
            value = parse_int(op["value"])
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError((plane_name, x, y, width, height))
            pos = (y * width + x) * 2
            before = u16(edited, pos)
            edited[pos:pos+2] = p16(value)
            edits.append({"x": x, "y": y, "before": before, "after": value})

        encoded = encode_stream(bytes(edited))
        descriptor_address = allocator.alloc(f"{plane_name}_map_desc", 8)
        lz_address = allocator.alloc(f"{plane_name}_map_lz", len(encoded))
        out[descriptor_address:descriptor_address+8] = p32(lz_address) + p16(width) + p16(height)
        out[lz_address:lz_address+len(encoded)] = encoded
        out[scene+block_offset+4:scene+block_offset+8] = p32(descriptor_address)
        allowed_scene_offsets.update(range(block_offset + 4, block_offset + 8))

        rebuilt = decode_stream(out, lz_address)
        assert rebuilt == bytes(edited)
        changed_words = sum(
            original[i:i+2] != rebuilt[i:i+2]
            for i in range(0, len(original), 2)
        )
        report["maps"][plane_name] = {
            "dimensions": [width, height],
            "old_descriptor": retail_map_desc,
            "new_descriptor": descriptor_address,
            "new_lz": lz_address,
            "encoded_bytes": len(encoded),
            "changed_words": changed_words,
            "edits": edits,
        }

    # Persistent placements.
    object_operations = manifest.get("object_operations", [])
    if object_operations:
        stream = parse_scene(raw, scene_index)
        placements = apply_object_operations(stream.placements, object_operations)
        decoded, runs = serialize_compiled(stream.prefix, placements)
        encoded = encode_stream(decoded)
        descriptor_size = 10 + 2 * len(runs)
        descriptor_address = allocator.alloc("object_desc", descriptor_size)
        lz_address = allocator.alloc("object_lz", len(encoded))
        descriptor = build_descriptor(
            count=len(placements),
            start=len(stream.prefix),
            end=len(decoded),
            source_lz=lz_address,
            runs=runs,
        )
        out[descriptor_address:descriptor_address+len(descriptor)] = descriptor
        out[lz_address:lz_address+len(encoded)] = encoded
        out[scene+0x0A:scene+0x0E] = p32(descriptor_address)
        allowed_scene_offsets.update(range(0x0A, 0x0E))

        rebuilt = parse_scene(bytes(out), scene_index)
        expected_rows = [(p.stride, p.status, p.x, p.y, p.param) for p in placements]
        actual_rows = [(p.stride, p.status, p.x, p.y, p.param) for p in rebuilt.placements]
        assert actual_rows == expected_rows
        report["objects"] = {
            "base_count": stream.placement_count,
            "new_count": len(placements),
            "new_descriptor": descriptor_address,
            "new_lz": lz_address,
            "encoded_bytes": len(encoded),
            "stride_runs": [list(row) for row in runs],
            "operations": object_operations,
        }

    # World collision/material rectangles.
    world_operations = manifest.get("world_operations", [])
    if world_operations:
        layout = discover_scene_layout(raw, scene_index)
        payload_length, payload_boundary_source = world_payload_length(raw, scene_index, layout)
        operations = assign_world_offsets(world_operations, payload_length)
        world_manifest = apply_world_ops(export_scene(raw, scene_index), operations)

        max_record_end = max(
            [payload_length] + [record["offset"] + 10 for record in world_manifest["records"]]
        )
        pool_start = align(max_record_end, 0x10)
        compiled = compile_manifest(world_manifest, pool_start=pool_start)
        sentinel = pool_start + len(compiled["pool"])
        resource_size = align(max(sentinel + 2, max_record_end), 0x10)
        world_address = allocator.alloc("world_resource", resource_size, 0x100)

        # Preserve the conservative retail payload first, then overlay authored
        # grid/records and a remote deduplicated list pool.
        out[world_address:world_address+payload_length] = raw[
            layout["world_base"]:layout["world_base"]+payload_length
        ]
        out[world_address:world_address+len(compiled["grid"])] = compiled["grid"]
        for record_offset, record_bytes in compiled["record_bytes"].items():
            if record_offset >= 0x8000:
                raise ValueError("world record offset exceeds 15-bit list-reference space")
            out[world_address+record_offset:world_address+record_offset+10] = record_bytes
        out[world_address+pool_start:world_address+sentinel] = compiled["pool"]
        out[world_address+sentinel:world_address+sentinel+2] = b"\xFF\xFF"
        out[scene+0x0E:scene+0x12] = p32(world_address)
        allowed_scene_offsets.update(range(0x0E, 0x12))

        _grid, lists, memberships = parse_index(
            out[world_address:], layout["grid_bytes"], sentinel
        )
        assert memberships == compiled["memberships"]
        valid_records = set(compiled["record_bytes"])
        assert all(ref in valid_records for refs in lists.values() for ref in refs)

        report["world"] = {
            "old_base": layout["world_base"],
            "new_base": world_address,
            "retail_payload_bytes": payload_length,
            "payload_boundary_source": payload_boundary_source,
            "record_count": len(world_manifest["records"]),
            "pool_start": pool_start,
            "pool_bytes": len(compiled["pool"]),
            "sentinel": sentinel,
            "operations": operations,
        }

    # Scene-record containment and final checksum.
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2] = p16(checksum)

    authored_scene_record = bytes(out[scene:scene+0x2E])
    changed_offsets = [
        i for i, (before, after) in enumerate(zip(retail_scene_record, authored_scene_record))
        if before != after
    ]
    if not set(changed_offsets) <= allowed_scene_offsets:
        raise AssertionError((changed_offsets, sorted(allowed_scene_offsets)))

    report["scene_record_changed_offsets"] = changed_offsets
    report["allocations"] = allocator.allocations
    report["rom_size"] = len(out)
    report["checksum"] = f"0x{checksum:04X}"
    report["output_sha1"] = hashlib.sha1(out).hexdigest()
    report["runtime_validation"] = "pending"
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    out, report = build(raw, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
