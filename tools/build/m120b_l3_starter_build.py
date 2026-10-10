#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
EXPECTED_SCENE_SHA1 = "e4da8446303f96be04dadc0db8f3edd565f9b5c1"
EXPECTED_OUTPUT_SHA1 = "f0d232b3f6e181ccb9bb06cf07f475a3e7b70837"
EXPECTED_OUTPUT_CHECKSUM = "0xC4DC"
CHECKSUM_OFFSET = 0x018E


def build(canonical: bytes, contract: dict[str, Any], overlay: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(canonical).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")
    if overlay.get("id") != "m120b_l3_urban_subway_starter":
        raise ValueError("wrong M120B overlay")

    scene_rom, overlay_report = compile_overlay(canonical, overlay)
    scene_sha1 = hashlib.sha1(scene_rom).hexdigest()
    if scene_sha1 != EXPECTED_SCENE_SHA1:
        raise ValueError(f"M120B scene fingerprint changed: {scene_sha1}")

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
        "starter_candidate_fingerprint_exact": output_sha1 == EXPECTED_OUTPUT_SHA1 and checksum == EXPECTED_OUTPUT_CHECKSUM,
    }
    if not all(assertions.values()):
        raise ValueError([name for name, passed in assertions.items() if not passed])

    report = {
        "schema": "truerecall.m120b.l3_starter_build.v1",
        "status": "PROTOTYPE_NOT_ART_FREEZE",
        "base_sha1": BASE_SHA1,
        "overlay_id": overlay_report["overlay_id"],
        "scene_parent_sha1": scene_sha1,
        "player_parent_sha1": player_sha1,
        "output_sha1": output_sha1,
        "genesis_checksum": checksum,
        "phase_bank_sha1": phase_hashes,
        "assertions": assertions,
        "runtime_status": "CONFIRMED_STARTER_REGRESSION",
    }
    return output, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("overlay", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    out, report = build(
        args.rom.read_bytes(),
        json.loads(args.contract.read_text(encoding="utf-8")),
        json.loads(args.overlay.read_text(encoding="utf-8")),
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
