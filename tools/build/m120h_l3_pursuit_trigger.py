#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2] if len(HERE.parents) >= 3 else Path.cwd()
ROM_PROBE = ROOT / "tools" / "rom_probe"
if str(ROM_PROBE) not in sys.path:
    sys.path.insert(0, str(ROM_PROBE))

from m09c_native_phase_pixel_sequence import BANKS
from m120g_l3_objective_build import build as build_m120g
from vm_asm import assemble, parse_text
from vm_disasm import reachable
from vm_source_export import export_type_source

EXPECTED_M120G_SHA1 = "150373a312283f5c89e5fa00e99f19d7a83bff44"
EXPECTED_OUTPUT_SHA1 = "acfecb2fdb5cc6c55a5c89ae172dd58d8444e1e3"
EXPECTED_OUTPUT_CHECKSUM = "0xD0C0"
TYPE_POINTER_TABLE = 0x07953E
TYPE_SELECTOR_TABLE = 0x07A33C
SIGNAL_TYPE = 87
CHASE_TYPE = 24
RETAIL_SIGNAL_SCRIPT = 0x17F2A6
SCRIPT_ADDRESS = 0x308000
CHECKSUM_OFFSET = 0x018E
FC56_STORE = "  STORE_ABS_W_D2 0xFFFFFC56\n"
SPAWN_SOURCE = (
    "  MOVI_W_D2 0x0018\n"
    "  PUSH_D2_W\n"
    "  NATIVE SpawnLinkedObject\n"
    "  ADJ_NATIVE_STACK 0x0002\n"
)


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def author_type87_source(source: str) -> str:
    if source.count(FC56_STORE) != 1:
        raise ValueError("type87 FC56 clear must be unique")
    return source.replace(FC56_STORE, FC56_STORE + SPAWN_SOURCE)


def phase_bank_sha1(rom: bytes | bytearray) -> list[str]:
    return [hashlib.sha1(bytes(rom[address:address + 0x8000])).hexdigest() for address in BANKS]


def build(
    canonical: bytes,
    contract: dict[str, Any],
    base_overlay: dict[str, Any],
    placement: dict[str, Any],
) -> tuple[bytes, dict[str, Any]]:
    m120g, m120g_report = build_m120g(canonical, contract, base_overlay, placement)
    parent_sha1 = hashlib.sha1(m120g).hexdigest()
    if parent_sha1 != EXPECTED_M120G_SHA1:
        raise ValueError(f"wrong M120G parent: {parent_sha1}")
    if canonical[TYPE_SELECTOR_TABLE + SIGNAL_TYPE] != 1:
        raise ValueError("retail type87 is not VM-scripted")

    retail_pointer_off = TYPE_POINTER_TABLE + SIGNAL_TYPE * 4
    retail_pointer = int.from_bytes(canonical[retail_pointer_off:retail_pointer_off + 4], "big")
    if retail_pointer != RETAIL_SIGNAL_SCRIPT:
        raise ValueError(f"type87 retail pointer changed: 0x{retail_pointer:06X}")

    original_start, source = export_type_source(canonical, SIGNAL_TYPE)
    if original_start != RETAIL_SIGNAL_SCRIPT:
        raise ValueError(f"unexpected type87 source base: 0x{original_start:06X}")
    authored_source = author_type87_source(source)
    blob, _labels = assemble(parse_text(authored_source), SCRIPT_ADDRESS)
    if len(blob) != 334:
        raise ValueError(f"type87 authored byte size changed: {len(blob)}")
    if any(byte != 0xFF for byte in m120g[SCRIPT_ADDRESS:SCRIPT_ADDRESS + len(blob)]):
        raise ValueError("M120H relocation window is not blank in M120G parent")

    output = bytearray(m120g)
    output[SCRIPT_ADDRESS:SCRIPT_ADDRESS + len(blob)] = blob
    output[retail_pointer_off:retail_pointer_off + 4] = SCRIPT_ADDRESS.to_bytes(4, "big")
    output[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = genesis_checksum(output).to_bytes(2, "big")

    instructions, _calls, _branches = reachable(bytes(output), SCRIPT_ADDRESS, max_states=200000, max_stack=32)
    if len(instructions) != 89:
        raise ValueError(f"relocated type87 reachable shape changed: {len(instructions)}")

    changed_offsets = [index for index, (before, after) in enumerate(zip(m120g, output)) if before != after]
    allowed_offsets = (
        set(range(SCRIPT_ADDRESS, SCRIPT_ADDRESS + len(blob)))
        | set(range(retail_pointer_off, retail_pointer_off + 4))
        | set(range(CHECKSUM_OFFSET, CHECKSUM_OFFSET + 2))
    )
    patch_domain_contained = all(index in allowed_offsets for index in changed_offsets)

    output_sha1 = hashlib.sha1(output).hexdigest()
    checksum = f"0x{genesis_checksum(output):04X}"
    parent_phase_hashes = phase_bank_sha1(m120g)
    output_phase_hashes = phase_bank_sha1(output)
    assertions = {
        "m120g_parent_exact": parent_sha1 == EXPECTED_M120G_SHA1,
        "retail_type87_pointer_exact": retail_pointer == RETAIL_SIGNAL_SCRIPT,
        "relocation_window_was_ff": True,
        "type87_pointer_relocated": int.from_bytes(output[retail_pointer_off:retail_pointer_off + 4], "big") == SCRIPT_ADDRESS,
        "type87_remains_scripted": output[TYPE_SELECTOR_TABLE + SIGNAL_TYPE] == 1,
        "spawn_sequence_in_source_once": authored_source.count("NATIVE SpawnLinkedObject") == source.count("NATIVE SpawnLinkedObject") + 1,
        "chase_type_exact": f"MOVI_W_D2 0x{CHASE_TYPE:04X}" in authored_source,
        "reachable_instruction_count_exact": len(instructions) == 89,
        "frozen_player_phase_banks_preserved": output_phase_hashes == parent_phase_hashes,
        "patch_domain_contained": patch_domain_contained,
        "candidate_fingerprint_exact": output_sha1 == EXPECTED_OUTPUT_SHA1 and checksum == EXPECTED_OUTPUT_CHECKSUM,
    }
    if not all(assertions.values()):
        raise ValueError([name for name, passed in assertions.items() if not passed])

    report = {
        "schema": "truerecall.m120h.l3_pursuit_trigger_build.v1",
        "status": "RUNTIME_CONFIRMED_EXTERNALLY",
        "base_m120g_sha1": parent_sha1,
        "candidate_sha1": output_sha1,
        "genesis_checksum": checksum,
        "signal_type": SIGNAL_TYPE,
        "chase_type": CHASE_TYPE,
        "retail_type87_script": f"0x{RETAIL_SIGNAL_SCRIPT:06X}",
        "relocated_type87_script": f"0x{SCRIPT_ADDRESS:06X}",
        "relocated_script_bytes": len(blob),
        "reachable_instruction_count": len(instructions),
        "trigger_semantics": "after type87 clears FC56 bit0 on successful lever branch, spawn one linked type24 hostile",
        "m120g_report": {
            "output_sha1": m120g_report["output_sha1"],
            "genesis_checksum": m120g_report["genesis_checksum"],
        },
        "changed_byte_count": len(changed_offsets),
        "phase_bank_sha1": output_phase_hashes,
        "assertions": assertions,
    }
    return bytes(output), report


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
