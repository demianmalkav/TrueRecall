#!/usr/bin/env python3
"""Recover object archetype / animation-set assignments from True Lies scripts.

The probe follows VM control flow conservatively, finds the native wrapper that
calls the engine archetype setter at 0xF9D4, and records only structural metadata.
It does not dump animation graphics or full object scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
ARCHETYPE_TABLE = 0x079906
ARCHETYPE_SETTER = 0x00F9D4
VM_ARCHETYPE_NATIVE = 0x002436
SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19

HP_NORMAL = 0x07A066
HP_HARD = 0x079F74
DAMAGE_NORMAL = 0x079E82
DAMAGE_HARD = 0x079D90

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


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def local_target(operand_address: int, target_word: int) -> int:
    return (operand_address & 0xFFFF0000) | target_word


def lzbeam_decode(rom: bytes, off: int) -> bytes:
    out_len = u16(rom, off)
    command_offset = u16(rom, off + 2)
    read_pos = off + 4
    command_pos = off + command_offset + 2
    bits_left = 0
    current = 0
    out = bytearray()

    def bit() -> int:
        nonlocal command_pos, bits_left, current
        if bits_left == 0:
            current = rom[command_pos]
            command_pos += 1
            bits_left = 8
        value = (current >> 7) & 1
        current = (current << 1) & 0xFF
        bits_left -= 1
        return value

    def bits(count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | bit()
        return value

    def count() -> int:
        value = 1
        while bit() == 0:
            value = (value << 1) | bit()
        return value

    literal_count = count()
    out.extend(rom[read_pos:read_pos + literal_count])
    read_pos += literal_count
    while len(out) < out_len:
        written = len(out)
        index_bits = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        source = bits(index_bits)
        copy_count = count() + 2
        for i in range(copy_count):
            out.append(out[source + i])
            if len(out) >= out_len:
                break
        if len(out) < out_len and bit() == 0:
            literal_count = count()
            out.extend(rom[read_pos:read_pos + literal_count])
            read_pos += literal_count
    return bytes(out[:out_len])


def placement_counts(rom: bytes):
    counts = Counter()
    scenes = defaultdict(set)
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
                type_id = u16(decoded, pos) & 0x03FF
                counts[type_id] += 1
                scenes[type_id].add(scene_index)
                pos += stride
    return counts, scenes


def reachable_instructions(rom: bytes, start: int):
    """Return reachable VM instructions using structural control flow only."""
    todo = [start]
    visited = set()
    decoded = {}
    while todo:
        pc = todo.pop()
        while pc not in visited and 0 <= pc < len(rom):
            visited.add(pc)
            here = pc
            opcode = u16(rom, pc)
            pc += 2

            if opcode in (0x0000, 0x0004):
                target_word = u16(rom, pc)
                target = local_target(pc, target_word)
                fallthrough = pc + 2
                decoded[here] = (opcode, rom[pc:pc + 2], [target, fallthrough])
                todo.append(target)
                pc = fallthrough
                continue
            if opcode == 0x0008:
                target_word = u16(rom, pc)
                target = local_target(pc, target_word)
                decoded[here] = (opcode, rom[pc:pc + 2], [target])
                todo.append(target)
                break
            if opcode == 0x000C:
                target = u32(rom, pc)
                ret = pc + 4
                decoded[here] = (opcode, rom[pc:pc + 4], [target, ret])
                todo.extend((target, ret))
                break
            if opcode == 0x0010:
                decoded[here] = (opcode, b"", [])
                break
            if opcode == 0x00AC:
                cases = u16(rom, pc)
                p = pc + 2
                targets = []
                for _ in range(cases):
                    p += 2  # case value
                    target_word = u16(rom, p)
                    targets.append(local_target(p, target_word))
                    p += 2
                targets.append(p)  # fallthrough after table
                decoded[here] = (opcode, rom[pc:p], targets)
                todo.extend(targets)
                break

            size = OPERAND_BYTES.get(opcode)
            if size is None:
                decoded[here] = (opcode, b"", [])
                break
            operand = rom[pc:pc + size]
            decoded[here] = (opcode, operand, [pc + size])
            pc += size
    return decoded


def archetype_calls(rom: bytes, type_id: int):
    if rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return []
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    instructions = reachable_instructions(rom, start)
    result = []
    for address, (opcode, operand, _successors) in instructions.items():
        if opcode != 0x00E4 or int.from_bytes(operand, "big") != VM_ARCHETYPE_NATIVE:
            continue
        # Retail scripts that set an archetype use:
        #   001C <word id> 00F0 00E4 00002436
        if address >= 6 and u16(rom, address - 6) == 0x001C and u16(rom, address - 2) == 0x00F0:
            result.append(u16(rom, address - 4))
        else:
            result.append(None)
    return sorted(set(result), key=lambda value: (value is None, value))


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

    # Engine setter: store archetype ID, multiply by four, look up descriptor,
    # store descriptor pointer, then clear animation-state fields.
    assert rom[ARCHETYPE_SETTER:ARCHETYPE_SETTER + 44] == bytes.fromhex(
        "3140002ad040d04043f900079906227100002149002c70003140001c3140001e314000203140002231400024"
    )
    # VM wrapper: A0=A5/current object, word argument -> D0, call setter, return VM dispatch.
    assert rom[VM_ARCHETYPE_NATIVE:VM_ARCHETYPE_NATIVE + 18] == bytes.fromhex(
        "304d302f00064eb90000f9d44ef9000119f4"
    )
    # Player/world avatar has a direct hardcoded archetype-set call with ID 0xBF.
    assert bytes.fromhex("303c00bf4eb90000f9d4") in rom[0x00D360:0x00D3A0]

    # Difficulty-stat initializer 0x1EEC uses FC4A*4 to choose HP/damage tables,
    # then indexes those tables by object+0x2A.
    assert rom[0x001EEC:0x001F16] == bytes.fromhex(
        "3038fc4ad040d0403228002a227b001c4228006c11711000006d227b00164228006e11711000006f4e75"
    )

    counts, scenes = placement_counts(rom)
    assert sum(counts.values()) == 2449

    rows = []
    aggregate = defaultdict(lambda: {"types": [], "placements": 0, "scenes": set()})
    for type_id in sorted(counts):
        ids = archetype_calls(rom, type_id)
        for archetype_id in ids:
            if archetype_id is None:
                continue
            descriptor = u32(rom, ARCHETYPE_TABLE + archetype_id * 4)
            row = {
                "type_id": type_id,
                "archetype_id": archetype_id,
                "animation_descriptor": f"0x{descriptor:06X}",
                "hp_normal": rom[HP_NORMAL + archetype_id],
                "hp_hard": rom[HP_HARD + archetype_id],
                "damage_normal": rom[DAMAGE_NORMAL + archetype_id],
                "damage_hard": rom[DAMAGE_HARD + archetype_id],
                "placements": counts[type_id],
                "scenes": sorted(scenes[type_id]),
            }
            rows.append(row)
            agg = aggregate[archetype_id]
            agg["types"].append(type_id)
            agg["placements"] += counts[type_id]
            agg["scenes"].update(scenes[type_id])

    # Known retail families recovered by the reachable VM scan.
    assert {row["archetype_id"] for row in rows} == {8, 166, 176, 177, 178}
    # IDs 176/177/178 deliberately share one animation descriptor while retaining
    # independently indexed archetype/stat IDs.
    assert u32(rom, ARCHETYPE_TABLE + 176 * 4) == 0x001008CE
    assert u32(rom, ARCHETYPE_TABLE + 177 * 4) == 0x001008CE
    assert u32(rom, ARCHETYPE_TABLE + 178 * 4) == 0x001008CE
    # Player archetype 0xBF has 23 HP, matching the health-pickup cap logic.
    assert rom[HP_NORMAL + 0xBF] == 0x17
    assert rom[HP_HARD + 0xBF] == 0x17

    families = []
    for archetype_id, agg in sorted(aggregate.items()):
        descriptor = u32(rom, ARCHETYPE_TABLE + archetype_id * 4)
        families.append({
            "archetype_id": archetype_id,
            "animation_descriptor": f"0x{descriptor:06X}",
            "type_ids": sorted(agg["types"]),
            "placements": agg["placements"],
            "scenes": sorted(agg["scenes"]),
            "hp_normal": rom[HP_NORMAL + archetype_id],
            "hp_hard": rom[HP_HARD + archetype_id],
            "damage_normal": rom[DAMAGE_NORMAL + archetype_id],
            "damage_hard": rom[DAMAGE_HARD + archetype_id],
        })

    report = {
        "schema": "truerecall.object_archetypes.v1",
        "base_sha1": digest,
        "confirmed": {
            "archetype_id_field": "object+0x2A",
            "animation_descriptor_field": "object+0x2C",
            "archetype_master_table": f"0x{ARCHETYPE_TABLE:06X}",
            "archetype_setter": f"0x{ARCHETYPE_SETTER:06X}",
            "vm_archetype_native": f"0x{VM_ARCHETYPE_NATIVE:06X}",
            "hp_field": "object+0x6C",
            "damage_field": "object+0x6E",
            "difficulty_word": "FFFFFC4A",
            "player_archetype_id": 191,
            "player_hp": 23,
        },
        "families": families,
        "type_assignments": rows,
        "notes": {
            "archetype_vs_visual": "object+0x2A is broader than a pure visual ID: it selects the animation descriptor and also indexes difficulty-dependent HP/damage tables; multiple IDs may share one animation descriptor",
            "coverage": "Only constant archetype assignments reached through VM native 0x2436 are emitted; absence does not mean a type lacks an archetype at runtime."
        }
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
