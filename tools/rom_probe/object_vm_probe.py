#!/usr/bin/env python3
"""Probe the True Lies generic object behavior VM and type tables.

Outputs structural metadata only. It does not dump copyrighted object scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_FLAG_TABLE = 0x07A24A
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
VM_JUMP_TABLE = 0x011814
VM_INTERPRETER = 0x011934
VM_ENTRY_SIZE = 4
VM_ENTRY_COUNT = (VM_INTERPRETER - VM_JUMP_TABLE) // VM_ENTRY_SIZE
RETAIL_MAX_PLACEMENT_TYPE = 138


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


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

    # Type initializer anchors around 0x010102.
    assert rom[0x01011C:0x010142] == bytes.fromhex(
        "720047f90007a24a123300003341000447f90007a33c12330000d040d04047f90007953e20330000"
    )
    assert rom[0x010142:0x010172] == bytes.fromhex(
        "4a01671823400042237c00011934003e334900100669003e0010600e23400042334900100669004200107200234100062341000a"
    )

    jump_entries = []
    targets = set()
    for index in range(VM_ENTRY_COUNT):
        off = VM_JUMP_TABLE + index * VM_ENTRY_SIZE
        opcode = u16(rom, off)
        displacement = signed16(u16(rom, off + 2))
        assert opcode == 0x6000  # BRA.W
        target = off + 4 + displacement
        assert 0 <= target < len(rom)
        targets.add(target)
        jump_entries.append({
            "script_offset": f"0x{index * 4:04X}",
            "stub_rom": f"0x{off:06X}",
            "handler_rom": f"0x{target:06X}",
        })
    assert VM_ENTRY_COUNT == 72
    assert len(targets) == 72

    types = []
    direct = []
    scripted = []
    for type_id in range(RETAIL_MAX_PLACEMENT_TYPE + 1):
        flag = rom[TYPE_FLAG_TABLE + type_id]
        selector = rom[TYPE_SELECTOR_TABLE + type_id]
        pointer = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
        representation = "scripted" if selector else "direct_code"
        row = {
            "type_id": type_id,
            "flag_table_byte": flag,
            "selector": selector,
            "per_type_pointer": f"0x{pointer:06X}",
            "representation": representation,
        }
        types.append(row)
        (scripted if selector else direct).append(row)

    # All retail placement IDs currently observed have zero in the first byte table.
    assert all(row["flag_table_byte"] == 0 for row in types)
    assert [row["type_id"] for row in direct] == [1, 10, 101]
    assert u32(rom, TYPE_POINTER_TABLE + 1 * 4) == 0x009732
    assert u32(rom, TYPE_POINTER_TABLE + 10 * 4) == 0x0050F0
    assert u32(rom, TYPE_POINTER_TABLE + 101 * 4) == 0x00505A

    report = {
        "schema": "truerecall.object_vm.v1",
        "base_sha1": digest,
        "type_tables": {
            "flag_byte_table": f"0x{TYPE_FLAG_TABLE:06X}",
            "selector_table": f"0x{TYPE_SELECTOR_TABLE:06X}",
            "pointer_table": f"0x{TYPE_POINTER_TABLE:06X}",
            "retail_placement_id_range_probed": [0, RETAIL_MAX_PLACEMENT_TYPE],
            "scripted_count": len(scripted),
            "direct_code_count": len(direct),
            "direct_code_types": direct,
        },
        "vm": {
            "interpreter": f"0x{VM_INTERPRETER:06X}",
            "jump_table": f"0x{VM_JUMP_TABLE:06X}",
            "entry_size": VM_ENTRY_SIZE,
            "entry_count": VM_ENTRY_COUNT,
            "unique_handler_count": len(targets),
            "entries": jump_entries,
        },
        "interpretation": {
            "selector_1": "per-type pointer is script/data; object uses fixed generic interpreter 0x11934",
            "selector_0": "per-type pointer is installed as direct executable routine",
        },
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
