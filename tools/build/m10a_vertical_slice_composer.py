#!/usr/bin/env python3
"""Compose frozen M09D player art with an M11D scene source from one canonical ROM.

Both upstream builders historically start from the immutable 2 MiB retail ROM and
may emit a 4 MiB image. This composer treats both outputs as transformations of a
single canonical 4 MiB base, verifies that overlapping changed bytes agree, merges
the two transformations, then recomputes the Genesis checksum.

The original ROM and exported retail scene-source JSON remain local inputs and are
never committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from m09d_quaid_sprint_build import build as build_player
from scene_source import compile_source, export_scene_source

BASE_SIZE = 0x200000
ROM_SIZE = 0x400000
BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
CHECKSUM_OFFSET = 0x018E
ROM_END_OFFSET = 0x01A4


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + u16(buf, off)) & 0xFFFF
    return total


def canonical_4m(raw: bytes) -> bytes:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical ROM, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong canonical SHA-1: {digest}")
    out = bytearray(raw) + bytearray([0xFF]) * (ROM_SIZE - BASE_SIZE)
    out[ROM_END_OFFSET:ROM_END_OFFSET + 4] = p32(ROM_SIZE - 1)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)
    return bytes(out)


def normalize_output(raw: bytes, output: bytes) -> bytes:
    """Normalize a builder output to the canonical 4 MiB comparison space.

    A true M11D no-op intentionally returns the original 2 MiB ROM. That means
    zero scene transformation, not a request to shrink the integrated output.
    """
    if output == raw:
        return canonical_4m(raw)
    if len(output) != ROM_SIZE:
        raise ValueError(f"builder output must be canonical 2 MiB no-op or 4 MiB, got {len(output)}")
    return output


def changed_bytes(base: bytes, candidate: bytes) -> dict[int, int]:
    if len(base) != len(candidate):
        raise ValueError("diff inputs have different sizes")
    return {
        off: after
        for off, (before, after) in enumerate(zip(base, candidate))
        if before != after and not (CHECKSUM_OFFSET <= off < CHECKSUM_OFFSET + 2)
    }


def coalesce_offsets(offsets: list[int]) -> list[dict[str, int]]:
    if not offsets:
        return []
    values = sorted(offsets)
    rows: list[dict[str, int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        rows.append({"start": start, "end_exclusive": previous + 1, "size": previous + 1 - start})
        start = previous = value
    rows.append({"start": start, "end_exclusive": previous + 1, "size": previous + 1 - start})
    return rows


def compose_outputs(raw: bytes, player_output: bytes, scene_output: bytes) -> tuple[bytes, dict[str, Any]]:
    base = canonical_4m(raw)
    player = normalize_output(raw, player_output)
    scene = normalize_output(raw, scene_output)

    player_diff = changed_bytes(base, player)
    scene_diff = changed_bytes(base, scene)
    overlap = sorted(set(player_diff) & set(scene_diff))
    conflicts = [off for off in overlap if player_diff[off] != scene_diff[off]]
    if conflicts:
        preview = ", ".join(f"0x{x:06X}" for x in conflicts[:16])
        raise ValueError(f"player/scene transformation conflict at {len(conflicts)} bytes: {preview}")

    merged = bytearray(base)
    for off, value in player_diff.items():
        merged[off] = value
    for off, value in scene_diff.items():
        merged[off] = value
    merged[ROM_END_OFFSET:ROM_END_OFFSET + 4] = p32(ROM_SIZE - 1)
    merged[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(merged)
    merged[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)

    report = {
        "schema": "truerecall.m10a.integration_composer.v1",
        "canonical_sha1": BASE_SHA1,
        "player_sha1": hashlib.sha1(player_output).hexdigest(),
        "scene_sha1": hashlib.sha1(scene_output).hexdigest(),
        "scene_is_exact_noop": scene_output == raw,
        "player_changed_bytes": len(player_diff),
        "scene_changed_bytes": len(scene_diff),
        "overlap_changed_bytes": len(overlap),
        "conflict_bytes": len(conflicts),
        "player_changed_ranges": coalesce_offsets(list(player_diff)),
        "scene_changed_ranges": coalesce_offsets(list(scene_diff)),
        "overlap_ranges": coalesce_offsets(overlap),
        "output_size": len(merged),
        "output_sha1": hashlib.sha1(merged).hexdigest(),
        "genesis_checksum": f"0x{checksum:04X}",
    }
    return bytes(merged), report


def build(raw: bytes, contract: dict[str, Any], scene_source: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    player_output, player_report = build_player(raw, contract)
    scene_output, scene_report = compile_source(raw, scene_source)
    merged, merge_report = compose_outputs(raw, player_output, scene_output)
    report = {
        "schema": "truerecall.m10a.vertical_slice_baseline.v1",
        "scene_index": scene_source["scene_index"],
        "player": player_report,
        "scene": scene_report,
        "merge": merge_report,
        "assertions": {
            "canonical_input_verified": hashlib.sha1(raw).hexdigest() == BASE_SHA1,
            "four_megabyte_output": len(merged) == ROM_SIZE,
            "no_transform_conflicts": merge_report["conflict_bytes"] == 0,
            "scene_noop_keeps_frozen_player_build": (
                not scene_report["noop"]
                or hashlib.sha1(merged).hexdigest() == player_report["output_sha1"]
            ),
        },
    }
    if not all(report["assertions"].values()):
        raise ValueError(f"integration assertion failed: {report['assertions']}")
    return merged, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("output", type=Path)
    scene_group = ap.add_mutually_exclusive_group(required=True)
    scene_group.add_argument("--scene-source", type=Path)
    scene_group.add_argument("--noop-scene", type=int)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if args.scene_source is not None:
        source = json.loads(args.scene_source.read_text(encoding="utf-8"))
    else:
        source = export_scene_source(raw, args.noop_scene)

    out, report = build(raw, contract, source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
