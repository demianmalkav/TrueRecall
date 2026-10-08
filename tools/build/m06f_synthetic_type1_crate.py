#!/usr/bin/env python3
"""M0.6F: inject a new scripted object class into an unused retail type slot.

Type 1 exists in engine tables but has zero retail placements. This build:
- converts type 1 from direct-code to VM-scripted;
- gives it a relocated edited clone of the shotgun-weapon pickup behavior;
- clones type 69's presentation/stat metadata into archetype/type 1;
- relocates the type 113 supply-crate script and changes one loot branch from
  type 68 (shotgun ammo) to synthetic type 1;
- recomputes the Genesis checksum.

The canonical ROM is never overwritten. This is a static authoring proof; runtime
execution must still be verified in an emulator or on hardware.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROM_PROBE = Path(__file__).resolve().parents[1] / "rom_probe"
sys.path.insert(0, str(ROM_PROBE))
from vm_source_export import export_type_source
from vm_asm import assemble, parse_text
from vm_disasm import reachable, u32

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
ARCHETYPE_TABLE = 0x079906
TYPE_FLAG_TABLE = 0x07A24A
HP_NORMAL = 0x07A066
HP_HARD = 0x079F74
DAMAGE_NORMAL = 0x079E82
DAMAGE_HARD = 0x079D90
CHECKSUM_OFFSET = 0x018E

SYNTHETIC_TYPE = 1
DONOR_TYPE = 69
CRATE_TYPE = 113
SYNTHETIC_SCRIPT = 0x1FB000
CRATE_SCRIPT = 0x1FB200
FREE_START = 0x1FABC3
FREE_END = 0x200000


def checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def set_u32(buf: bytearray, off: int, value: int) -> None:
    buf[off:off + 4] = value.to_bytes(4, "big")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(raw)}")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    # Prove the chosen slot is the known unused retail direct-code type.
    if raw[TYPE_SELECTOR_TABLE + SYNTHETIC_TYPE] != 0:
        raise SystemExit("type 1 is no longer the expected unused direct-code slot")
    if u32(raw, TYPE_POINTER_TABLE + SYNTHETIC_TYPE * 4) != 0x009732:
        raise SystemExit("unexpected retail type-1 pointer")

    # Build the new type-1 script from a proven retail source representation.
    donor_start, donor_source = export_type_source(raw, DONOR_TYPE)
    if donor_start != 0x1761F0:
        raise SystemExit("unexpected donor script base")
    grant5 = "  MOVI_W_D1 0x0005\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    grant6 = "  MOVI_W_D1 0x0006\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    if donor_source.count(grant5) != 1:
        raise SystemExit("shotgun-grant source pattern not unique")
    synthetic_source = donor_source.replace(grant5, grant6)
    synthetic_bytes, _ = assemble(parse_text(synthetic_source), SYNTHETIC_SCRIPT)

    # Relocate the crate script and redirect exactly one loot branch: 68 -> 1.
    crate_start, crate_source = export_type_source(raw, CRATE_TYPE)
    if crate_start != 0x17C84A:
        raise SystemExit("unexpected crate script base")
    spawn_ammo = "  MOVI_W_D2 0x0044\n  PUSH_D2_W\n  NATIVE SpawnLinkedObject\n"
    spawn_new = "  MOVI_W_D2 0x0001\n  PUSH_D2_W\n  NATIVE SpawnLinkedObject\n"
    if crate_source.count(spawn_ammo) != 1:
        raise SystemExit("crate shotgun-ammo spawn pattern not unique")
    crate_source = crate_source.replace(spawn_ammo, spawn_new)
    crate_bytes, _ = assemble(parse_text(crate_source), CRATE_SCRIPT)

    for start, blob in ((SYNTHETIC_SCRIPT, synthetic_bytes), (CRATE_SCRIPT, crate_bytes)):
        if start < FREE_START or start + len(blob) > FREE_END:
            raise SystemExit("script relocation falls outside verified FF padding")
        if any(x != 0xFF for x in raw[start:start + len(blob)]):
            raise SystemExit(f"target 0x{start:06X} is not pristine FF padding")

    out = bytearray(raw)
    out[SYNTHETIC_SCRIPT:SYNTHETIC_SCRIPT + len(synthetic_bytes)] = synthetic_bytes
    out[CRATE_SCRIPT:CRATE_SCRIPT + len(crate_bytes)] = crate_bytes

    # Convert type 1 to VM-scripted representation and point it at the new source.
    out[TYPE_SELECTOR_TABLE + SYNTHETIC_TYPE] = 1
    set_u32(out, TYPE_POINTER_TABLE + SYNTHETIC_TYPE * 4, SYNTHETIC_SCRIPT)

    # Give initial archetype 1 the same proven visual/stat metadata as donor 69.
    set_u32(out, ARCHETYPE_TABLE + SYNTHETIC_TYPE * 4,
            u32(raw, ARCHETYPE_TABLE + DONOR_TYPE * 4))
    for table in (TYPE_FLAG_TABLE, HP_NORMAL, HP_HARD, DAMAGE_NORMAL, DAMAGE_HARD):
        out[table + SYNTHETIC_TYPE] = raw[table + DONOR_TYPE]

    # Redirect only crate type 113 to its relocated source variant.
    set_u32(out, TYPE_POINTER_TABLE + CRATE_TYPE * 4, CRATE_SCRIPT)

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = checksum(out).to_bytes(2, "big")

    # Static regression checks against the generated ROM.
    if out[TYPE_SELECTOR_TABLE + SYNTHETIC_TYPE] != 1:
        raise AssertionError("synthetic type did not enter scripted mode")
    if u32(out, TYPE_POINTER_TABLE + SYNTHETIC_TYPE * 4) != SYNTHETIC_SCRIPT:
        raise AssertionError("synthetic type pointer mismatch")
    if u32(out, TYPE_POINTER_TABLE + CRATE_TYPE * 4) != CRATE_SCRIPT:
        raise AssertionError("crate pointer mismatch")
    if u32(out, ARCHETYPE_TABLE + SYNTHETIC_TYPE * 4) != u32(raw, ARCHETYPE_TABLE + DONOR_TYPE * 4):
        raise AssertionError("synthetic archetype descriptor mismatch")

    synth_ins, _, _ = reachable(bytes(out), SYNTHETIC_SCRIPT, max_states=200000, max_stack=32)
    crate_ins, _, _ = reachable(bytes(out), CRATE_SCRIPT, max_states=200000, max_stack=32)
    if len(synth_ins) != 68 or len(crate_ins) != 341:
        raise AssertionError("unexpected relocated instruction counts")

    child_signature = bytes.fromhex("001c000100f000e4000020d8")
    if bytes(out[CRATE_SCRIPT:CRATE_SCRIPT + len(crate_bytes)]).count(child_signature) != 1:
        raise AssertionError("crate does not contain exactly one type-1 linked spawn")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"base_sha1={digest}")
    print(f"synthetic_type={SYNTHETIC_TYPE}")
    print(f"synthetic_script=0x{SYNTHETIC_SCRIPT:06X} bytes={len(synthetic_bytes)} instructions={len(synth_ins)}")
    print(f"crate_script=0x{CRATE_SCRIPT:06X} bytes={len(crate_bytes)} instructions={len(crate_ins)}")
    print(f"checksum=0x{checksum(out):04X}")
    print(f"output_sha1={hashlib.sha1(out).hexdigest()}")


if __name__ == "__main__":
    main()
