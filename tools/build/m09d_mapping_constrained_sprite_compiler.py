#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image

from sprite_asset_compiler import encode_chunk

CHUNK_BYTES = 128
BANK_CHUNKS = 256
BANK_BYTES = CHUNK_BYTES * BANK_CHUNKS
AUTHORED_DIRECTIONS = ("N", "NE", "E", "SE", "S")


def _hex_int(value: str | int) -> int:
    return int(value, 0) if isinstance(value, str) else int(value)


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema") != "truerecall.m09d.quaid_sprint_contract.v1":
        raise ValueError("wrong M09D contract schema")
    if contract.get("authored_direction_families") != list(AUTHORED_DIRECTIONS):
        raise ValueError("unexpected authored direction families")
    phases = contract.get("phase_deltas")
    if phases != [0, 2, 4, 6, 8, 10]:
        raise ValueError(f"unexpected phase contract: {phases}")
    budget = contract["production_budget_v1"]
    if budget["transparent_palette_index"] != 0:
        raise ValueError("palette index 0 must remain transparent")
    lo, hi = contract["chunk_index_range"]
    if (_hex_int(lo), _hex_int(hi)) != (0x68, 0x7F):
        raise ValueError("unexpected chunk-slot range")


def compile_banks(
    contract: dict[str, Any],
    source_frames: dict[str, list[Image.Image]],
) -> tuple[list[bytes], dict[str, Any]]:
    """Compile 5 authored facings x 6 native phases into six raw 256-chunk banks.

    Mapping geometry and chunk-slot identities are taken verbatim from the M09D
    contract. SW/W/NW are intentionally not authored: retail H-flip aliases
    SE/E/NE mapping records.
    """
    validate_contract(contract)
    phase_deltas = list(contract["phase_deltas"])
    families = contract.get("families")
    records = contract.get("records")
    directions = contract.get("directions")
    if families is None and (records is None or directions is None):
        raise ValueError("contract must provide either families or records+directions")
    budget = contract["production_budget_v1"]

    for direction in AUTHORED_DIRECTIONS:
        frames = source_frames.get(direction)
        if frames is None or len(frames) != len(phase_deltas):
            raise ValueError(f"{direction} requires exactly {len(phase_deltas)} source frames")

    banks: list[bytes] = []
    phase_meta: list[dict[str, Any]] = []
    all_slot_hashes: dict[str, list[str]] = {}

    for phase_index, phase_delta in enumerate(phase_deltas):
        bank = bytearray(BANK_BYTES)
        assignments: dict[int, bytes] = {}
        frame_rows: list[dict[str, Any]] = []

        for direction in AUTHORED_DIRECTIONS:
            img = source_frames[direction][phase_index]
            if img.mode != "P":
                raise ValueError(f"{direction} phase {phase_delta}: image must be mode P")
            extrema = img.getextrema()
            if extrema and extrema[1] > 15:
                raise ValueError(f"{direction} phase {phase_delta}: palette index >15")

            if families is not None:
                family = families[direction]
                pattern = family["phase_record_pattern"]
                record_name = f"record_{pattern[phase_index]}"
                record = family[record_name]
                record_offset = record["offset"]
                clip_w, clip_h = map(int, record["clip"])
                pieces = [(int(x), int(y), _hex_int(slot)) for x, y, slot in record["pieces"]]
            else:
                record_offset = directions[direction]["record_offsets"][phase_index]
                record = records[record_offset]
                clip_w, clip_h = int(record["clip_width"]), int(record["clip_height"])
                pieces = [
                    (int(p["local_x"]), int(p["local_y"]), int(p["chunk_index"]))
                    for p in record["pieces"]
                ]
            if img.width < clip_w or img.height < clip_h:
                raise ValueError(
                    f"{direction} phase {phase_delta}: canvas {img.width}x{img.height} "
                    f"smaller than clip {clip_w}x{clip_h}"
                )

            slots: list[int] = []
            for local_x, local_y, slot in pieces:
                if not 0x68 <= slot <= 0x7F:
                    raise ValueError(f"slot 0x{slot:02X} outside M09D reserved range")
                chunk = encode_chunk(img, int(local_x), int(local_y))
                previous = assignments.get(slot)
                if previous is not None and previous != chunk:
                    raise ValueError(
                        f"phase {phase_delta}: slot 0x{slot:02X} receives conflicting pixels"
                    )
                assignments[slot] = chunk
                slots.append(slot)

            frame_rows.append(
                {
                    "direction": direction,
                    "phase_delta": phase_delta,
                    "record": record_offset,
                    "canvas": [img.width, img.height],
                    "clip": [clip_w, clip_h],
                    "piece_count": len(pieces),
                    "chunk_slots": [f"0x{x:02X}" for x in slots],
                }
            )

        if len(assignments) > int(budget["reserved_chunk_slots_per_phase"]):
            raise ValueError("phase exceeds reserved chunk-slot budget")
        for slot, chunk in assignments.items():
            start = slot * CHUNK_BYTES
            bank[start : start + CHUNK_BYTES] = chunk
            all_slot_hashes.setdefault(f"0x{slot:02X}", []).append(hashlib.sha1(chunk).hexdigest())

        bank_bytes = bytes(bank)
        banks.append(bank_bytes)
        phase_meta.append(
            {
                "phase_index": phase_index,
                "phase_delta": phase_delta,
                "used_chunk_slots": len(assignments),
                "used_chunk_bytes": len(assignments) * CHUNK_BYTES,
                "reserved_chunk_slots": int(budget["reserved_chunk_slots_per_phase"]),
                "reserved_chunk_bytes": int(budget["reserved_chunk_bytes_per_phase"]),
                "max_frame_piece_count": max(row["piece_count"] for row in frame_rows),
                "bank_sha1": hashlib.sha1(bank_bytes).hexdigest(),
                "frames": frame_rows,
            }
        )

    metadata = {
        "schema": "truerecall.m09d.mapping_constrained_compile.v1",
        "contract_schema": contract["schema"],
        "descriptor": contract["descriptor"],
        "phase_deltas": phase_deltas,
        "authored_direction_families": list(AUTHORED_DIRECTIONS),
        "mirrored_direction_families": contract["mirrored_direction_families"],
        "bank_bytes": BANK_BYTES,
        "chunk_bytes": CHUNK_BYTES,
        "chunk_slot_range": contract["chunk_index_range"],
        "phases": phase_meta,
        "assertions": {
            "mapping_geometry_preserved": True,
            "chunk_slot_identities_preserved": True,
            "transparent_index_zero_reserved": True,
            "palette_indices_within_0_15": True,
            "phase_slot_budget_respected": all(
                p["used_chunk_slots"] <= p["reserved_chunk_slots"] for p in phase_meta
            ),
            "frame_piece_budget_respected": all(
                p["max_frame_piece_count"] <= budget["max_retail_piece_count_per_frame"]
                for p in phase_meta
            ),
            "eight_runtime_facings_via_native_mirroring": True,
        },
        "slot_chunk_sha1_by_phase": all_slot_hashes,
    }
    return banks, metadata


def load_sources(manifest_path: Path, contract: dict[str, Any]) -> dict[str, list[Image.Image]]:
    spec = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    sources: dict[str, list[Image.Image]] = {}
    phases = contract["phase_deltas"]
    for direction in AUTHORED_DIRECTIONS:
        entries = spec.get("directions", {}).get(direction)
        if not isinstance(entries, list) or len(entries) != len(phases):
            raise ValueError(f"manifest direction {direction} must contain six images")
        images = []
        for expected_delta, entry in zip(phases, entries):
            if int(entry["phase_delta"]) != expected_delta:
                raise ValueError(f"{direction}: phase ordering mismatch")
            img = Image.open((base / entry["image"]).resolve())
            if img.mode != "P":
                raise ValueError(f"{direction} phase {expected_delta}: PNG must be indexed mode P")
            images.append(img.copy())
            img.close()
        sources[direction] = images
    return sources


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("contract", type=Path)
    ap.add_argument("source_manifest", type=Path)
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    sources = load_sources(args.source_manifest, contract)
    banks, metadata = compile_banks(contract, sources)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for i, bank in enumerate(banks):
        (args.out_dir / f"phase_{i}.bank.bin").write_bytes(bank)
    (args.out_dir / "compile.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
