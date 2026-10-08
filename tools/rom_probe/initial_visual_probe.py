#!/usr/bin/env python3
"""Recover conservative initial visual identity for retail placement types.

The generic allocator sets the initial archetype from the type_id before the
object VM script runs. This probe also recovers an initial animation selector
only when a canonical animation call occurs in the straight-line entry prefix
before any VM control-flow split.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
ARCHETYPE_TABLE = 0x079906
VM_ANIMATION_NATIVE = 0x001F9A

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
FLOW = {0x0000,0x0004,0x0008,0x000C,0x0010,0x00AC}


def placed_counts(rom: bytes) -> Counter[int]:
    counts: Counter[int] = Counter()
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc)
        start = u16(rom, desc + 2)
        source = u32(rom, desc + 6)
        decoded = lzbeam_decode(rom, source)
        runs=[]; p=desc+0x0A; total=0
        while total < count:
            stride=rom[p]; quantity=rom[p+1]; p+=2
            assert stride in (6,8) and quantity > 0
            runs.append((stride,quantity)); total += quantity
        pos=start
        for stride,quantity in runs:
            for _ in range(quantity):
                counts[u16(decoded,pos)&0x03FF] += 1
                pos += stride
    return counts


def decode_linear(rom: bytes, pc: int):
    op=u16(rom,pc); p=pc+2
    if op in FLOW:
        return {"pc":pc,"op":op,"flow":True}
    size=OPERAND_BYTES.get(op)
    if size is None:
        return {"pc":pc,"op":op,"bad":True}
    raw=rom[p:p+size]
    return {"pc":pc,"op":op,"operand":int.from_bytes(raw,"big") if size else None,"end":p+size}


def initial_animation_selector(rom: bytes, type_id: int):
    if rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return None,"direct_code"
    pc=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    history=[]
    for _ in range(300):
        ins=decode_linear(rom,pc)
        if ins.get("bad"):
            return None,f"unknown_0x{ins['op']:04X}"
        if ins.get("flow"):
            return None,f"flow_0x{ins['op']:04X}"
        history.append(ins)
        if ins["op"]==0x00E4 and ins.get("operand")==VM_ANIMATION_NATIVE:
            if len(history)>=5 and [x["op"] for x in history[-5:]] == [0x001C,0x00F0,0x001C,0x00F0,0x00E4]:
                return history[-5]["operand"],"linear_prefix"
            return None,"animation_call_noncanonical"
        pc=ins["end"]
    return None,"limit"


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--json",type=Path)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    assert len(rom)==EXPECTED_SIZE
    digest=hashlib.sha1(rom).hexdigest(); assert digest==EXPECTED_SHA1

    # Generic allocator F732 keeps D0=type_id, reads a per-type byte at 0x7A158,
    # then calls F9D4. F9D4 stores D0 into object+0x2A and resolves descriptor
    # through 0x79906, proving initial archetype ID == allocation type_id.
    assert rom[0x00F732:0x00F7AC].startswith(bytes.fromhex("2f003238f9fc670000883041720021410004"))
    assert rom[0x00F794:0x00F7AC] == bytes.fromhex("43f90007a158123100003141000a61000230317c00000008")
    assert rom[0x00F9D4:0x00F9E8] == bytes.fromhex("3140002ad040d04043f900079906227100002149")
    # Placement materializer passes status/type & 0x03FF in D0 into F732.
    assert rom[0x010BCA:0x010BE6] == bytes.fromhex("024003ff0c4000e664303f004eb90000f7326544301f4eb900010102")

    counts=placed_counts(rom)
    rows=[]; reasons=Counter(); resolved_placements=0
    for type_id,count in sorted(counts.items()):
        selector,reason=initial_animation_selector(rom,type_id)
        reasons[reason]+=1
        row={
            "type_id":type_id,
            "placements":count,
            "initial_archetype_id":type_id,
            "initial_animation_descriptor":f"0x{u32(rom,ARCHETYPE_TABLE+type_id*4):06X}",
            "initial_selector":None if selector is None else f"0x{selector:04X}",
            "selector_evidence":reason,
        }
        rows.append(row)
        if selector is not None:
            resolved_placements += count

    assert len(counts)==128 and sum(counts.values())==2449
    resolved_types=sum(1 for row in rows if row["initial_selector"] is not None)
    assert resolved_types==50

    report={
        "schema":"truerecall.initial_visuals.v1",
        "base_sha1":digest,
        "confirmed":{
            "placement_type_to_allocator":"materializer masks placement status/type with 0x03FF and calls F732 with D0=type_id",
            "initial_archetype_rule":"generic allocator F732 calls F9D4 with unchanged D0, so initial object+0x2A archetype ID equals type_id",
            "initial_descriptor_table":"0x079906",
            "later_script_changes":"VM native 0x2436 may replace the archetype later; reachable archetype calls are lifecycle states, not necessarily initial identity"
        },
        "conservative_selector_coverage":{
            "placed_type_ids":len(counts),
            "resolved_type_ids":resolved_types,
            "total_placements":sum(counts.values()),
            "resolved_placements":resolved_placements,
            "method":"canonical 0x1F9A animation call before first VM control-flow split",
            "stop_reasons":dict(sorted(reasons.items()))
        },
        "types":rows
    }
    text=json.dumps(report,indent=2,sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(text+'\n',encoding='utf-8')


if __name__=="__main__":
    main()
