#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from m09c_native_phase_pixel_sequence import BANKS
from m09d_quaid_sprint_build import build as build_player
from m100a_vertical_slice_baseline import compose
from scene_compiler import BASE_SHA1
from scene_compiler_v2 import compile_source_v2
from scene_source_v2 import export_scene_source_v2

SCENE_INDEX = 0
PALETTE_INDEX = 8
PALETTE_BEFORE = 0x0464
PALETTE_AFTER = 0x0648
PLAYER_PALETTE_RANGE = range(32, 48)
FROZEN_M09D_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_SCENE_V2_SHA1 = "427b842188b29e4fa040802c94b7d60fe44976cc"
EXPECTED_SCENE_V2_CHECKSUM = "0xA30C"
EXPECTED_OUTPUT_SHA1 = "270e1d633db7883c9170bb1e4eb367abdf97a2bd"
EXPECTED_OUTPUT_CHECKSUM = "0x6B9E"
EXPECTED_PALETTE_POINTER = 0x303080
CHECKSUM_OFFSET = 0x018E


def edit_scene_source(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("schema") != "truerecall.scene_source.v2":
        raise ValueError("M1.1A requires scene_source.v2")
    if int(source.get("scene_index", -1)) != SCENE_INDEX:
        raise ValueError("M1.1A is pinned to scene 0")
    if PALETTE_INDEX in PLAYER_PALETTE_RANGE:
        raise AssertionError("environment palette edit overlaps frozen player line")

    edited = deepcopy(source)
    before = int(edited["palette"]["colors"][PALETTE_INDEX])
    if before != PALETTE_BEFORE:
        raise ValueError(f"scene0 palette baseline changed at index {PALETTE_INDEX}: 0x{before:04X}")
    edited["palette"]["colors"][PALETTE_INDEX] = PALETTE_AFTER

    edited["objects"]["records"].append(
        {
            "id": "m110a_shotgun_0000",
            "type_id": 69,
            "status_flags": 0x7800,
            "stride": 6,
            "x": 690,
            "y": 558,
            "param": None,
        }
    )
    edited["world"]["records"].append(
        {
            "id": "m100a_wall_0000",
            "type": 9,
            "rect": [668, 540, 676, 580],
        }
    )
    return edited


def build(canonical: bytes, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")

    base_source = export_scene_source_v2(canonical, SCENE_INDEX)
    edited_source = edit_scene_source(base_source)
    scene_rom, scene_source_report = compile_source_v2(canonical, edited_source)
    scene_build = scene_source_report["build"]
    scene_sha1 = hashlib.sha1(scene_rom).hexdigest()
    scene_checksum = f"0x{int.from_bytes(scene_rom[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}"
    if scene_sha1 != EXPECTED_SCENE_V2_SHA1 or scene_checksum != EXPECTED_SCENE_V2_CHECKSUM:
        raise ValueError(f"M1.1A scene-v2 fingerprint changed: {scene_sha1} / {scene_checksum}")

    palette_report = scene_build["palette"]
    if palette_report is None:
        raise ValueError("M1.1A palette operation missing")
    if palette_report["changed_color_indices"] != [PALETTE_INDEX]:
        raise ValueError("unexpected palette edit set")
    if int(palette_report["new_pointer"]) != EXPECTED_PALETTE_POINTER:
        raise ValueError("M1.1A palette allocation moved")

    allocations = sorted(scene_build["allocations"], key=lambda row: int(row["address"]))
    for left, right in zip(allocations, allocations[1:]):
        if int(left["address"]) + int(left["size"]) > int(right["address"]):
            raise ValueError(f"M1.1A allocation overlap: {left} / {right}")

    player_rom, player_report = build_player(canonical, contract)
    player_sha1 = hashlib.sha1(player_rom).hexdigest()
    if player_sha1 != FROZEN_M09D_SHA1:
        raise ValueError(f"frozen M09D parent changed: {player_sha1}")

    output, compose_report = compose(canonical, player_rom, scene_rom)
    output_sha1 = hashlib.sha1(output).hexdigest()
    output_checksum = f"0x{int.from_bytes(output[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}"
    if output_sha1 != EXPECTED_OUTPUT_SHA1 or output_checksum != EXPECTED_OUTPUT_CHECKSUM:
        raise ValueError(f"M1.1A integrated fingerprint changed: {output_sha1} / {output_checksum}")

    output_bank_hashes = [hashlib.sha1(output[address:address+0x8000]).hexdigest() for address in BANKS]
    frozen_bank_hashes = list(player_report["phase_bank_sha1"])
    assertions = {
        **compose_report["assertions"],
        "scene_source_v2_used": scene_source_report["schema"] == "truerecall.scene_source_build.v2",
        "single_transaction_palette_present": palette_report["changed_color_indices"] == [PALETTE_INDEX],
        "palette_outside_player_line": PALETTE_INDEX not in PLAYER_PALETTE_RANGE,
        "allocation_ledger_nonoverlap": all(
            int(left["address"]) + int(left["size"]) <= int(right["address"])
            for left, right in zip(allocations, allocations[1:])
        ),
        "frozen_player_parent_exact": player_sha1 == FROZEN_M09D_SHA1,
        "frozen_player_phase_banks_preserved": output_bank_hashes == frozen_bank_hashes,
        "deterministic_scene_v2_fingerprint": scene_sha1 == EXPECTED_SCENE_V2_SHA1 and scene_checksum == EXPECTED_SCENE_V2_CHECKSUM,
        "deterministic_integrated_fingerprint": output_sha1 == EXPECTED_OUTPUT_SHA1 and output_checksum == EXPECTED_OUTPUT_CHECKSUM,
    }
    if not all(assertions.values()):
        failed = [key for key, value in assertions.items() if not value]
        raise ValueError(f"M1.1A assertions failed: {failed}")

    report = {
        "schema": "truerecall.m110a.palette_vertical_slice.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "palette_edit": {
            "index": PALETTE_INDEX,
            "before": PALETTE_BEFORE,
            "after": PALETTE_AFTER,
            "player_palette_range": [32, 47],
            "new_pointer": palette_report["new_pointer"],
        },
        "scene_source_build": scene_source_report,
        "scene_parent_sha1": scene_sha1,
        "scene_parent_checksum": scene_checksum,
        "player_parent_sha1": player_sha1,
        "compose": compose_report,
        "output_sha1": output_sha1,
        "output_size": len(output),
        "genesis_checksum": output_checksum,
        "phase_bank_sha1": output_bank_hashes,
        "assertions": assertions,
        "runtime_status": "NOT_YET_PROVEN",
    }
    return output, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    canonical = args.rom.read_bytes()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    output, report = build(canonical, contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
