#!/usr/bin/env python3
"""M09C static gate for the native player-animation integration seam.

The probe deliberately distinguishes the archetype-191 descriptor recovered from
the archetype table from the runtime-proven visual-avatar descriptor used by the
renderer. It maps player facing-family bases through the Beam direction table,
resolves the resulting selectors against both descriptors, locates callers of
the FDDC animation resolver and inventories conservative free runs inside the
visual descriptor's 64 KiB relative-address window.

Structural metadata only; no sprite pixels or copyrighted asset dumps are emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"

ARCHETYPE_TABLE = 0x079906
PLAYER_ARCHETYPE_ID = 191
ARCH191_DESCRIPTOR_EXPECTED = 0x0E51FE
RUNTIME_VISUAL_DESCRIPTOR = 0x0F0000
DIR_TABLE = 0x013F32
FDDC = 0x00FDDC

# Player-facing animation-family bases established by the player-control probes.
FAMILY_BASES = {
    "walk_pistol": 0x0002,
    "walk_shotgun": 0x0012,
    "walk_uzi": 0x0022,
    "walk_grenade_mine": 0x0032,
    "walk_flamethrower": 0x0042,
    "idle_pistol": 0x0052,
    "idle_shotgun": 0x0062,
    "idle_uzi": 0x0072,
    "idle_grenade_mine": 0x0082,
    "idle_flamethrower": 0x0092,
    "maniac_jllbfr": 0x00F2,
    "roll": 0x0142,
    "kneeling_roll_fire": 0x0172,
    "life_loss_common": 0x0262,
}


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def facing_selectors(rom: bytes, base: int) -> list[int]:
    return [u16(rom, DIR_TABLE + base + facing * 2) for facing in range(8)]


def resolve_selector(rom: bytes, descriptor: int, selector: int) -> dict[str, Any]:
    if descriptor + selector + 2 > len(rom):
        return {"valid": False, "reason": "selector_out_of_rom"}
    encoded = u16(rom, descriptor + selector)
    alias_offset = encoded & 0x0FFE
    if descriptor + alias_offset + 2 > len(rom):
        return {
            "valid": False,
            "reason": "alias_out_of_rom",
            "encoded_entry": encoded,
            "alias_offset": alias_offset,
        }
    record_offset = u16(rom, descriptor + alias_offset)
    record = descriptor + record_offset
    if record < 0 or record + 0x10 > len(rom):
        return {
            "valid": False,
            "reason": "record_header_out_of_rom",
            "encoded_entry": encoded,
            "alias_offset": alias_offset,
            "record_offset": record_offset,
        }
    piece_count = rom[record + 0x0F]
    record_size = 0x10 + piece_count * 4
    if piece_count > 64 or record + record_size > len(rom):
        return {
            "valid": False,
            "reason": "implausible_record",
            "encoded_entry": encoded,
            "alias_offset": alias_offset,
            "record_offset": record_offset,
            "piece_count": piece_count,
        }
    return {
        "valid": True,
        "encoded_entry": encoded,
        "alias_offset": alias_offset,
        "record_offset": record_offset,
        "record_address": record,
        "record_flags": rom[record + 0x0E],
        "piece_count": piece_count,
        "record_size": record_size,
        "control_words": [u16(rom, record + i * 2) for i in range(3)],
        "geometry_words": [u16(rom, record + off) for off in (0x06, 0x08, 0x0A, 0x0C)],
    }


def call_target(rom: bytes, pc: int) -> tuple[int, int] | None:
    """Return (instruction_size,target) for common 68000 subroutine forms."""
    op = u16(rom, pc)
    if op == 0x4EB9 and pc + 6 <= len(rom):  # JSR absolute long
        return 6, u32(rom, pc + 2)
    if op == 0x4EB8 and pc + 4 <= len(rom):  # JSR absolute word
        target = u16(rom, pc + 2)
        if target & 0x8000:
            target -= 0x10000
        return 4, target & 0xFFFFFFFF
    if op & 0xFF00 == 0x6100:  # BSR
        disp8 = op & 0xFF
        if disp8 == 0:
            if pc + 4 > len(rom):
                return None
            disp = int.from_bytes(rom[pc + 2:pc + 4], "big", signed=True)
            return 4, pc + 2 + disp
        if disp8 == 0xFF:  # 68020 long BSR; not expected on 68000 retail code
            return None
        disp = disp8 - 0x100 if disp8 & 0x80 else disp8
        return 2, pc + 2 + disp
    return None


def find_calls_to(rom: bytes, target: int, start: int = 0, end: int | None = None) -> list[dict[str, Any]]:
    end = len(rom) if end is None else min(end, len(rom))
    rows = []
    for pc in range(start & ~1, end - 1, 2):
        decoded = call_target(rom, pc)
        if decoded is None:
            continue
        size, resolved = decoded
        if resolved == target:
            context_start = max(start, pc - 12)
            context_end = min(end, pc + size + 12)
            rows.append({
                "pc": pc,
                "size": size,
                "context_sha1": hashlib.sha1(rom[context_start:context_end]).hexdigest(),
                "context_start": context_start,
                "context_end": context_end,
            })
    return rows


def ff_runs(rom: bytes, start: int, end: int, minimum: int = 0x20) -> list[dict[str, int]]:
    rows = []
    pos = start
    while pos < end:
        if rom[pos] != 0xFF:
            pos += 1
            continue
        run_start = pos
        while pos < end and rom[pos] == 0xFF:
            pos += 1
        size = pos - run_start
        if size >= minimum:
            rows.append({"start": run_start, "end": pos, "size": size})
    return rows


def absolute_long_refs(rom: bytes, address: int) -> list[int]:
    needle = address.to_bytes(4, "big")
    hits = []
    pos = 0
    while True:
        hit = rom.find(needle, pos)
        if hit < 0:
            break
        hits.append(hit)
        pos = hit + 1
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest = hashlib.sha1(rom).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    # Existing M0.6 animation-resolver anchor.
    expected_fddc = bytes.fromhex(
        "2268002c3231000031410024300102400ffe317100000020"
    )
    assert rom[0x00FDEC:0x00FE04] == expected_fddc

    arch191_descriptor = u32(rom, ARCHETYPE_TABLE + PLAYER_ARCHETYPE_ID * 4)
    assert arch191_descriptor == ARCH191_DESCRIPTOR_EXPECTED

    families: dict[str, Any] = {}
    visual_records: set[tuple[int, int]] = set()
    arch191_records: set[tuple[int, int]] = set()
    for name, base in FAMILY_BASES.items():
        selectors = facing_selectors(rom, base)
        visual = [resolve_selector(rom, RUNTIME_VISUAL_DESCRIPTOR, selector) for selector in selectors]
        archetype = [resolve_selector(rom, arch191_descriptor, selector) for selector in selectors]
        for row in visual:
            if row.get("valid"):
                visual_records.add((row["record_offset"], row["record_size"]))
        for row in archetype:
            if row.get("valid"):
                arch191_records.add((row["record_offset"], row["record_size"]))
        families[name] = {
            "base": base,
            "selectors": selectors,
            "runtime_visual": visual,
            "archetype191": archetype,
            "all_runtime_visual_valid": all(row.get("valid") for row in visual),
            "all_archetype191_valid": all(row.get("valid") for row in archetype),
        }

    # Locate code paths that actually invoke the canonical selector->record resolver.
    fddc_calls_near_helpers = find_calls_to(rom, FDDC, 0x00001800, 0x00002600)
    fddc_calls_global = find_calls_to(rom, FDDC)

    visual_window_start = RUNTIME_VISUAL_DESCRIPTOR
    visual_window_end = min(RUNTIME_VISUAL_DESCRIPTOR + 0x10000, len(rom))
    free_runs = ff_runs(rom, visual_window_start, visual_window_end, 0x20)

    # Conservative occupied intervals from player-family records that actually
    # resolve against the runtime visual descriptor. This does not by itself make
    # every remaining FF run safe; the report labels candidates, not allocations.
    occupied_visual = [
        {
            "start": RUNTIME_VISUAL_DESCRIPTOR + offset,
            "end": RUNTIME_VISUAL_DESCRIPTOR + offset + size,
            "offset": offset,
            "size": size,
        }
        for offset, size in sorted(visual_records)
    ]

    report = {
        "schema": "truerecall.m09c.native_sequence_seam.v1",
        "base_sha1": digest,
        "status": "static_probe",
        "descriptors": {
            "archetype191": {
                "address": arch191_descriptor,
                "evidence": "archetype table 0x079906 + 191*4",
            },
            "runtime_visual_avatar": {
                "address": RUNTIME_VISUAL_DESCRIPTOR,
                "evidence": "M08/M09B2 runtime descriptor sweep; this probe only analyzes its retail structure",
                "absolute_long_references": absolute_long_refs(rom, RUNTIME_VISUAL_DESCRIPTOR),
            },
        },
        "fddc": {
            "address": FDDC,
            "resolver_signature_start": 0x00FDEC,
            "writes": {
                "encoded_entry": "object+0x24",
                "record_offset": "object+0x20",
            },
            "near_helper_callers": fddc_calls_near_helpers,
            "global_callers": fddc_calls_global,
        },
        "direction_table": DIR_TABLE,
        "families": families,
        "resolved_record_counts": {
            "runtime_visual": len(visual_records),
            "archetype191": len(arch191_records),
        },
        "runtime_visual_records": occupied_visual,
        "runtime_visual_64k_ff_candidates": free_runs,
        "candidate_policy": (
            "FF runs are only candidate storage. M09C must not allocate one until "
            "selector/record/group-table overlap and reference containment are proven."
        ),
        "next_gate": (
            "Use the canonical result to choose a player-facing selector family and an "
            "unused selector/record path that preserves object+0x2C == 0x0F0000."
        ),
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
