#!/usr/bin/env python3
"""Transactional scene compiler v3 with primary gameplay graphics.

The frozen v2 transaction remains unchanged. v3 consumes its resulting scene
state/ledger, allocates the confirmed primary graphics resource after all prior
allocations (with the closed M1.1B 0x304000 floor), and owns final checksum
repair and final scene-record containment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lzbeam_codec import encode_stream, decode_stream
from scene_compiler import (
    BASE_SHA1,
    BASE_SIZE,
    CHECKSUM_OFFSET,
    ROM_END_OFFSET,
    SCENE_TABLE,
    genesis_checksum,
    p16,
    p32,
    parse_int,
    u32,
)
from scene_compiler_v2 import build_v2
from scene_graphics import PRIMARY_PLANE_OFFSET, TILE_BYTES, descriptor_identity, map_reference_stats
from scene_source_v3 import PATCH_SCHEMA_V3, export_scene_source_v3, patch_v3_is_noop, source_v3_to_patch

DEFAULT_ROM_SIZE = 0x400000
GRAPHICS_ALLOCATION_FLOOR = 0x304000
SCENE_RECORD_SIZE = 0x2E


def _validate_base(raw: bytes) -> None:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")


def align(value: int, alignment: int = 0x10) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _ensure_expanded(stage_out: bytes, rom_size: int = DEFAULT_ROM_SIZE) -> bytearray:
    if len(stage_out) > rom_size:
        raise ValueError("stage output exceeds configured v3 ROM size")
    out = bytearray(stage_out)
    if len(out) < rom_size:
        out += bytearray([0xFF]) * (rom_size - len(out))
    out[ROM_END_OFFSET:ROM_END_OFFSET + 4] = p32(rom_size - 1)
    return out


def _next_graphics_address(allocations: list[dict[str, Any]]) -> int:
    ends = [GRAPHICS_ALLOCATION_FLOOR]
    for row in allocations:
        ends.append(int(row["address"]) + int(row["size"]))
    return align(max(ends))


def _validate_operation_identity(raw: bytes, scene_index: int, operation: dict[str, Any]) -> dict[str, int]:
    identity = descriptor_identity(raw, scene_index)
    expected = {
        "retail_descriptor": identity["descriptor"],
        "retail_primary_lz": identity["primary_lz"],
        "secondary_pointer": identity["secondary"],
        "aux_pointer": identity["aux"],
        "secondary_plane_descriptor": identity["secondary_plane_descriptor"],
    }
    for key, value in expected.items():
        if parse_int(operation[key]) != value:
            raise ValueError(f"graphics operation identity mismatch: {key}")
    retail = decode_stream(raw, identity["primary_lz"])
    digest = hashlib.sha256(retail).hexdigest()
    if str(operation["retail_decoded_sha256"]) != digest:
        raise ValueError("graphics operation retail decoded fingerprint mismatch")
    return identity


def build_v3(raw: bytes, patch: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    _validate_base(raw)
    if patch.get("schema") != PATCH_SCHEMA_V3:
        raise ValueError("unsupported scene patch v3 schema")
    scene_index = parse_int(patch["scene_index"])
    patch_v2 = dict(patch["scene_patch_v2"])
    if parse_int(patch_v2["scene_index"]) != scene_index:
        raise ValueError("scene index mismatch inside scene_patch.v3")
    graphics_operation = patch.get("graphics_operation")

    if patch_v3_is_noop(patch):
        return raw, {
            "schema": "truerecall.scene_build.v3",
            "base_sha1": BASE_SHA1,
            "scene_index": scene_index,
            "noop": True,
            "scene_v2_stage": None,
            "primary_graphics": None,
            "allocations": [],
            "scene_record_changed_offsets": [],
            "rom_size": len(raw),
            "output_sha1": BASE_SHA1,
            "runtime_validation": "pending",
        }

    stage_out, stage_report = build_v2(raw, patch_v2)
    out = _ensure_expanded(stage_out)
    scene = u32(raw, SCENE_TABLE + scene_index * 4)
    retail_scene_record = bytes(raw[scene:scene + SCENE_RECORD_SIZE])
    allocations = [dict(row) for row in stage_report.get("allocations", [])]
    graphics_report = None

    if graphics_operation is not None:
        if graphics_operation.get("op") != "replace_primary_graphics":
            raise ValueError(f"unsupported primary graphics operation: {graphics_operation.get('op')}")
        identity = _validate_operation_identity(raw, scene_index, graphics_operation)
        edited = bytes.fromhex(graphics_operation["tile_bytes_hex"])
        if not edited or len(edited) % TILE_BYTES:
            raise ValueError("primary graphics operation must contain complete Genesis tiles")
        tile_count = len(edited) // TILE_BYTES
        if parse_int(graphics_operation["tile_count"]) != tile_count:
            raise ValueError("primary graphics operation tile_count mismatch")
        original = decode_stream(raw, identity["primary_lz"])
        original_count = len(original) // TILE_BYTES
        changed_tiles = [
            index
            for index in range(max(original_count, tile_count))
            if original[index*TILE_BYTES:(index+1)*TILE_BYTES]
            != edited[index*TILE_BYTES:(index+1)*TILE_BYTES]
        ]
        declared = [parse_int(value) for value in graphics_operation["changed_tile_indices"]]
        if declared != changed_tiles or not changed_tiles:
            raise ValueError(f"graphics changed_tile_indices mismatch: declared={declared}, actual={changed_tiles}")

        refs = map_reference_stats(bytes(out), scene_index)
        for plane, row in refs.items():
            if int(row["max_tile_index"]) >= tile_count:
                raise ValueError(f"{plane} references tile outside authored primary graphics set")

        encoded = encode_stream(edited)
        descriptor_address = _next_graphics_address(allocations)
        lz_address = align(descriptor_address + 12)
        if lz_address + len(encoded) > len(out):
            raise ValueError("primary graphics allocation exceeds expanded ROM")
        out[descriptor_address:descriptor_address + 12] = (
            p32(lz_address) + p32(identity["secondary"]) + p32(identity["aux"])
        )
        out[lz_address:lz_address + len(encoded)] = encoded
        out[scene + PRIMARY_PLANE_OFFSET:scene + PRIMARY_PLANE_OFFSET + 4] = p32(descriptor_address)

        rebuilt = decode_stream(out, lz_address)
        if rebuilt != edited:
            raise AssertionError("v3 primary graphics decode mismatch")
        if u32(out, descriptor_address + 4) != identity["secondary"]:
            raise AssertionError("v3 secondary graphics pointer changed")
        if u32(out, descriptor_address + 8) != identity["aux"]:
            raise AssertionError("v3 auxiliary graphics pointer changed")

        graphics_allocations = [
            {"name": "primary_graphics_descriptor", "address": descriptor_address, "size": 12},
            {"name": "primary_graphics_lz", "address": lz_address, "size": len(encoded)},
        ]
        allocations.extend(graphics_allocations)
        graphics_report = {
            "retail_descriptor": identity["descriptor"],
            "retail_primary_lz": identity["primary_lz"],
            "secondary_pointer": identity["secondary"],
            "aux_pointer": identity["aux"],
            "new_descriptor": descriptor_address,
            "new_primary_lz": lz_address,
            "encoded_bytes": len(encoded),
            "decoded_bytes": len(edited),
            "tile_count": tile_count,
            "changed_tile_indices": changed_tiles,
            "decoded_sha256": hashlib.sha256(edited).hexdigest(),
            "encoded_sha256": hashlib.sha256(encoded).hexdigest(),
            "map_reference_stats": refs,
        }

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)

    authored_scene_record = bytes(out[scene:scene + SCENE_RECORD_SIZE])
    changed_offsets = [
        index
        for index, (before, after) in enumerate(zip(retail_scene_record, authored_scene_record))
        if before != after
    ]
    allowed_offsets = set(stage_report.get("scene_record_changed_offsets", []))
    if graphics_report is not None:
        allowed_offsets.update(range(PRIMARY_PLANE_OFFSET, PRIMARY_PLANE_OFFSET + 4))
    if not set(changed_offsets) <= allowed_offsets:
        raise AssertionError((changed_offsets, sorted(allowed_offsets)))

    ordered = sorted(allocations, key=lambda row: int(row["address"]))
    for left, right in zip(ordered, ordered[1:]):
        if int(left["address"]) + int(left["size"]) > int(right["address"]):
            raise AssertionError(f"allocation overlap: {left} / {right}")

    report = {
        "schema": "truerecall.scene_build.v3",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "noop": False,
        "scene_v2_stage": stage_report,
        "primary_graphics": graphics_report,
        "allocations": ordered,
        "scene_record_changed_offsets": changed_offsets,
        "rom_size": len(out),
        "checksum": f"0x{checksum:04X}",
        "output_sha1": hashlib.sha1(out).hexdigest(),
        "runtime_validation": "pending",
    }
    return bytes(out), report


def compile_source_v3(raw: bytes, source: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    _validate_base(raw)
    base = export_scene_source_v3(raw, source["scene_index"])
    patch = source_v3_to_patch(base, source)
    if patch_v3_is_noop(patch):
        return raw, {
            "schema": "truerecall.scene_source_build.v3",
            "scene_index": source["scene_index"],
            "noop": True,
            "patch": patch,
        }
    out, build_report = build_v3(raw, patch)
    return out, {
        "schema": "truerecall.scene_source_build.v3",
        "scene_index": source["scene_index"],
        "noop": False,
        "patch": patch,
        "build": build_report,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    build_cmd = sub.add_parser("build-patch")
    build_cmd.add_argument("rom", type=Path)
    build_cmd.add_argument("patch", type=Path)
    build_cmd.add_argument("output", type=Path)
    build_cmd.add_argument("--report", type=Path)
    source_cmd = sub.add_parser("compile-source")
    source_cmd.add_argument("rom", type=Path)
    source_cmd.add_argument("source", type=Path)
    source_cmd.add_argument("output", type=Path)
    source_cmd.add_argument("--report", type=Path)
    args = ap.parse_args()
    raw = args.rom.read_bytes()
    data = json.loads((args.patch if args.command == "build-patch" else args.source).read_text(encoding="utf-8"))
    if args.command == "build-patch":
        out, report = build_v3(raw, data)
    else:
        out, report = compile_source_v3(raw, data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
