#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from m09c_native_phase_pixel_sequence import BANKS
from m09d_quaid_sprint_build import build as build_player
from scene_compiler import build as build_scene

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 0x200000
OUTPUT_SIZE = 0x400000
CHECKSUM_OFFSET = 0x018E
FROZEN_M09D_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
SCENE_INDEX = 18


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off : off + 2], "big")


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + u16(buf, off)) & 0xFFFF
    return total


def changed_indices(base: bytes, derived: bytes) -> set[int]:
    if len(base) != len(derived):
        raise ValueError("diff buffers must have equal length")
    return {i for i, (a, b) in enumerate(zip(base, derived)) if a != b}


def ranges(indices: Iterable[int]) -> list[list[int]]:
    values = sorted(set(indices))
    if not values:
        return []
    out: list[list[int]] = []
    start = previous = values[0]
    for value in values[1:]:
        if value != previous + 1:
            out.append([start, previous + 1])
            start = value
        previous = value
    out.append([start, previous + 1])
    return out


def compose(
    canonical: bytes,
    player_rom: bytes,
    scene_rom: bytes,
) -> tuple[bytes, dict[str, Any]]:
    if len(canonical) != BASE_SIZE:
        raise ValueError("canonical ROM must be exactly 2 MiB")
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")
    if len(player_rom) != OUTPUT_SIZE or len(scene_rom) != OUTPUT_SIZE:
        raise ValueError("both derived parents must be exactly 4 MiB")

    base4 = canonical + bytes([0xFF]) * (OUTPUT_SIZE - BASE_SIZE)
    player_delta = changed_indices(base4, player_rom)
    scene_delta = changed_indices(base4, scene_rom)
    checksum_bytes = {CHECKSUM_OFFSET, CHECKSUM_OFFSET + 1}
    shared = (player_delta & scene_delta) - checksum_bytes
    conflicts = sorted(i for i in shared if player_rom[i] != scene_rom[i])
    if conflicts:
        preview = ", ".join(f"0x{x:06X}" for x in conflicts[:12])
        raise ValueError(f"M1.0A incompatible parent deltas at {preview}")

    merged = bytearray(player_rom)
    for index in scene_delta - checksum_bytes:
        merged[index] = scene_rom[index]

    merged[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(merged)
    merged[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = checksum.to_bytes(2, "big")
    output = bytes(merged)

    scene_preserved = all(
        output[index] == scene_rom[index]
        for index in scene_delta - checksum_bytes
    )
    player_only = player_delta - scene_delta - checksum_bytes
    player_preserved = all(output[index] == player_rom[index] for index in player_only)

    report = {
        "schema": "truerecall.m100a.compose.v1",
        "base_sha1": BASE_SHA1,
        "player_parent_sha1": hashlib.sha1(player_rom).hexdigest(),
        "scene_parent_sha1": hashlib.sha1(scene_rom).hexdigest(),
        "output_sha1": hashlib.sha1(output).hexdigest(),
        "output_size": len(output),
        "genesis_checksum": f"0x{checksum:04X}",
        "player_delta_bytes": len(player_delta),
        "scene_delta_bytes": len(scene_delta),
        "shared_nonchecksum_bytes": len(shared),
        "shared_ranges": ranges(shared),
        "player_delta_ranges": ranges(player_delta),
        "scene_delta_ranges": ranges(scene_delta),
        "assertions": {
            "no_incompatible_overlap": not conflicts,
            "scene_delta_preserved": scene_preserved,
            "player_only_delta_preserved": player_preserved,
        },
    }
    return output, report


def build(
    canonical: bytes,
    contract: dict[str, Any],
    scene_manifest: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    if scene_manifest.get("schema") != "truerecall.scene_patch.v1":
        raise ValueError("wrong scene manifest schema")
    if int(scene_manifest.get("scene_index", -1)) != SCENE_INDEX:
        raise ValueError("M1.0A baseline is pinned to scene 18")

    player_rom, player_report = build_player(canonical, contract)
    player_sha1 = hashlib.sha1(player_rom).hexdigest()
    if player_sha1 != FROZEN_M09D_SHA1:
        raise ValueError(f"frozen M09D parent changed: {player_sha1}")
    if not player_report["expected_candidate_fingerprint"]["matches"]:
        raise ValueError("M09D frozen fingerprint gate is not green")

    scene_rom, scene_report = build_scene(canonical, scene_manifest)
    output, compose_report = compose(canonical, player_rom, scene_rom)

    player_bank_hashes = [
        hashlib.sha1(output[address : address + 0x8000]).hexdigest()
        for address in BANKS
    ]
    frozen_bank_hashes = list(player_report["phase_bank_sha1"])
    bank_preserved = player_bank_hashes == frozen_bank_hashes

    assertions = {
        **compose_report["assertions"],
        "frozen_player_parent_exact": player_sha1 == FROZEN_M09D_SHA1,
        "frozen_player_phase_banks_preserved": bank_preserved,
        "scene_index_is_18": scene_report["scene_index"] == SCENE_INDEX,
        "scene_build_is_nonempty": bool(
            scene_report.get("objects") or scene_report.get("world") or scene_report.get("maps")
        ),
    }
    if not all(assertions.values()):
        failed = [key for key, value in assertions.items() if not value]
        raise ValueError(f"M1.0A integration assertions failed: {failed}")

    report = {
        "schema": "truerecall.m100a.vertical_slice_baseline.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "player": {
            "sha1": player_sha1,
            "source_art_fingerprint": player_report["source_art_fingerprint"],
            "phase_bank_sha1": frozen_bank_hashes,
        },
        "scene": scene_report,
        "compose": compose_report,
        "output_sha1": hashlib.sha1(output).hexdigest(),
        "output_size": len(output),
        "genesis_checksum": f"0x{int.from_bytes(output[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}",
        "assertions": assertions,
        "direct_runtime_parent_sha1": FROZEN_M09D_SHA1,
        "runtime_status": "NOT_YET_PROVEN",
    }
    return output, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("scene_manifest", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    canonical = args.rom.read_bytes()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    scene_manifest = json.loads(args.scene_manifest.read_text(encoding="utf-8"))
    output, report = build(canonical, contract, scene_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
