#!/usr/bin/env python3
"""Recover semantic identities for True Lies pickup object type IDs.

The probe follows the retail object VM control flow, checks direct inventory RAM
reads/writes, and validates the native weapon-ownership helper. It emits only
structural metadata; no copyrighted graphics or placement coordinates.
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

RAM = {
    "shotgun_ammo":0xFFFFFB72,
    "uzi_ammo":0xFFFFFB74,
    "grenades":0xFFFFFB76,
    "mines":0xFFFFFB78,
    "flamethrower_fuel":0xFFFFFB7A,
    "lives":0xFFFFFB8A,
    "weapon_selected":0xFFFFFB8C,
    "weapon_owned":0xFFFFFB8E,
}


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def bank_target(pc: int, low_word: int) -> int:
    return (pc & 0xFFFF0000) | low_word


def decode(rom: bytes, pc: int) -> dict:
    op = u16(rom, pc)
    p = pc + 2
    if op in (0x0000,0x0004,0x0008):
        low = u16(rom, p); p += 2
        return {"pc":pc,"op":op,"end":p,"target":bank_target(p, low)}
    if op == 0x000C:
        target = u32(rom, p); p += 4
        return {"pc":pc,"op":op,"end":p,"target":target}
    if op == 0x0010:
        return {"pc":pc,"op":op,"end":p}
    if op == 0x00AC:
        count = u16(rom, p); p += 2
        cases = []
        for _ in range(count):
            value = u16(rom, p)
            target = bank_target(p + 4, u16(rom, p + 2))
            p += 4
            cases.append((value,target))
        return {"pc":pc,"op":op,"end":p,"cases":cases}
    if op not in OPERAND_BYTES:
        return {"pc":pc,"op":op,"bad":True}
    size = OPERAND_BYTES[op]
    raw = rom[p:p+size]
    p += size
    return {"pc":pc,"op":op,"end":p,"operand":int.from_bytes(raw,"big") if size else None}


def reachable_instructions(rom: bytes, type_id: int) -> list[dict]:
    assert rom[TYPE_SELECTOR_TABLE + type_id] == 1
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    queue = deque([(start,())])
    seen = set()
    instructions = {}
    while queue and len(seen) < 20000:
        pc, stack = queue.popleft()
        key = (pc,stack)
        if key in seen:
            continue
        seen.add(key)
        ins = decode(rom,pc)
        instructions[pc] = ins
        assert not ins.get("bad"), f"bad VM opcode type={type_id} pc=0x{pc:06X}"
        op = ins["op"]
        if op in (0x0000,0x0004):
            queue.append((ins["target"],stack)); queue.append((ins["end"],stack))
        elif op == 0x0008:
            queue.append((ins["target"],stack))
        elif op == 0x000C:
            if len(stack) < 16:
                queue.append((ins["target"],stack+(ins["end"],)))
        elif op == 0x0010:
            if stack:
                queue.append((stack[-1],stack[:-1]))
        elif op == 0x00AC:
            for _,target in ins["cases"]:
                queue.append((target,stack))
            queue.append((ins["end"],stack))
        else:
            queue.append((ins["end"],stack))
    return sorted(instructions.values(), key=lambda row: row["pc"])


def normalize_address(op: int, operand: int | None) -> int | None:
    if operand is None:
        return None
    if op in (0x0024,0x0028,0x0030,0x0054,0x0058,0x0060):
        return operand
    if op in (0x002C,0x005C):
        return 0xFFFF0000 | operand
    return None


def inventory_refs(instructions: list[dict]) -> dict[str,list[str]]:
    out = {name:[] for name in RAM}
    for ins in instructions:
        address = normalize_address(ins["op"], ins.get("operand"))
        for name,target in RAM.items():
            if address == target:
                out[name].append(f"0x{ins['pc']:06X}")
    return {name:hits for name,hits in out.items() if hits}


def placed_counts(rom: bytes) -> Counter[int]:
    counts: Counter[int] = Counter()
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc)
        start = u16(rom, desc + 2)
        source = u32(rom, desc + 6)
        decoded = lzbeam_decode(rom, source)
        runs=[]; run_pos=desc+0x0A; total=0
        while total < count:
            stride=rom[run_pos]; quantity=rom[run_pos+1]; run_pos += 2
            assert stride in (6,8) and quantity > 0
            runs.append((stride,quantity)); total += quantity
        pos=start
        for stride,quantity in runs:
            for _ in range(quantity):
                counts[u16(decoded,pos)&0x03FF] += 1
                pos += stride
    return counts


def has_pattern(rom: bytes, type_id: int, pattern: bytes) -> bool:
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    # Pickup scripts are compact; a 0x400-byte search window stays inside the
    # contiguous script area while avoiding dependence on type-ID pointer order.
    return rom.find(pattern, start, min(start + 0x400, len(rom))) >= 0


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--json",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    assert len(rom)==EXPECTED_SIZE
    digest=hashlib.sha1(rom).hexdigest()
    assert digest==EXPECTED_SHA1

    # Native wrapper at 0xAEF8 forwards one word argument to 0x5CF4.
    assert rom[0x00AEF8:0x00AF08] == bytes.fromhex("302f00064eb900005cf44ef9000119f4")
    # 0x5CF4 loads a weapon-bit table and ORs it into FB8E. Table values for
    # selector offsets 0,2,4,6,8,10 are 1,2,4,8,0x10,0x20.
    assert rom[0x005CDC:0x005CE8] == bytes.fromhex("000100020004000800100020")
    assert rom[0x005CF4:0x005CFC] == bytes.fromhex("323b00e68378fb8e")

    counts=placed_counts(rom)
    evidence={}
    for type_id in (51,52,53,54,61,62,68,69,70,71):
        instructions=reachable_instructions(rom,type_id)
        evidence[type_id]={"placements":counts[type_id],"inventory_refs":inventory_refs(instructions)}

    # Weapon/ammo pairs.
    assert "shotgun_ammo" in evidence[69]["inventory_refs"] and "weapon_owned" in evidence[69]["inventory_refs"]
    assert "shotgun_ammo" in evidence[68]["inventory_refs"] and "weapon_owned" not in evidence[68]["inventory_refs"]
    assert "uzi_ammo" in evidence[70]["inventory_refs"] and "weapon_owned" in evidence[70]["inventory_refs"]
    assert "uzi_ammo" in evidence[71]["inventory_refs"] and "weapon_owned" not in evidence[71]["inventory_refs"]
    assert has_pattern(rom,69,bytes.fromhex("001c000200f000e40000aef8"))
    assert has_pattern(rom,70,bytes.fromhex("001c000400f000e40000aef8"))

    # Grenade and mine pickups increase ammo and explicitly set ownership bits.
    assert set(("grenades","weapon_owned")) <= set(evidence[53]["inventory_refs"])
    assert set(("mines","weapon_owned")) <= set(evidence[62]["inventory_refs"])

    # Flamethrower weapon grants ownership through the generic helper; fuel does not.
    assert "flamethrower_fuel" in evidence[51]["inventory_refs"]
    assert has_pattern(rom,51,bytes.fromhex("001c000a00f000e40000aef8"))
    assert "flamethrower_fuel" in evidence[52]["inventory_refs"]
    assert not has_pattern(rom,52,bytes.fromhex("0000aef8"))

    # Extra life directly increments FB8A by one. Type 54 targets player+0x6C;
    # the damage callback at 0x371A reads/subtracts/writes that same health field.
    assert "lives" in evidence[61]["inventory_refs"]
    assert rom[0x00371A:0x00373E] == bytes.fromhex("302a006c6708906d006e67026412304a322800306708324100690040000670003540006c")
    health_instructions=reachable_instructions(rom,54)
    assert any(i["op"]==0x002C and i.get("operand")==0xF9F8 for i in health_instructions)
    assert any(i["op"]==0x0048 for i in health_instructions)
    assert any(i["op"]==0x0080 and i.get("operand")==0x0017 for i in health_instructions)
    assert any(i["op"]==0x0080 and i.get("operand")==0x000C for i in health_instructions)

    labels=[
        {"type_id":69,"name":"shotgun_weapon_pickup","status":"CONFIRMED","effect":"grants shotgun ownership and adds 5 shells up to 99"},
        {"type_id":68,"name":"shotgun_ammo_pickup","status":"CONFIRMED","effect":"adds 25 or 30 shells (mode-dependent) up to 99"},
        {"type_id":70,"name":"uzi_weapon_pickup","status":"CONFIRMED","effect":"grants Uzi ownership and adds 15 rounds up to 999"},
        {"type_id":71,"name":"uzi_ammo_pickup","status":"CONFIRMED","effect":"adds 50 or 70 rounds (mode-dependent) up to 999"},
        {"type_id":53,"name":"grenade_pickup","status":"CONFIRMED","effect":"adds 3 grenades up to 9 and sets ownership bit 0x08"},
        {"type_id":62,"name":"mine_pickup","status":"CONFIRMED","effect":"adds 3 mines up to 9 and sets ownership bit 0x10"},
        {"type_id":51,"name":"flamethrower_weapon_pickup","status":"CONFIRMED","effect":"grants flamethrower ownership bit 0x20 and adds 30 fuel up to 99"},
        {"type_id":52,"name":"flamethrower_fuel_pickup","status":"CONFIRMED","effect":"adds 50 fuel up to 99"},
        {"type_id":61,"name":"extra_life_pickup","status":"CONFIRMED","effect":"increments lives by 1 while current lives <= 9 (effective cap 10)"},
        {"type_id":54,"name":"health_pickup","status":"CONFIRMED","effect":"restores player health field +0x6C by 12 when below 11, otherwise sets it to max 23"},
    ]
    for row in labels:
        row["placements"]=counts[row["type_id"]]
        row["evidence"]=evidence[row["type_id"]]

    report={
        "schema":"truerecall.object_pickups.v1",
        "base_sha1":digest,
        "confirmed_labels":labels,
        "native_weapon_grant":{"vm_wrapper":"0x00AEF8","native":"0x005CF4","ownership_ram":"FFFFFB8E","bit_table":[1,2,4,8,16,32]},
        "health_field":{"player_object_offset":"0x006C","damage_path":"0x00371A-0x00373D","maximum":23},
    }
    text=json.dumps(report,indent=2,sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(text+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
