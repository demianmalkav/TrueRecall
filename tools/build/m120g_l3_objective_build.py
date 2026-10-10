#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from m09c_native_phase_pixel_sequence import BANKS
from m09d_quaid_sprint_build import build as build_player
from m100a_vertical_slice_baseline import compose
from scene_compiler import BASE_SHA1
from scene_overlay import compile_overlay

FROZEN_M09D_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_SCENE_SHA1 = "cd43a4b53371e4d8329eaa328582ffd64262bddf"
EXPECTED_OUTPUT_SHA1 = "150373a312283f5c89e5fa00e99f19d7a83bff44"
EXPECTED_OUTPUT_CHECKSUM = "0xB7B0"
CHECKSUM_OFFSET = 0x018E


def compose_production_overlay(base_overlay: dict[str, Any], placement: dict[str, Any]) -> dict[str, Any]:
    if base_overlay.get("id") != "m120c_l3_three_zone_refinement":
        raise ValueError("M120G must derive from frozen M120C visual skeleton")
    if placement.get("schema") != "truerecall.m120g.objective_placement.v1":
        raise ValueError("wrong M120G placement schema")
    if not placement.get("replace_base_objects") or not placement.get("replace_base_world"):
        raise ValueError("M120G must explicitly retire M120C proof objects/world")
    out = copy.deepcopy(base_overlay)
    out["id"] = placement["id"]
    out["status"] = placement["status"]
    out["design_target"] = placement["design_intent"]
    out["objects"] = copy.deepcopy(placement["objects"])
    out["world"] = copy.deepcopy(placement["world"])
    return out


def build(canonical: bytes, contract: dict[str, Any], base_overlay: dict[str, Any], placement: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")
    overlay = compose_production_overlay(base_overlay, placement)
    scene_rom, overlay_report = compile_overlay(canonical, overlay)
    scene_sha1 = hashlib.sha1(scene_rom).hexdigest()
    if scene_sha1 != EXPECTED_SCENE_SHA1:
        raise ValueError(f"M120G scene fingerprint changed: {scene_sha1}")

    player_rom, player_report = build_player(canonical, contract)
    player_sha1 = hashlib.sha1(player_rom).hexdigest()
    if player_sha1 != FROZEN_M09D_SHA1:
        raise ValueError(f"frozen M09D parent changed: {player_sha1}")

    output, compose_report = compose(canonical, player_rom, scene_rom)
    output_sha1 = hashlib.sha1(output).hexdigest()
    checksum = f"0x{int.from_bytes(output[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2], 'big'):04X}"
    phase_hashes = [hashlib.sha1(output[address:address+0x8000]).hexdigest() for address in BANKS]
    assertions = {
        **compose_report["assertions"],
        "scene_fingerprint_exact": scene_sha1 == EXPECTED_SCENE_SHA1,
        "frozen_player_parent_exact": player_sha1 == FROZEN_M09D_SHA1,
        "frozen_player_phase_banks_preserved": phase_hashes == list(player_report["phase_bank_sha1"]),
        "production_candidate_fingerprint_exact": output_sha1 == EXPECTED_OUTPUT_SHA1 and checksum == EXPECTED_OUTPUT_CHECKSUM,
        "objective_pair_exact": [(o["type_id"], o["x"], o["y"], o["status_flags"], o["stride"]) for o in placement["objects"]] == [(60,724,558,"0x7800",6),(87,652,558,"0x7800",6)],
        "proof_world_retired": placement["world"] == [],
    }
    if not all(assertions.values()):
        raise ValueError([name for name, passed in assertions.items() if not passed])

    report = {
        "schema": "truerecall.m120g.l3_objective_build.v1",
        "status": placement["status"],
        "base_sha1": BASE_SHA1,
        "visual_base_overlay": base_overlay["id"],
        "placement_id": placement["id"],
        "scene_parent_sha1": scene_sha1,
        "player_parent_sha1": player_sha1,
        "output_sha1": output_sha1,
        "genesis_checksum": checksum,
        "phase_bank_sha1": phase_hashes,
        "overlay_report": overlay_report,
        "assertions": assertions,
        "runtime_status": "CONFIRMED_NATIVE_OBJECTIVE_AND_CLOSED_VISUAL_CONTRACTS",
    }
    return output, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("base_overlay", type=Path)
    ap.add_argument("placement", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    out, report = build(
        args.rom.read_bytes(),
        json.loads(args.contract.read_text(encoding="utf-8")),
        json.loads(args.base_overlay.read_text(encoding="utf-8")),
        json.loads(args.placement.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
