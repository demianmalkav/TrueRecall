#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from m09c_native_phase_pixel_sequence import (
    BANKS,
    CHECKSUM_OFFSET,
    build as build_m09c,
    genesis_checksum,
)
from m09d_mapping_constrained_sprite_compiler import compile_banks
from m09d_quaid_sprint_source import AUTHORED_DIRECTIONS, PHASE_DELTAS, render_frame

EXPECTED_CANONICAL_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
EXPECTED_M09C_PARENT_SHA1 = "3256f9dcbc6376624716e3508f41c0439e17cef6"
EXPECTED_M09D_CANDIDATE_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_M09D_CANDIDATE_CHECKSUM = "0x266C"


def source_frames(contract: dict[str, Any]):
    return {
        direction: [
            render_frame(contract, direction, phase_index)
            for phase_index in range(len(PHASE_DELTAS))
        ]
        for direction in AUTHORED_DIRECTIONS
    }


def source_fingerprint(frames) -> tuple[str, list[dict[str, Any]]]:
    h = hashlib.sha1()
    rows = []
    for direction in AUTHORED_DIRECTIONS:
        for phase_delta, img in zip(PHASE_DELTAS, frames[direction]):
            pixels = img.tobytes()
            digest = hashlib.sha1(pixels).hexdigest()
            h.update(direction.encode("ascii"))
            h.update(phase_delta.to_bytes(2, "big"))
            h.update(img.width.to_bytes(2, "big"))
            h.update(img.height.to_bytes(2, "big"))
            h.update(pixels)
            rows.append(
                {
                    "direction": direction,
                    "phase_delta": phase_delta,
                    "canvas": [img.width, img.height],
                    "indexed_pixels_sha1": digest,
                }
            )
    return h.hexdigest(), rows


def overlay_phase_banks(parent: bytes, banks: list[bytes]) -> tuple[bytes, int]:
    if len(parent) != 0x400000:
        raise ValueError("M09D parent must be a 4 MiB M09C build")
    if len(banks) != len(BANKS):
        raise ValueError(f"expected {len(BANKS)} phase banks")
    out = bytearray(parent)
    for address, bank in zip(BANKS, banks):
        if len(bank) != 0x8000:
            raise ValueError("each M09D phase bank must be exactly 0x8000 bytes")
        out[address : address + len(bank)] = bank
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = checksum.to_bytes(2, "big")
    return bytes(out), checksum


def build(raw: bytes, contract: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    base_sha1 = hashlib.sha1(raw).hexdigest()
    if base_sha1 != EXPECTED_CANONICAL_SHA1:
        raise ValueError(f"wrong canonical base SHA-1: {base_sha1}")

    parent, parent_report = build_m09c(raw)
    parent_sha1 = hashlib.sha1(parent).hexdigest()
    if parent_sha1 != EXPECTED_M09C_PARENT_SHA1:
        raise ValueError(f"M09C parent fingerprint changed: {parent_sha1}")

    frames = source_frames(contract)
    art_sha1, frame_rows = source_fingerprint(frames)
    banks, compile_report = compile_banks(contract, frames)
    if not all(compile_report["assertions"].values()):
        raise ValueError("M09D mapping-constrained compile assertions failed")

    out, checksum = overlay_phase_banks(parent, banks)
    output_sha1 = hashlib.sha1(out).hexdigest()
    report = {
        "schema": "truerecall.m09d.quaid_sprint_build.v2",
        "base_sha1": base_sha1,
        "parent_schema": parent_report["schema"],
        "parent_sha1": parent_sha1,
        "output_sha1": output_sha1,
        "output_size": len(out),
        "genesis_checksum": f"0x{checksum:04X}",
        "source_art_status": "production_candidate_v11",
        "source_art_fingerprint": art_sha1,
        "source_frames": frame_rows,
        "phase_bank_addresses": [f"0x{x:06X}" for x in BANKS],
        "phase_bank_sha1": [hashlib.sha1(bank).hexdigest() for bank in banks],
        "compile_assertions": compile_report["assertions"],
        "compile_phase_budgets": [
            {
                "phase_delta": phase["phase_delta"],
                "used_chunk_slots": phase["used_chunk_slots"],
                "used_chunk_bytes": phase["used_chunk_bytes"],
                "max_frame_piece_count": phase["max_frame_piece_count"],
            }
            for phase in compile_report["phases"]
        ],
        "integration_policy": (
            "M09C parent is rebuilt canonically; only six 0x8000 phase banks are replaced; "
            "descriptor, native phase trampolines, mapping geometry and player control remain unchanged"
        ),
        "expected_candidate_fingerprint": {
            "sha1": EXPECTED_M09D_CANDIDATE_SHA1,
            "checksum": EXPECTED_M09D_CANDIDATE_CHECKSUM,
            "matches": output_sha1 == EXPECTED_M09D_CANDIDATE_SHA1
            and f"0x{checksum:04X}" == EXPECTED_M09D_CANDIDATE_CHECKSUM,
        },
    }
    return out, report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("contract", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    out, report = build(args.rom.read_bytes(), contract)
    if not report["expected_candidate_fingerprint"]["matches"]:
        raise SystemExit(
            "M09D deterministic production-candidate fingerprint changed: "
            f"{report['output_sha1']} / {report['genesis_checksum']}"
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
