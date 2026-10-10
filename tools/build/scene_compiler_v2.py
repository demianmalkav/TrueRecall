#!/usr/bin/env python3
"""Transactional scene compiler v2 with palette allocation.

M11H composes the proven M11B scene compiler with M11F palette authoring while
preserving a single collision-free expanded-ROM allocation plan. The existing
scene compiler runs first for maps/objects/world; palette data is then allocated
after the highest reported allocation and the final checksum is repaired once
more over the complete transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scene_compiler import (
    BASE_SHA1,
    BASE_SIZE,
    CHECKSUM_OFFSET,
    DEFAULT_ALLOCATION_BASE,
    build as build_scene_patch_v1,
    genesis_checksum,
    p16,
    p32,
    parse_int,
    u16,
    u32,
    SCENE_TABLE,
)
from scene_palette import PALETTE_BYTES, PALETTE_WORDS, validate_colors
from scene_source_v2 import PATCH_SCHEMA_V2, export_scene_source_v2, patch_v2_is_noop, source_v2_to_patch

SCENE_RECORD_SIZE = 0x2E


def _validate_base(raw: bytes) -> None:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")


def _scene_patch_is_noop(scene_patch: dict[str, Any]) -> bool:
    return not scene_patch.get("map_operations", []) and not scene_patch.get("object_operations", []) and not scene_patch.get("world_operations", [])


def _palette_words(raw: bytes, pointer: int) -> list[int]:
    if pointer < 0 or pointer + PALETTE_BYTES > len(raw):
        raise ValueError(f"palette pointer out of canonical ROM range: 0x{pointer:06X}")
    colors = [u16(raw, pointer + i * 2) for i in range(PALETTE_WORDS)]
    return list(validate_colors(colors))


def _next_allocation_address(scene_patch: dict[str, Any], stage1_report: dict[str, Any]) -> int:
    allocation_base = parse_int(scene_patch.get("allocation_base", DEFAULT_ALLOCATION_BASE))
    ends = [allocation_base]
    for row in stage1_report.get("allocations", []):
        ends.append(int(row["address"]) + int(row["size"]))
    cursor = max(ends)
    return (cursor + 0x0F) & ~0x0F


def build_v2(raw: bytes, patch: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    _validate_base(raw)
    if patch.get("schema") != PATCH_SCHEMA_V2:
        raise ValueError("unsupported scene patch v2 schema")

    scene_index = parse_int(patch["scene_index"])
    scene_patch = dict(patch["scene_patch"])
    if scene_patch.get("schema") != "truerecall.scene_patch.v1":
        raise ValueError("scene_patch.v2 must embed scene_patch.v1")
    if parse_int(scene_patch["scene_index"]) != scene_index:
        raise ValueError("scene index mismatch inside scene_patch.v2")

    palette_operation = patch.get("palette_operation")
    if _scene_patch_is_noop(scene_patch) and palette_operation is None:
        return raw, {
            "schema": "truerecall.scene_build.v2",
            "base_sha1": BASE_SHA1,
            "scene_index": scene_index,
            "noop": True,
            "scene_stage": None,
            "palette": None,
            "allocations": [],
            "scene_record_changed_offsets": [],
            "rom_size": len(raw),
            "output_sha1": hashlib.sha1(raw).hexdigest(),
            "runtime_validation": "pending",
        }

    stage1_out, stage1_report = build_scene_patch_v1(raw, scene_patch)
    out = bytearray(stage1_out)
    scene = u32(raw, SCENE_TABLE + scene_index * 4)
    retail_scene_record = bytes(raw[scene:scene + SCENE_RECORD_SIZE])

    palette_report = None
    allocations = [dict(row) for row in stage1_report.get("allocations", [])]

    if palette_operation is not None:
        if palette_operation.get("op") != "replace_palette":
            raise ValueError(f"unsupported palette operation: {palette_operation.get('op')}")

        retail_palette0 = u32(raw, scene + 0x02)
        retail_palette1 = u32(raw, scene + 0x06)
        if retail_palette0 != retail_palette1:
            raise ValueError("canonical scene uses split palette pointers")

        expected_pointer = parse_int(palette_operation["retail_pointer"])
        if expected_pointer != retail_palette0:
            raise ValueError("palette operation retail pointer identity mismatch")

        before_colors = _palette_words(raw, retail_palette0)
        after_colors = list(validate_colors(list(palette_operation["colors"])))
        changed_indices = [index for index, (before, after) in enumerate(zip(before_colors, after_colors)) if before != after]
        declared_indices = [parse_int(value) for value in palette_operation["changed_indices"]]
        if declared_indices != changed_indices:
            raise ValueError(f"palette changed_indices mismatch: declared={declared_indices}, actual={changed_indices}")
        if not changed_indices:
            raise ValueError("replace_palette operation contains no color changes")

        palette_address = _next_allocation_address(scene_patch, stage1_report)
        if palette_address + PALETTE_BYTES > len(out):
            raise ValueError("palette allocation exceeds expanded ROM")

        for index, value in enumerate(after_colors):
            start = palette_address + index * 2
            out[start:start + 2] = p16(value)

        out[scene + 0x02:scene + 0x06] = p32(palette_address)
        out[scene + 0x06:scene + 0x0A] = p32(palette_address)

        rebuilt_colors = [u16(out, palette_address + i * 2) for i in range(PALETTE_WORDS)]
        if rebuilt_colors != after_colors:
            raise AssertionError("authored palette reparse mismatch")
        if u32(out, scene + 0x02) != palette_address or u32(out, scene + 0x06) != palette_address:
            raise AssertionError("authored palette pointer patch failed")

        palette_allocation = {"name": "scene_palette", "address": palette_address, "size": PALETTE_BYTES}
        allocations.append(palette_allocation)
        palette_report = {
            "retail_pointer": retail_palette0,
            "new_pointer": palette_address,
            "palette_bytes": PALETTE_BYTES,
            "changed_color_indices": changed_indices,
        }

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)

    authored_scene_record = bytes(out[scene:scene + SCENE_RECORD_SIZE])
    changed_offsets = [index for index, (before, after) in enumerate(zip(retail_scene_record, authored_scene_record)) if before != after]
    allowed_offsets = set(stage1_report.get("scene_record_changed_offsets", []))
    if palette_report is not None:
        allowed_offsets.update(range(0x02, 0x0A))
    if not set(changed_offsets) <= allowed_offsets:
        raise AssertionError((changed_offsets, sorted(allowed_offsets)))

    ordered = sorted(allocations, key=lambda row: int(row["address"]))
    for left, right in zip(ordered, ordered[1:]):
        left_end = int(left["address"]) + int(left["size"])
        if left_end > int(right["address"]):
            raise AssertionError(f"allocation overlap: {left} / {right}")

    report = {
        "schema": "truerecall.scene_build.v2",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "noop": False,
        "scene_stage": stage1_report,
        "palette": palette_report,
        "allocations": allocations,
        "scene_record_changed_offsets": changed_offsets,
        "rom_size": len(out),
        "checksum": f"0x{checksum:04X}",
        "output_sha1": hashlib.sha1(out).hexdigest(),
        "runtime_validation": "pending",
    }
    return bytes(out), report


def compile_source_v2(raw: bytes, source: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    _validate_base(raw)
    base = export_scene_source_v2(raw, source["scene_index"])
    patch = source_v2_to_patch(base, source)
    if patch_v2_is_noop(patch):
        return raw, {
            "schema": "truerecall.scene_source_build.v2",
            "scene_index": source["scene_index"],
            "noop": True,
            "patch": patch,
        }
    out, build_report = build_v2(raw, patch)
    return out, {
        "schema": "truerecall.scene_source_build.v2",
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
        out, report = build_v2(raw, data)
    else:
        out, report = compile_source_v2(raw, data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
