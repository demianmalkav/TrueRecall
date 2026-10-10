#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from m09d_quaid_sprint_build import build as build_m09d
from scene_compiler import CHECKSUM_OFFSET, ROM_END_OFFSET, genesis_checksum, p16, p32
from scene_source import compile_source, export_scene_source

CANONICAL_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
M09D_V9_SHA1 = "eccbd54596c932ba3d7d2361af2437e59087b853"
M09D_V9_CHECKSUM = "0x7DCB"
M11D_SCENE18_SHA1 = "fac81fdc87b76a75c9b590d58707b16fcd6a5f04"
EXPECTED_COMBINED_SHA1 = "b96cfb9652a4c5dce7142fe0e03bfb1b257cc474"
EXPECTED_COMBINED_CHECKSUM = "0x5E8B"
ROM_SIZE = 0x400000

Range = tuple[int, int]


def expanded_canonical(raw: bytes) -> bytes:
    if hashlib.sha1(raw).hexdigest() != CANONICAL_SHA1 or len(raw) != 0x200000:
        raise ValueError("wrong canonical base")
    out = bytearray(raw) + bytearray([0xFF]) * (ROM_SIZE - len(raw))
    out[ROM_END_OFFSET : ROM_END_OFFSET + 4] = p32(ROM_SIZE - 1)
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = b"\x00\x00"
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = p16(genesis_checksum(out))
    return bytes(out)


def diff_ranges(
    base: bytes,
    candidate: bytes,
    *,
    ignored_ranges: Iterable[Range] = ((CHECKSUM_OFFSET, CHECKSUM_OFFSET + 2),),
) -> list[Range]:
    if len(base) != len(candidate):
        raise ValueError("diff inputs must have equal length")
    ignored = tuple(ignored_ranges)
    offsets = [
        i
        for i, (before, after) in enumerate(zip(base, candidate))
        if before != after and not any(start <= i < end for start, end in ignored)
    ]
    if not offsets:
        return []
    result: list[Range] = []
    start = previous = offsets[0]
    for offset in offsets[1:]:
        if offset == previous + 1:
            previous = offset
            continue
        result.append((start, previous + 1))
        start = previous = offset
    result.append((start, previous + 1))
    return result


def intersect_ranges(left: Iterable[Range], right: Iterable[Range]) -> list[Range]:
    intersections: list[Range] = []
    for a0, a1 in left:
        for b0, b1 in right:
            start = max(a0, b0)
            end = min(a1, b1)
            if start < end:
                intersections.append((start, end))
    return intersections


def integration_scene_source(raw: bytes) -> dict[str, Any]:
    source = deepcopy(export_scene_source(raw, 18))
    source["planes"]["C000"]["tile_words"][0] = 0x0001
    source["objects"]["records"].append(
        {
            "id": "new_health_0",
            "type_id": 54,
            "status_flags": 0x7800,
            "stride": 6,
            "x": 128,
            "y": 120,
            "param": None,
        }
    )
    source["world"]["records"].append(
        {
            "id": "new_wall_0",
            "type": 9,
            "rect": [64, 64, 80, 256],
        }
    )
    return source


def verify_scene18(rom: bytes) -> dict[str, Any]:
    source = export_scene_source(rom, 18)
    health = [
        row
        for row in source["objects"]["records"]
        if row["type_id"] == 54 and row["x"] == 128 and row["y"] == 120 and row["stride"] == 6
    ]
    walls = [
        row
        for row in source["world"]["records"]
        if row["type"] == 9 and row["rect"] == [64, 64, 80, 256]
    ]
    result = {
        "c000_tile_0": source["planes"]["C000"]["tile_words"][0],
        "matching_health_objects": len(health),
        "matching_world_walls": len(walls),
    }
    if result != {
        "c000_tile_0": 1,
        "matching_health_objects": 1,
        "matching_world_walls": 1,
    }:
        raise AssertionError(result)
    return result


def apply_ranges(target: bytearray, source: bytes, ranges: Iterable[Range]) -> None:
    for start, end in ranges:
        target[start:end] = source[start:end]


def build(raw: bytes, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    baseline = expanded_canonical(raw)

    m09d, m09d_report = build_m09d(raw, contract)
    if hashlib.sha1(m09d).hexdigest() != M09D_V9_SHA1:
        raise AssertionError("frozen M09D v9 fingerprint changed")
    if m09d_report["genesis_checksum"] != M09D_V9_CHECKSUM:
        raise AssertionError("frozen M09D v9 checksum changed")

    scene_source = integration_scene_source(raw)
    scene_rom, scene_report = compile_source(raw, scene_source)
    scene_sha1 = hashlib.sha1(scene_rom).hexdigest()
    if scene_sha1 != M11D_SCENE18_SHA1:
        raise AssertionError(f"M11D scene-18 proof changed: {scene_sha1}")

    m09d_ranges = diff_ranges(baseline, m09d)
    scene_ranges = diff_ranges(baseline, scene_rom)
    intersections = intersect_ranges(m09d_ranges, scene_ranges)
    if intersections:
        raise ValueError(f"unplanned M09D/M11D range overlap: {intersections}")

    out = bytearray(scene_rom)
    apply_ranges(out, m09d, m09d_ranges)
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = p16(checksum)
    combined = bytes(out)

    # Both source layers must survive composition byte-for-byte in their own
    # changed ranges. The shared Genesis checksum is intentionally recomputed last.
    for start, end in m09d_ranges:
        if combined[start:end] != m09d[start:end]:
            raise AssertionError(("m09d_range_corruption", start, end))
    for start, end in scene_ranges:
        if combined[start:end] != scene_rom[start:end]:
            raise AssertionError(("scene_range_corruption", start, end))

    reparsed = verify_scene18(combined)
    output_sha1 = hashlib.sha1(combined).hexdigest()
    checksum_text = f"0x{checksum:04X}"
    if output_sha1 != EXPECTED_COMBINED_SHA1 or checksum_text != EXPECTED_COMBINED_CHECKSUM:
        raise AssertionError((output_sha1, checksum_text))

    allocations = scene_report["build"]["allocations"]
    allocation_floor = min(row["address"] for row in allocations)
    report = {
        "schema": "truerecall.m1a.integration_build.v1",
        "base_sha1": CANONICAL_SHA1,
        "m09d_sha1": M09D_V9_SHA1,
        "m11d_scene18_sha1": M11D_SCENE18_SHA1,
        "output_sha1": output_sha1,
        "output_size": len(combined),
        "genesis_checksum": checksum_text,
        "m09d_changed_range_count": len(m09d_ranges),
        "scene_changed_range_count": len(scene_ranges),
        "range_intersections": intersections,
        "scene_allocation_floor": f"0x{allocation_floor:06X}",
        "scene_allocations": allocations,
        "scene_patch": scene_report["patch"],
        "scene_reparse": reparsed,
        "assertions": {
            "frozen_m09d_fingerprint": True,
            "canonical_m11d_scene18_fingerprint": True,
            "no_unplanned_range_overlap": not intersections,
            "scene_allocations_at_or_above_0x300000": allocation_floor >= 0x300000,
            "scene_reparse_exact": reparsed
            == {
                "c000_tile_0": 1,
                "matching_health_objects": 1,
                "matching_world_walls": 1,
            },
            "combined_fingerprint_pinned": True,
        },
        "runtime_validation": "required separately against M09D v9 logical parent",
    }
    return combined, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    out, report = build(raw, contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
