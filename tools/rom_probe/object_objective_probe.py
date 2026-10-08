#!/usr/bin/env python3
"""Recover objective/key semantics from reachable True Lies object-VM code.

The probe traverses the script CFG rather than scanning arbitrary byte windows.
It validates FC54 mission-flag access and the game's own FC06/message-table path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
MESSAGE_TABLE = 0x0063DC
FC54 = 0xFFFFFC54

OPERAND_BYTES = {
    0x0014:2,0x0018:2,0x001C:2,0x0020:4,0x0024:4,0x0028:4,0x002C:2,0x0030:4,
    0x0034:2,0x0038:2,0x003C:2,0x0040:2,0x0044:0,0x0048:0,0x004C:0,0x0050:0,
    0x0054:4,0x0058:4,0x005C:2,0x0060:4,0x0064:2,0x0068:2,0x006C:2,
    0x0070:0,0x0074:0,0x0078:0,0x007C:0,0x0080:2,0x0084:4,0x0088:0,0x008C:0,
    0x0090:0,0x0094:0,0x0098:0,0x009C:0,0x00A0:0,0x00A4:0,0x00A8:0,
    0x00B0:0,0x00B4:0,0x00B8:0,0x00BC:0,0x00C0:0,0x00C4:0,0x00C8:0,0x00CC:0,
    0x00D0:0,0x00D4:0,0x00D8:0,0x00DC:0,0x00E0:0,0x00E4:4,0x00E8:0,0x00EC:2,
    0x00F0:0,0x00F4:0,0x00F8:0,0x00FC:0,0x0100:0,0x0104:0,0x0108:0,0x010C:0,
    0x0110:0,0x0114:0,0x0118:0,0x011C:0,
}


def bank_target(pc: int, low_word: int) -> int:
    return (pc & 0xFFFF0000) | low_word


def decode(rom: bytes, pc: int) -> dict:
    op = u16(rom, pc)
    p = pc + 2
    if op in (0x0000, 0x0004, 0x0008):
        low = u16(rom, p); p += 2
        return {"pc":pc, "op":op, "end":p, "target":bank_target(p, low)}
    if op == 0x000C:
        target = u32(rom, p); p += 4
        return {"pc":pc, "op":op, "end":p, "target":target}
    if op == 0x0010:
        return {"pc":pc, "op":op, "end":p}
    if op == 0x00AC:
        count = u16(rom, p); p += 2
        cases = []
        for _ in range(count):
            value = u16(rom, p)
            target = bank_target(p + 4, u16(rom, p + 2))
            p += 4
            cases.append((value, target))
        return {"pc":pc, "op":op, "end":p, "cases":cases}
    if op not in OPERAND_BYTES:
        return {"pc":pc, "op":op, "bad":True}
    size = OPERAND_BYTES[op]
    raw = rom[p:p + size]
    p += size
    return {"pc":pc, "op":op, "end":p, "operand":int.from_bytes(raw, "big") if size else None}


def reachable_instructions(rom: bytes, type_id: int) -> list[dict]:
    assert rom[TYPE_SELECTOR_TABLE + type_id] == 1
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    queue = deque([(start, ())])
    seen = set()
    instructions = {}
    while queue and len(seen) < 20_000:
        pc, stack = queue.popleft()
        key = (pc, stack)
        if key in seen:
            continue
        seen.add(key)
        ins = decode(rom, pc)
        assert not ins.get("bad"), (type_id, hex(pc), hex(ins["op"]))
        instructions[pc] = ins
        op = ins["op"]
        if op in (0x0000, 0x0004):
            queue.append((ins["target"], stack))
            queue.append((ins["end"], stack))
        elif op == 0x0008:
            queue.append((ins["target"], stack))
        elif op == 0x000C:
            if len(stack) < 16:
                queue.append((ins["target"], stack + (ins["end"],)))
        elif op == 0x0010:
            if stack:
                queue.append((stack[-1], stack[:-1]))
        elif op == 0x00AC:
            for _, target in ins["cases"]:
                queue.append((target, stack))
            queue.append((ins["end"], stack))
        else:
            queue.append((ins["end"], stack))
    return list(instructions.values())


def placed_by_scene(rom: bytes) -> tuple[Counter[int], dict[int, list[int]]]:
    counts: Counter[int] = Counter()
    scenes: dict[int, list[int]] = {}
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
            assert stride in (6, 8) and quantity > 0
            runs.append((stride, quantity))
            total += quantity
        pos = start
        for stride, quantity in runs:
            for _ in range(quantity):
                type_id = u16(decoded, pos) & 0x03FF
                counts[type_id] += 1
                scenes.setdefault(type_id, []).append(scene_index)
                pos += stride
    return counts, scenes


def message(rom: bytes, message_id: int) -> str:
    ptr = u16(rom, MESSAGE_TABLE + message_id)
    end = rom.find(b"$", ptr)
    assert end >= ptr
    return rom[ptr:end].decode("latin1").replace(">", " ").replace("<", " ")


def has_fc54_read(instructions: list[dict]) -> bool:
    return any(i["op"] == 0x0028 and i.get("operand") == FC54 for i in instructions)


def has_fc54_write(instructions: list[dict]) -> bool:
    return any(i["op"] == 0x0058 and i.get("operand") == FC54 for i in instructions)


def has_imm(instructions: list[dict], value: int) -> bool:
    return any(i["op"] in (0x001C, 0x0080) and i.get("operand") == value for i in instructions)


def has_native(instructions: list[dict], address: int) -> bool:
    return any(i["op"] == 0x00E4 and i.get("operand") == address for i in instructions)


def item_evidence(rom: bytes, type_id: int, flag: int, message_ids: list[int], setter: bool) -> dict:
    instructions = reachable_instructions(rom, type_id)
    assert has_fc54_read(instructions)
    assert has_imm(instructions, flag)
    if setter:
        assert has_fc54_write(instructions)
        assert any(i["op"] == 0x00B4 for i in instructions)
    else:
        assert any(i["op"] == 0x00B0 for i in instructions)
    assert has_native(instructions, 0x0000AF08)
    for message_id in message_ids:
        assert has_imm(instructions, message_id), (type_id, hex(message_id))
    return {
        "reachable_instructions": len(instructions),
        "fc54_read": True,
        "fc54_write": has_fc54_write(instructions),
        "message_ids": [f"0x{x:02X}" for x in message_ids],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest()
    assert digest == EXPECTED_SHA1

    # FC06 is an even byte offset into the word-pointer table at 0x63DC.
    assert rom[0x00623A:0x006258] == bytes.fromhex(
        "3038fc0641f9000063dc30300000223c000063dc0281ffff000080412240"
    )
    # Mission flags are explicitly reset during mission/scene setup.
    assert rom[0x000FBA:0x000FC0] == bytes.fromhex("4278fc5431fc")

    counts, scenes = placed_by_scene(rom)
    labels = [
        (63, "security_passcard", 0x8000, [0x0A, 0x0C]),
        (58, "gate_key", 0x8000, [0x2C]),
        (60, "subway_lever", 0x4000, [0x3A, 0x3C]),
        (55, "palace_key", 0x0400, [0x56]),
        (56, "catacombs_key", 0x0800, [0x58]),
        (57, "brass_key", 0x1000, [0x5A]),
        (64, "alpha_security_pass", 0x1000, [0x78]),
        (65, "beta_security_pass", 0x2000, [0x7A]),
        (66, "gamma_security_pass", 0x4000, [0x7C]),
        (67, "delta_security_pass", 0x8000, [0x7E]),
    ]
    rows = []
    for type_id, name, bit, message_ids in labels:
        evidence = item_evidence(rom, type_id, bit, message_ids, True)
        rows.append({
            "type_id": type_id,
            "name": name,
            "status": "CONFIRMED",
            "mission_flag": f"0x{bit:04X}",
            "placements": counts[type_id],
            "scenes": sorted(set(scenes.get(type_id, []))),
            "messages": [{"id": f"0x{m:02X}", "text": message(rom, m)} for m in message_ids],
            "evidence": evidence,
        })

    # China reuses one class for three sequential bomb-disarming keys.
    bomb = reachable_instructions(rom, 9)
    assert counts[9] == 3 and sorted(scenes[9]) == [9, 10, 11]
    assert has_fc54_read(bomb) and has_fc54_write(bomb) and has_native(bomb, 0x0000AF08)
    for bit in (0x2000, 0x4000, 0x8000):
        assert has_imm(bomb, bit)
    for message_id in (0x62, 0x64, 0x66):
        assert has_imm(bomb, message_id)
    rows.append({
        "type_id": 9,
        "name": "bomb_disarming_key",
        "status": "CONFIRMED",
        "placements": 3,
        "scenes": [9, 10, 11],
        "progression_flags": ["0x2000", "0x4000", "0x8000"],
        "messages": [{"id": f"0x{m:02X}", "text": message(rom, m)} for m in (0x62, 0x64, 0x66)],
    })

    controllers = [
        (13, "security_passcard_door", 0x8000, [0x04]),
        (16, "palace_gate", 0x0400, [0x5C]),
        (17, "catacombs_gate", 0x0800, [0x5E]),
        (18, "locked_gate_palace_key_profile", 0x0400, [0x60]),
        (77, "alpha_pass_door", 0x1000, [0x70]),
        (78, "beta_pass_door", 0x2000, [0x72]),
        (79, "gamma_pass_door", 0x4000, [0x74]),
        (80, "delta_pass_door", 0x8000, [0x76]),
        (87, "subway_signal_box", 0x4000, [0x34, 0x36, 0x38]),
    ]
    control_rows = []
    for type_id, name, bit, message_ids in controllers:
        evidence = item_evidence(rom, type_id, bit, message_ids, False)
        control_rows.append({
            "type_id": type_id,
            "name": name,
            "status": "CONFIRMED",
            "required_flag": f"0x{bit:04X}",
            "placements": counts[type_id],
            "scenes": sorted(set(scenes.get(type_id, []))),
            "messages": [{"id": f"0x{m:02X}", "text": message(rom, m)} for m in message_ids],
            "evidence": evidence,
        })

    report = {
        "schema": "truerecall.object_objectives.v2",
        "base_sha1": digest,
        "mission_flag_ram": "FFFFFC54",
        "message_offset_ram": "FFFFFC06",
        "message_pointer_table": "0x0063DC",
        "objective_items": rows,
        "gates_and_controllers": control_rows,
        "scene_mapping_evidence": {
            "china": "bomb-disarming-key type 9 appears exactly once in scenes 9, 10 and 11",
            "refinery": "Alpha/Beta/Gamma/Delta pass pickups and corresponding doors occur in scene 13",
        },
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
