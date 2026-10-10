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
from m110a_palette_vertical_slice import edit_scene_source as edit_scene_source_v2
from m111c_graphics_vertical_slice import (
    AUTHORED_TILE_BYTES,
    EXPECTED_OUTPUT_SHA1 as CLOSED_M111C_SHA1,
    EXPECTED_OUTPUT_CHECKSUM as CLOSED_M111C_CHECKSUM,
    RETAIL_TILE_SHA256,
    TILE_INDEX,
)
from scene_compiler import BASE_SHA1
from scene_compiler_v3 import compile_source_v3
from scene_source_v3 import SCHEMA_V3, downgrade_v3_source, export_scene_source_v3
from scene_graphics import TILE_BYTES

SCENE_INDEX = 0
FROZEN_M09D_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
CHECKSUM_OFFSET = 0x018E


def edit_scene_source_v3(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("schema") != SCHEMA_V3 or int(source.get("scene_index", -1)) != SCENE_INDEX:
        raise ValueError("M1.1C vertical slice requires scene0 scene_source.v3")

    edited_v2 = edit_scene_source_v2(downgrade_v3_source(source))
    edited = deepcopy(edited_v2)
    edited["schema"] = SCHEMA_V3
    edited["primary_graphics"] = deepcopy(source["primary_graphics"])

    payload = bytearray.fromhex(edited["primary_graphics"]["tile_bytes_hex"])
    start = TILE_INDEX * TILE_BYTES
    end = start + TILE_BYTES
    retail = bytes(payload[start:end])
    if hashlib.sha256(retail).hexdigest() != RETAIL_TILE_SHA256:
        raise ValueError("closed retail tile2 identity changed")
    payload[start:end] = AUTHORED_TILE_BYTES
    edited["primary_graphics"]["tile_bytes_hex"] = bytes(payload).hex()
    return edited


def build(canonical: bytes, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")

    base_source = export_scene_source_v3(canonical, SCENE_INDEX)
    edited_source = edit_scene_source_v3(base_source)
    scene_rom, source_report = compile_source_v3(canonical, edited_source)
    if source_report["noop"]:
        raise ValueError("M1.1C authored scene unexpectedly compiled as no-op")
    scene_build = source_report["build"]
    graphics = scene_build["primary_graphics"]
    palette = scene_build["scene_v2_stage"]["palette"]
    if graphics is None or graphics["changed_tile_indices"] != [TILE_INDEX]:
        raise ValueError("M1.1C graphics edit set changed")
    if palette is None or palette["changed_color_indices"] != [8]:
        raise ValueError("M1.1C palette edit set changed")

    allocations = list(scene_build["allocations"])
    for left, right in zip(allocations, allocations[1:]):
        if int(left["address"]) + int(left["size"]) > int(right["address"]):
            raise ValueError(f"M1.1C allocation overlap: {left} / {right}")

    player_rom, player_report = build_player(canonical, contract)
    player_sha1 = hashlib.sha1(player_rom).hexdigest()
    if player_sha1 != FROZEN_M09D_SHA1:
        raise ValueError(f"frozen M09D parent changed: {player_sha1}")

    output, compose_report = compose(canonical, player_rom, scene_rom)
    output_sha1 = hashlib.sha1(output).hexdigest()
    output_checksum = f"0x{int.from_bytes(output[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}"
    if output_sha1 != CLOSED_M111C_SHA1 or output_checksum != CLOSED_M111C_CHECKSUM:
        raise ValueError(
            f"M1.1C does not reproduce closed M1.1B candidate: {output_sha1} / {output_checksum}"
        )

    output_bank_hashes = [hashlib.sha1(output[address:address+0x8000]).hexdigest() for address in BANKS]
    frozen_bank_hashes = list(player_report["phase_bank_sha1"])
    assertions = {
        **compose_report["assertions"],
        "scene_source_v3_used": source_report["schema"] == "truerecall.scene_source_build.v3",
        "single_transaction_has_palette": palette["changed_color_indices"] == [8],
        "single_transaction_has_primary_graphics": graphics["changed_tile_indices"] == [TILE_INDEX],
        "single_transaction_allocation_nonoverlap": all(
            int(left["address"]) + int(left["size"]) <= int(right["address"])
            for left, right in zip(allocations, allocations[1:])
        ),
        "frozen_player_parent_exact": player_sha1 == FROZEN_M09D_SHA1,
        "frozen_player_phase_banks_preserved": output_bank_hashes == frozen_bank_hashes,
        "closed_m111c_candidate_reproduced_exact": output_sha1 == CLOSED_M111C_SHA1 and output_checksum == CLOSED_M111C_CHECKSUM,
    }
    if not all(assertions.values()):
        failed = [key for key, value in assertions.items() if not value]
        raise ValueError(f"M1.1C vertical-slice assertions failed: {failed}")

    report = {
        "schema": "truerecall.m112a.scene_source_v3_vertical_slice.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "scene_source_build": source_report,
        "scene_parent_sha1": hashlib.sha1(scene_rom).hexdigest(),
        "scene_parent_checksum": f"0x{int.from_bytes(scene_rom[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}",
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
