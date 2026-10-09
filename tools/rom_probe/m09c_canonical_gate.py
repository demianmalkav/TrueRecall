#!/usr/bin/env python3
"""Run the complete canonical M09C static gate against the exact retail ROM.

This orchestration layer intentionally does not implement new reverse-engineering
logic. It serializes the two already-defined canonical probes, validates their
JSON contracts, and emits one PASS checkpoint only when both gates succeed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
NATIVE_SCHEMA = "truerecall.m09c.native_sequence_seam.v1"
VISUAL_SCHEMA = "truerecall.m09c.visual_avatar_roundtrip.v1"
GATE_SCHEMA = "truerecall.m09c.canonical_gate.v1"
EXPECTED_ARCH191 = 0x0E51FE
EXPECTED_VISUAL = 0x0F0000


def verify_rom(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise ValueError(f"wrong ROM size: {len(raw)}")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise ValueError(f"wrong base ROM SHA-1: {digest}")
    return {"size": len(raw), "sha1": digest}


def run_probe(script: Path, rom: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(script), str(rom), "--json", str(output)],
        check=True,
    )
    if not output.is_file():
        raise RuntimeError(f"probe did not create {output}")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def validate_reports(native: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    if native.get("schema") != NATIVE_SCHEMA:
        raise ValueError(f"unexpected native schema: {native.get('schema')}")
    if visual.get("schema") != VISUAL_SCHEMA:
        raise ValueError(f"unexpected visual schema: {visual.get('schema')}")
    if native.get("base_sha1") != EXPECTED_SHA1 or visual.get("base_sha1") != EXPECTED_SHA1:
        raise ValueError("probe report base SHA-1 mismatch")

    descriptors = native.get("descriptors", {})
    arch = descriptors.get("archetype191", {}).get("address")
    runtime_visual = descriptors.get("runtime_visual_avatar", {}).get("address")
    if arch != EXPECTED_ARCH191:
        raise ValueError(f"archetype-191 descriptor changed: {arch!r}")
    if runtime_visual != EXPECTED_VISUAL:
        raise ValueError(f"runtime visual descriptor changed: {runtime_visual!r}")

    fddc = native.get("fddc", {})
    global_callers = fddc.get("global_callers", [])
    if not global_callers:
        raise ValueError("canonical FDDC caller set is empty")

    families = native.get("families", {})
    maniac = families.get("maniac_jllbfr")
    if not isinstance(maniac, dict):
        raise ValueError("missing canonical JLLBFR family")
    if maniac.get("base") != 0x00F2:
        raise ValueError("JLLBFR family base changed")
    if maniac.get("all_runtime_visual_valid") is not True:
        raise ValueError("JLLBFR does not resolve completely on runtime visual descriptor")

    if visual.get("runtime_visual_descriptor") != EXPECTED_VISUAL:
        raise ValueError("visual round-trip used the wrong descriptor")
    if visual.get("comparison_archetype191_descriptor") != EXPECTED_ARCH191:
        raise ValueError("visual comparison descriptor changed")
    if visual.get("facing_family_base") != 0x00F2:
        raise ValueError("visual round-trip did not use the JLLBFR family")

    frame_count = visual.get("frame_count")
    compiled = visual.get("compiled_frames")
    if not isinstance(frame_count, int) or frame_count <= 0:
        raise ValueError(f"invalid visual frame count: {frame_count!r}")
    if not isinstance(compiled, list) or len(compiled) != frame_count:
        raise ValueError("compiled frame count mismatch")
    if not all(row.get("matches_retail_pixels") is True for row in compiled):
        raise ValueError("canonical visual round-trip is not pixel exact")

    metadata = visual.get("compiler_metadata", {})
    if metadata.get("frame_count") != frame_count:
        raise ValueError("compiler metadata frame count mismatch")

    unique_selectors = visual.get("unique_selectors", [])
    if len(unique_selectors) != frame_count:
        raise ValueError("unique selector count does not match compiled frames")

    return {
        "native": {
            "fddc_global_callers": len(global_callers),
            "runtime_visual_record_count": native.get("resolved_record_counts", {}).get("runtime_visual"),
            "archetype191_record_count": native.get("resolved_record_counts", {}).get("archetype191"),
            "runtime_visual_ff_candidate_runs": len(native.get("runtime_visual_64k_ff_candidates", [])),
            "jllbfr_runtime_visual_valid": True,
        },
        "visual": {
            "frame_count": frame_count,
            "unique_selectors": unique_selectors,
            "chunk_bank_bytes": visual.get("chunk_bank_bytes"),
            "chunk_bank_sha1": visual.get("chunk_bank_sha1"),
            "global_unique_chunks": metadata.get("global_unique_chunks"),
            "max_frame_working_set": metadata.get("max_frame_working_set"),
            "max_scanline_pieces": metadata.get("max_scanline_pieces"),
            "max_scanline_pixels": metadata.get("max_scanline_pixels"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("extracted_metadata"),
        help="directory for canonical JSON evidence",
    )
    args = parser.parse_args()

    rom_identity = verify_rom(args.rom)
    here = Path(__file__).resolve().parent
    native_script = here / "m09c_native_sequence_seam_probe.py"
    visual_script = here / "m09c_visual_avatar_roundtrip_probe.py"

    native_json = args.output_dir / "m09c_native_sequence_seam.json"
    visual_json = args.output_dir / "m09c_visual_avatar_roundtrip.json"
    gate_json = args.output_dir / "m09c_canonical_gate.json"

    # Ordering is intentional: do not attempt the more expensive pixel/compiler
    # round-trip until descriptor/family reconciliation has completed cleanly.
    run_probe(native_script, args.rom, native_json)
    native = load_json(native_json)
    if native.get("schema") != NATIVE_SCHEMA:
        raise ValueError("native seam probe failed schema gate")

    run_probe(visual_script, args.rom, visual_json)
    visual = load_json(visual_json)
    summary = validate_reports(native, visual)

    result = {
        "schema": GATE_SCHEMA,
        "status": "PASS",
        "base_rom": rom_identity,
        "native_report": str(native_json),
        "visual_report": str(visual_json),
        "summary": summary,
        "promotion": {
            "descriptor_family_reconciliation": "canonical_static_pass",
            "visual_avatar_roundtrip": "canonical_pixel_exact_pass",
            "native_authored_sequence_runtime": "NOT_YET_PROVEN",
        },
        "next": (
            "Select one non-overlapping authored selector/record seam from the canonical "
            "native report, preserve object+0x2C == 0x0F0000, implement one minimal "
            "native progression proof, then run deterministic BlastEm regression."
        ),
    }
    gate_json.parent.mkdir(parents=True, exist_ok=True)
    gate_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
