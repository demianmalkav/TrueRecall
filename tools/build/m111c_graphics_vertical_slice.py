#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from m09c_native_phase_pixel_sequence import BANKS
from m100a_vertical_slice_baseline import compose
from m110a_palette_vertical_slice import build as build_m110a
from scene_compiler import BASE_SHA1
from scene_graphics import TILE_BYTES, compile_primary_graphics, export_primary_graphics

SCENE_INDEX = 0
TILE_INDEX = 2
GFX_ALLOCATION_BASE = 0x304000
RETAIL_TILE_SHA256 = "e0e77a507412b120f6ede61f62295b1a7b2ff19d3dcc8f7253e51663470c888e"
AUTHORED_TILE_BYTES = bytes.fromhex(
    "e000000e"
    "0e0000e0"
    "00e00e00"
    "000ee000"
    "000ee000"
    "00e00e00"
    "0e0000e0"
    "e000000e"
)
EXPECTED_M110A_SHA1 = "270e1d633db7883c9170bb1e4eb367abdf97a2bd"
EXPECTED_M110A_CHECKSUM = "0x6B9E"
EXPECTED_GRAPHICS_SCENE_SHA1 = "a26f74937233e155e025bcd45a220660c75e110f"
EXPECTED_GRAPHICS_SCENE_CHECKSUM = "0xED13"
EXPECTED_OUTPUT_SHA1 = "b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0"
EXPECTED_OUTPUT_CHECKSUM = "0xFAD7"
CHECKSUM_OFFSET = 0x018E


def checksum_word(raw: bytes) -> str:
    return f"0x{int.from_bytes(raw[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2], 'big'):04X}"


def align(value: int, alignment: int = 0x10) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def edit_primary_source(source: dict[str, Any]) -> dict[str, Any]:
    if source.get("schema") != "truerecall.scene_primary_graphics.v1":
        raise ValueError("M1.1B requires scene_primary_graphics.v1")
    if int(source.get("scene_index", -1)) != SCENE_INDEX:
        raise ValueError("M1.1B is pinned to scene 0")
    tiles = bytearray.fromhex(source["tile_bytes_hex"])
    if len(tiles) != int(source["tile_count"]) * TILE_BYTES:
        raise ValueError("primary tile payload length mismatch")
    start = TILE_INDEX * TILE_BYTES
    end = start + TILE_BYTES
    before = bytes(tiles[start:end])
    before_sha256 = hashlib.sha256(before).hexdigest()
    if before_sha256 != RETAIL_TILE_SHA256:
        raise ValueError(f"scene0 retail tile {TILE_INDEX} fingerprint changed: {before_sha256}")
    tiles[start:end] = AUTHORED_TILE_BYTES
    edited = deepcopy(source)
    edited["tile_bytes_hex"] = bytes(tiles).hex()
    return edited


