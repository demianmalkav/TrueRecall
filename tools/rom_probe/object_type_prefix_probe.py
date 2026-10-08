#!/usr/bin/env python3
"""Symbolically evaluate straight-line True Lies object-script prefixes.

The evaluator is deliberately conservative. It recovers only constant callback
assignments proven before complex script flow. Stack-relative addresses and
other nonconstant values remain symbolic so temporary object-field writes cannot
be misclassified as executable callback pointers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E

# Bytes consumed after the opcode word for fixed-width VM opcodes.
OPERAND_BYTES = {
    0x0014: 2, 0x0018: 2, 0x001C: 2, 0x0020: 4,
    0x0024: 4, 0x0028: 4, 0x002C: 2, 0x0030: 4,
    0x0034: 2, 0x0038: 2, 0x003C: 2, 0x0040: 2,
    0x0044: 0, 0x0048: 0, 0x004C: 0, 0x0050: 0,
    0x0054: 4, 0x0058: 4, 0x005C: 2, 0x0060: 4,
    0x0064: 2, 0x0068: 2, 0x006C: 2,
    0x0070: 0, 0x0074: 0, 0x0078: 0, 0x007C: 0,
    0x0080: 2, 0x0084: 4, 0x0088: 0, 0x008C: 0,
    0x0090: 0, 0x0094: 0, 0x0098: 0, 0x009C: 0,
    0x00A0: 0, 0x00A4: 0, 0x00A8: 0,
    0x00B0: 0, 0x00B4: 0, 0x00B8: 0, 0x00BC: 0,
    0x00C0: 0, 0x00C4: 0, 0x00C8: 0, 0x00CC: 0,
    0x00D0: 0, 0x00D4: 0, 0x00D8: 0, 0x00DC: 0,
    0x00E0: 0, 0x00E4: 4, 0x00E8: 0, 0x00EC: 2,
    0x00F0: 0, 0x00F4: 0, 0x00F8: 0, 0x00FC: 0,
    0x0100: 0, 0x0104: 0, 0x0108: 0, 0x010C: 0,
    0x0110: 0, 0x0114: 0, 0x0118: 0, 0x011C: 0,
}

# Branch/call/return/switch opcodes are intentionally not traversed here.
FLOW_STOP = {0x0000, 0x0004, 0x0008, 0x000C, 0x0010, 0x00AC}


def const(value: int, bits: int):
    return ("const", value & ((1 << bits) - 1), bits)


def field(offset: int, bits: int):
    return ("field", offset, bits)


def binary(name: str, left, right):
    return (name, left, right)


def constant_value(expr):
    return expr[1] if isinstance(expr, tuple) and expr and expr[0] == "const" else None


def plausible_code_pointer(value: int | None, rom_size: int) -> bool:
    """Accept only aligned pointers inside the canonical ROM code/address space."""
    return value is not None and 0x200 <= value < rom_size and (value & 1) == 0


def placed_type_counts(rom: bytes) -> Counter[int]:
    counts: Counter[int] = Counter()
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc)
        start = u16(rom, desc + 2)
        source = u32(rom, desc + 6)
        decoded = lzbeam_decode(rom, source)

        runs = []
        run_pos = desc + 0x0A
        total = 0
        while total < count:
            stride = rom[run_pos]
            quantity = rom[run_pos + 1]
            run_pos += 2
            assert stride in (6, 8)
            runs.append((stride, quantity))
            total += quantity
        assert total == count

        pos = start
        for stride, quantity in runs:
            for _ in range(quantity):
                counts[u16(decoded, pos) & 0x03FF] += 1
                pos += stride
    return counts


def evaluate_prefix(rom: bytes, type_id: int, max_ops: int = 100):
    if rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return {"representation": "direct_code", "writes": []}

    pc = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    d1 = ("unknown", "D1")
    d2 = ("unknown", "D2")
    stack = []
    writes = []
    stop_reason = "max_ops"

    for _ in range(max_ops):
        opcode = u16(rom, pc)
        pc += 2
        if opcode in FLOW_STOP:
            stop_reason = f"flow_0x{opcode:04X}"
            break
        if opcode not in OPERAND_BYTES:
            stop_reason = f"unknown_0x{opcode:04X}"
            break

        size = OPERAND_BYTES[opcode]
        operand_raw = rom[pc:pc + size]
        pc += size
        operand = int.from_bytes(operand_raw, "big") if size else None

        if opcode == 0x0014:
            # LEA 0(A3,D1.W),A0 / MOVE.L A0,D1: runtime stack-relative address.
            d1 = ("stack_relative_address", operand)
        elif opcode == 0x0018:
            d1 = ("object_link_relative_address", operand)
        elif opcode == 0x001C:
            d2 = const(operand, 16)
        elif opcode == 0x0020:
            d2 = const(operand, 32)
        elif opcode == 0x0080:
            d1 = const(operand, 16)
        elif opcode == 0x0084:
            d1 = const(operand, 32)
        elif opcode in (0x0088, 0x008C):
            d1 = ("memory_load_into_D1", opcode)
        elif opcode == 0x00A8:
            d1, d2 = d2, d1
        elif opcode == 0x0034:
            d2 = field(operand, 8)
        elif opcode == 0x0038:
            d2 = field(operand, 16)
        elif opcode == 0x003C:
            d2 = ("sign_extend", field(operand, 16))
        elif opcode == 0x0040:
            d2 = field(operand, 32)
        elif opcode in (0x0024, 0x0028, 0x002C, 0x0030):
            d2 = ("memory_load", opcode, operand)
        elif opcode in (0x0044, 0x0048, 0x004C, 0x0050):
            d2 = ("memory_load_at_D1", opcode)
        elif opcode in (0x0064, 0x0068, 0x006C):
            width = {0x0064: 8, 0x0068: 16, 0x006C: 32}[opcode]
            writes.append({"offset": operand, "width": width, "expr": d2})
        elif opcode == 0x00B0:
            d2 = binary("and", d2, d1)
        elif opcode == 0x00B4:
            d2 = binary("or", d2, d1)
        elif opcode == 0x00B8:
            d2 = binary("xor", d2, d1)
        elif opcode == 0x00C4:
            d2 = binary("add", d2, d1)
        elif opcode == 0x00C8:
            d2 = binary("sub", d2, d1)
        elif opcode == 0x011C:
            d1 = binary("add", d1, d2)
        elif opcode == 0x00D8:
            d2 = ("neg", d2)
        elif opcode == 0x00DC:
            d2 = ("not", d2)
        elif opcode == 0x00E0:
            d2 = ("bool_not", d2)
        elif opcode == 0x00E4:
            d2 = ("native_call_result", f"0x{operand:06X}")
        elif opcode in (0x0090, 0x0094, 0x0098, 0x009C, 0x00A0, 0x00A4):
            d2 = ("compare_result", opcode, d2, d1)
        elif opcode in (0x00BC, 0x00C0, 0x00CC, 0x00D0, 0x00D4, 0x00E8):
            d2 = ("operation_result", opcode, d2, d1)
        elif opcode in (0x00F0, 0x00F4):
            stack.append(d2)
        elif opcode in (0x00F8, 0x00FC):
            d2 = stack.pop() if stack else ("unknown", "stack_pop_D2")
        elif opcode in (0x0100, 0x0104):
            stack.append(d1)
        elif opcode in (0x0108, 0x010C):
            d1 = stack.pop() if stack else ("unknown", "stack_pop_D1")
        elif opcode in (0x0110, 0x0114, 0x0118):
            d2 = ("engine_result", opcode)
        # Stores not targeting object-relative fields do not affect this probe.
    else:
        stop_reason = "max_ops"

    latest = {}
    for write in writes:
        latest[(write["offset"], write["width"])] = write["expr"]

    raw34 = constant_value(latest.get((0x34, 32)))
    raw38 = constant_value(latest.get((0x38, 32)))
    cb34 = raw34 if plausible_code_pointer(raw34, len(rom)) else None
    cb38 = raw38 if plausible_code_pointer(raw38, len(rom)) else None

    return {
        "representation": "scripted",
        "stop_reason": stop_reason,
        "writes": writes,
        "callback_34": cb34,
        "callback_38": cb38,
        "final_34_expr": latest.get((0x34, 32)),
        "final_38_expr": latest.get((0x38, 32)),
    }


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

    placements = placed_type_counts(rom)
    assert sum(placements.values()) == 2449
    assert len(placements) == 128

    groups = defaultdict(lambda: {"type_ids": [], "placements": 0})
    unresolved_types = []
    unresolved_placements = 0

    for type_id, count in sorted(placements.items()):
        result = evaluate_prefix(rom, type_id)
        cb34 = result.get("callback_34")
        cb38 = result.get("callback_38")
        if cb34 is None and cb38 is None:
            unresolved_types.append(type_id)
            unresolved_placements += count
            continue
        key = (cb34, cb38)
        groups[key]["type_ids"].append(type_id)
        groups[key]["placements"] += count

    group_rows = []
    for (cb34, cb38), value in groups.items():
        group_rows.append({
            "callback_34": None if cb34 is None else f"0x{cb34:06X}",
            "callback_38": None if cb38 is None else f"0x{cb38:06X}",
            "type_ids": value["type_ids"],
            "type_count": len(value["type_ids"]),
            "placements": value["placements"],
        })
    group_rows.sort(key=lambda row: (-row["placements"], row["type_ids"][0]))

    resolved_placements = sum(row["placements"] for row in group_rows)
    # Regression for the bug that originally misclassified type 44 as 0x003FFF.
    type44 = evaluate_prefix(rom, 44)
    assert type44["callback_34"] is None
    assert type44["final_34_expr"][0] == "stack_relative_address"

    report = {
        "schema": "truerecall.object_type_prefix.v2",
        "base_sha1": digest,
        "method": "conservative straight-line symbolic execution; stack-relative values remain nonconstant and code pointers must be aligned/in-ROM",
        "placement_types": len(placements),
        "total_placements": sum(placements.values()),
        "callback_resolved_placements": resolved_placements,
        "callback_resolved_fraction": resolved_placements / sum(placements.values()),
        "callback_groups": group_rows,
        "unresolved": {
            "type_ids": unresolved_types,
            "type_count": len(unresolved_types),
            "placements": unresolved_placements,
        },
        "regressions": {
            "type_44_false_0x003FFF_removed": True,
        },
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
