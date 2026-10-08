#!/usr/bin/env python3
"""M0.6E: relocate and edit the scripted shotgun pickup through the VM toolchain.

This is a controlled authoring proof. It exports retail type 69 to source,
changes the initial shotgun shell grant 5 -> requested value (default 6),
assembles the script into verified FF padding at 0x1FB000, redirects the type
pointer, and repairs the Genesis checksum. The canonical base is never modified.
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
from vm_disasm import reachable, u32, TYPE_POINTER_TABLE

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_ID = 69
ORIGINAL_START = 0x1761F0
RELOCATED_START = 0x1FB000
FREE_START = 0x1FABC3
FREE_END = 0x200000
CHECKSUM_OFFSET = 0x018E


def checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--amount", type=int, default=6)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(raw)}")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")
    if not 0 <= args.amount <= 99:
        raise SystemExit("amount must be 0..99")

    ptr_off = TYPE_POINTER_TABLE + TYPE_ID * 4
    if u32(raw, ptr_off) != ORIGINAL_START:
        raise SystemExit(f"unexpected type 69 pointer: 0x{u32(raw, ptr_off):06X}")

    original_start, source = export_type_source(raw, TYPE_ID)
    assert original_start == ORIGINAL_START
    needle = "  MOVI_W_D1 0x0005\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    replacement = f"  MOVI_W_D1 0x{args.amount:04X}\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    if source.count(needle) != 1:
        raise SystemExit("expected unique shotgun-grant source pattern not found")
    edited_source = source.replace(needle, replacement)

    built, labels = assemble(parse_text(edited_source), RELOCATED_START)
    if RELOCATED_START < FREE_START or RELOCATED_START + len(built) > FREE_END:
        raise SystemExit("relocated script does not fit the validated FF padding region")
    if any(x != 0xFF for x in raw[RELOCATED_START:RELOCATED_START + len(built)]):
        raise SystemExit("relocation target is not pristine FF padding")

    out = bytearray(raw)
    out[RELOCATED_START:RELOCATED_START + len(built)] = built
    out[ptr_off:ptr_off + 4] = RELOCATED_START.to_bytes(4, "big")
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = checksum(out).to_bytes(2, "big")

    if u32(out, ptr_off) != RELOCATED_START:
        raise AssertionError("type pointer did not update")
    original_ins, _, _ = reachable(raw, ORIGINAL_START, max_states=200000, max_stack=32)
    relocated_ins, _, _ = reachable(bytes(out), RELOCATED_START, max_states=200000, max_stack=32)
    if len(original_ins) != 68 or len(relocated_ins) != 68:
        raise AssertionError("unexpected instruction count")
    norm0 = sorted((pc - ORIGINAL_START, ins["op"], ins["end"] - pc) for pc, ins in original_ins.items())
    norm1 = sorted((pc - RELOCATED_START, ins["op"], ins["end"] - pc) for pc, ins in relocated_ins.items())
    if norm0 != norm1:
        raise AssertionError("relocated instruction shape changed")
    hits = [pc for pc, ins in relocated_ins.items() if ins["op"] == 0x0080 and ins.get("operand") == args.amount]
    if not hits:
        raise AssertionError("edited immediate not present in relocated script")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"base_sha1={digest}")
    print(f"type_id={TYPE_ID}")
    print(f"original_script=0x{ORIGINAL_START:06X}")
    print(f"relocated_script=0x{RELOCATED_START:06X}")
    print(f"script_bytes={len(built)}")
    print(f"labels={len(labels)}")
    print(f"amount={args.amount}")
    print(f"checksum=0x{checksum(out):04X}")
    print(f"output_sha1={hashlib.sha1(out).hexdigest()}")


if __name__ == "__main__":
    main()