def build(canonical: bytes, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")

    m110a_rom, m110a_report = build_m110a(canonical, contract)
    m110a_sha1 = hashlib.sha1(m110a_rom).hexdigest()
    m110a_checksum = checksum_word(m110a_rom)
    if m110a_sha1 != EXPECTED_M110A_SHA1 or m110a_checksum != EXPECTED_M110A_CHECKSUM:
        raise ValueError(f"closed M110A baseline changed: {m110a_sha1} / {m110a_checksum}")

    base_source = export_primary_graphics(canonical, SCENE_INDEX)
    edited_source = edit_primary_source(base_source)
    graphics_rom, graphics_report = compile_primary_graphics(
        canonical,
        edited_source,
        allocation_base=GFX_ALLOCATION_BASE,
    )
    graphics_sha1 = hashlib.sha1(graphics_rom).hexdigest()
    graphics_checksum = checksum_word(graphics_rom)
    if graphics_sha1 != EXPECTED_GRAPHICS_SCENE_SHA1 or graphics_checksum != EXPECTED_GRAPHICS_SCENE_CHECKSUM:
        raise ValueError(f"M1.1B graphics parent changed: {graphics_sha1} / {graphics_checksum}")
    if graphics_report["changed_tile_indices"] != [TILE_INDEX]:
        raise ValueError(f"unexpected authored tile set: {graphics_report['changed_tile_indices']}")
    if int(graphics_report["new_descriptor"]) != GFX_ALLOCATION_BASE:
        raise ValueError("graphics descriptor allocation moved")
    if bytes.fromhex(edited_source["tile_bytes_hex"])[TILE_INDEX*TILE_BYTES:(TILE_INDEX+1)*TILE_BYTES] != AUTHORED_TILE_BYTES:
        raise AssertionError("authored tile payload mismatch")

    scene_allocations = [dict(row) for row in m110a_report["scene_source_build"]["build"]["allocations"]]
    scene_end = max(int(row["address"]) + int(row["size"]) for row in scene_allocations)
    minimum_graphics_base = align(scene_end)
    if GFX_ALLOCATION_BASE < minimum_graphics_base:
        raise ValueError(
            f"graphics allocation overlaps M110A scene ledger: 0x{GFX_ALLOCATION_BASE:06X} < 0x{minimum_graphics_base:06X}"
        )
    combined_allocations = scene_allocations + [dict(row) for row in graphics_report["allocations"]]
    ordered = sorted(combined_allocations, key=lambda row: int(row["address"]))
    allocation_nonoverlap = all(
        int(left["address"]) + int(left["size"]) <= int(right["address"])
        for left, right in zip(ordered, ordered[1:])
    )
    if not allocation_nonoverlap:
        raise ValueError("M1.1B combined allocation ledger overlaps")

    output, compose_report = compose(canonical, m110a_rom, graphics_rom)
    output_sha1 = hashlib.sha1(output).hexdigest()
    output_checksum = checksum_word(output)
    if output_sha1 != EXPECTED_OUTPUT_SHA1 or output_checksum != EXPECTED_OUTPUT_CHECKSUM:
        raise ValueError(f"M1.1B integrated fingerprint changed: {output_sha1} / {output_checksum}")

    m110a_phase_hashes = list(m110a_report["phase_bank_sha1"])
    output_phase_hashes = [hashlib.sha1(output[address:address + 0x8000]).hexdigest() for address in BANKS]
    palette_pointer = int(m110a_report["palette_edit"]["new_pointer"])
    palette_exact = output[palette_pointer:palette_pointer + 128] == m110a_rom[palette_pointer:palette_pointer + 128]

    assertions = {
        **compose_report["assertions"],
        "closed_m110a_parent_exact": m110a_sha1 == EXPECTED_M110A_SHA1,
        "single_authored_primary_tile": graphics_report["changed_tile_indices"] == [TILE_INDEX],
        "authored_tile_payload_exact": bytes.fromhex(edited_source["tile_bytes_hex"])[TILE_INDEX*TILE_BYTES:(TILE_INDEX+1)*TILE_BYTES] == AUTHORED_TILE_BYTES,
        "graphics_allocation_after_m110a_ledger": GFX_ALLOCATION_BASE >= minimum_graphics_base,
        "combined_allocation_ledger_nonoverlap": allocation_nonoverlap,
        "frozen_player_phase_banks_preserved": output_phase_hashes == m110a_phase_hashes,
        "m110a_palette_bytes_preserved": palette_exact,
        "deterministic_graphics_parent": graphics_sha1 == EXPECTED_GRAPHICS_SCENE_SHA1 and graphics_checksum == EXPECTED_GRAPHICS_SCENE_CHECKSUM,
        "deterministic_integrated_candidate": output_sha1 == EXPECTED_OUTPUT_SHA1 and output_checksum == EXPECTED_OUTPUT_CHECKSUM,
    }
    if not all(assertions.values()):
        failed = [key for key, value in assertions.items() if not value]
        raise ValueError(f"M1.1B integration assertions failed: {failed}")

    report = {
        "schema": "truerecall.m111c.graphics_vertical_slice.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "m110a_parent_sha1": m110a_sha1,
        "m110a_parent_checksum": m110a_checksum,
        "graphics_edit": {
            "tile_index": TILE_INDEX,
            "retail_tile_sha256": RETAIL_TILE_SHA256,
            "authored_tile_hex": AUTHORED_TILE_BYTES.hex(),
            "allocation_base": GFX_ALLOCATION_BASE,
            "new_descriptor": graphics_report["new_descriptor"],
            "new_primary_lz": graphics_report["new_primary_lz"],
        },
        "graphics_parent_sha1": graphics_sha1,
        "graphics_parent_checksum": graphics_checksum,
        "graphics_build": graphics_report,
        "combined_allocations": ordered,
        "compose": compose_report,
        "phase_bank_sha1": output_phase_hashes,
        "output_sha1": output_sha1,
        "output_size": len(output),
        "genesis_checksum": output_checksum,
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
