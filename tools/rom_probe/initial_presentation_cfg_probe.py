#!/usr/bin/env python3
"""Recover initial presentation families for retail True Lies placement types.

The probe follows object-VM control flow conservatively and stops each path at
its first canonical presentation native. It recognizes direct animation calls
and the engine's direction/facing-aware animation-family helpers. Structural
metadata only; no graphics are emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32
from initial_visual_cfg_probe import decode

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
DIR_TABLE = 0x013F32

PRESENTATION_NATIVES = {
    0x001F9A: "direct",
    0x001FF6: "facing_family_set",
    0x00200C: "facing_family_clear",
    0x002022: "direction24_family",
    0x002448: "direction24_family_alt",
}


def canonical_args(rom: bytes, pc: int):
    start = pc - 12
    if start < 0 or u16(rom, start) != 0x001C:
        return None
    arg0 = u16(rom, start + 2)
    if u16(rom, start + 4) != 0x00F0 or u16(rom, start + 6) != 0x001C:
        return None
    arg1 = u16(rom, start + 8)
    if u16(rom, start + 10) != 0x00F0:
        return None
    return arg0, arg1


def first_presentation_calls(rom: bytes, type_id: int, max_states: int = 100_000, max_stack: int = 16):
    if rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return {"direct_code": True, "calls": [], "states": 0, "truncated": False}
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    queue = deque([(start, ())])
    seen = set()
    calls = []
    truncated = False
    while queue:
        if len(seen) >= max_states:
            truncated = True
            break
        pc, stack = queue.popleft()
        key = (pc, stack)
        if key in seen:
            continue
        seen.add(key)
        if not (0 <= pc < len(rom) - 2):
            continue
        ins = decode(rom, pc)
        if ins.get("bad"):
            continue
        op = ins["op"]
        if op == 0x00E4 and ins.get("operand") in PRESENTATION_NATIVES:
            args = canonical_args(rom, pc)
            if args:
                calls.append({"pc": pc, "native": ins["operand"], "mode": PRESENTATION_NATIVES[ins["operand"]], "arg0": args[0], "arg1": args[1]})
                continue
        if op in (0x0000, 0x0004):
            queue.append((ins["target"], stack)); queue.append((ins["end"], stack))
        elif op == 0x0008:
            queue.append((ins["target"], stack))
        elif op == 0x000C:
            if len(stack) < max_stack: queue.append((ins["target"], stack + (ins["end"],)))
            else: truncated = True
        elif op == 0x0010:
            if stack: queue.append((stack[-1], stack[:-1]))
        elif op == 0x00AC:
            for _, target in ins["cases"]: queue.append((target, stack))
            queue.append((ins["end"], stack))
        else:
            queue.append((ins["end"], stack))
    unique=[]; seen_calls=set()
    for call in calls:
        key=(call["pc"],call["native"],call["arg0"],call["arg1"])
        if key not in seen_calls: seen_calls.add(key); unique.append(call)
    return {"direct_code": False, "calls": unique, "states": len(seen), "truncated": truncated}


def placed_counts(rom: bytes) -> Counter[int]:
    counts: Counter[int] = Counter()
    for scene_index in range(SCENE_COUNT):
        scene=u32(rom,SCENE_TABLE+scene_index*4); desc=u32(rom,scene+0x0A)
        count=u16(rom,desc); start=u16(rom,desc+2); source=u32(rom,desc+6); decoded=lzbeam_decode(rom,source)
        run_pos=desc+0x0A; total=0; runs=[]
        while total<count:
            stride,quantity=rom[run_pos],rom[run_pos+1]; run_pos+=2
            assert stride in (6,8) and quantity>0
            runs.append((stride,quantity)); total+=quantity
        pos=start
        for stride,quantity in runs:
            for _ in range(quantity): counts[u16(decoded,pos)&0x03FF]+=1; pos+=stride
    return counts


def facing_selectors(rom: bytes, base: int):
    values=[]
    for facing in range(8):
        off=base+facing*2
        if DIR_TABLE+off+2<=len(rom): values.append(u16(rom,DIR_TABLE+off))
    return values


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("--json",type=Path); args=ap.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=EXPECTED_SIZE: raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest=hashlib.sha1(rom).hexdigest()
    if digest!=EXPECTED_SHA1: raise SystemExit(f"wrong base ROM SHA-1: {digest}")
    counts=placed_counts(rom); rows=[]; coverage=Counter(); resolved_placements=0
    for type_id,placements in sorted(counts.items()):
        result=first_presentation_calls(rom,type_id); calls=[]
        for call in result["calls"]:
            row=dict(call)
            if call["mode"].startswith("facing_family"):
                row["selectors_8way"]=[f"0x{x:04X}" for x in facing_selectors(rom,call["arg0"])]
            calls.append(row)
        families=sorted({(c["mode"],c["arg0"]) for c in result["calls"]})
        if result["direct_code"]: classification="direct_code"
        elif result["truncated"]: classification="truncated"
        elif not calls: classification="no_initial_presentation_native"
        elif len(families)==1: classification="unique_presentation_family"
        else: classification="branch_variants"
        coverage[classification]+=1
        if calls: resolved_placements+=placements
        rows.append({"type_id":type_id,"placements":placements,"classification":classification,"initial_archetype_id":type_id,"calls":calls})
    assert len(counts)==128 and sum(counts.values())==2449
    assert coverage==Counter({"unique_presentation_family":106,"branch_variants":14,"no_initial_presentation_native":6,"direct_code":2})
    assert resolved_placements==2427
    report={"schema":"truerecall.initial_presentation_cfg.v1","base_sha1":digest,"method":"CFG with return stack; stop each path at first canonical direct/facing/direction presentation native","presentation_natives":{f"0x{k:06X}":v for k,v in PRESENTATION_NATIVES.items()},"coverage":dict(coverage),"resolved_placements":resolved_placements,"total_placements":sum(counts.values()),"resolved_fraction":resolved_placements/sum(counts.values()),"types":rows}
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True); args.json.write_text(text+"\n",encoding="utf-8")

if __name__=="__main__": main()
