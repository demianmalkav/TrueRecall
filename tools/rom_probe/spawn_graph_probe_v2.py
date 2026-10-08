#!/usr/bin/env python3
"""Recover the constant object-spawn graph used by True Lies object VM scripts.

The graph records only spawn edges whose child type is structurally constant at
an reachable VM call site, plus two separately proven specialized projectile
natives. It does not infer identity from graphics.
"""
from __future__ import annotations

import argparse, hashlib, json
from collections import Counter, defaultdict, deque
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32
from initial_visual_cfg_probe import decode

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E

SPAWN_NATIVES = {
    0x00205C: "alloc_generic",
    0x00206E: "alloc_linked",
    0x002082: "alloc_linked_offset",
    0x002096: "spawn_generic_init",
    0x0020D8: "spawn_linked_init",
    0x00211C: "spawn_linked_offset_init",
}

SPECIALIZED_PROJECTILES = {0x00DAA4: 175, 0x00DB48: 170}


def placed_info(rom: bytes):
    counts: Counter[int] = Counter(); scenes: dict[int, set[int]] = defaultdict(set)
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4); desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc); pos = u16(rom, desc + 2); decoded = lzbeam_decode(rom, u32(rom, desc + 6))
        run_pos = desc + 0x0A; total = 0; runs = []
        while total < count:
            stride, quantity = rom[run_pos], rom[run_pos + 1]; run_pos += 2
            assert stride in (6, 8) and quantity > 0
            runs.append((stride, quantity)); total += quantity
        assert total == count
        for stride, quantity in runs:
            for _ in range(quantity):
                type_id = u16(decoded, pos) & 0x03FF; counts[type_id] += 1; scenes[type_id].add(scene_index); pos += stride
    return counts, scenes


def constant_word_arg_before_native(rom: bytes, pc: int) -> int | None:
    if pc >= 6 and u16(rom, pc - 6) == 0x001C and u16(rom, pc - 2) == 0x00F0:
        return u16(rom, pc - 4)
    return None


def reachable_native_calls(rom: bytes, type_id: int, max_states: int = 100_000):
    if type_id >= 256 or rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return []
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4); queue = deque([(start, ())]); seen = set(); calls = []
    while queue and len(seen) < max_states:
        pc, stack = queue.popleft(); key = (pc, stack)
        if key in seen or not (0 <= pc < len(rom) - 2): continue
        seen.add(key); ins = decode(rom, pc)
        if ins.get("bad"): continue
        op = ins["op"]
        if op == 0x00E4:
            target = ins.get("operand"); calls.append((pc, target, constant_word_arg_before_native(rom, pc)))
        if op in (0x0000, 0x0004):
            queue.append((ins["target"], stack)); queue.append((ins["end"], stack))
        elif op == 0x0008: queue.append((ins["target"], stack))
        elif op == 0x000C:
            if len(stack) < 16: queue.append((ins["target"], stack + (ins["end"],)))
        elif op == 0x0010:
            if stack: queue.append((stack[-1], stack[:-1]))
        elif op == 0x00AC:
            for _, target in ins["cases"]: queue.append((target, stack))
            queue.append((ins["end"], stack))
        else: queue.append((ins["end"], stack))
    return calls


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("rom", type=Path); ap.add_argument("--json", type=Path); args = ap.parse_args()
    rom = args.rom.read_bytes(); assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest(); assert digest == EXPECTED_SHA1
    assert rom[0x205C:0x206E] == bytes.fromhex("302f00064eb90000f73230084ef9000119f4")
    assert rom[0x206E:0x2082] == bytes.fromhex("302f0006304d4eb90000f7cc30084ef9000119f4")
    assert rom[0x2082:0x2096] == bytes.fromhex("302f0006304d4eb90000f88630084ef9000119f4")
    assert rom[0x2096:0x20C4].startswith(bytes.fromhex("302f00064eb90000f732651a302f00064eb900010102"))
    assert rom[0x20D8:0x211C].startswith(bytes.fromhex("302f0006304d4eb90000f7cc651a302f00064eb900010102"))
    assert rom[0x211C:0x2160].startswith(bytes.fromhex("302f0006304d4eb90000f886651a302f00064eb900010102"))

    counts, scenes = placed_info(rom); assert len(counts) == 128 and sum(counts.values()) == 2449; placed = set(counts)
    edges = []; graph: dict[int, set[int]] = defaultdict(set); callsite_seen = set()
    for parent in range(256):
        for pc, target, arg in reachable_native_calls(rom, parent):
            if target in SPAWN_NATIVES:
                assert arg is not None, (parent, hex(pc), hex(target)); child = arg; key = (parent, child, target, pc)
                if key not in callsite_seen:
                    callsite_seen.add(key); edges.append({"parent_type":parent,"child_type":child,"kind":SPAWN_NATIVES[target],"native":f"0x{target:06X}","callsite":f"0x{pc:06X}","source":"constant_vm_argument"})
                graph[parent].add(child)
            elif target in SPECIALIZED_PROJECTILES:
                child = SPECIALIZED_PROJECTILES[target]; key = (parent, child, target, pc)
                if key not in callsite_seen:
                    callsite_seen.add(key); edges.append({"parent_type":parent,"child_type":child,"kind":"specialized_projectile_spawn","native":f"0x{target:06X}","callsite":f"0x{pc:06X}","source":"fixed_native_child"})
                graph[parent].add(child)

    assert graph[113] == {54, 68}; assert 227 in graph[46]; assert 225 in graph[104]; assert 170 in graph[121]
    assert 170 in graph[5] and 170 in graph[7]; assert 175 in graph[20] and 175 in graph[86]
    children = set().union(*(v for v in graph.values())) if graph else set()
    report = {
        "schema":"truerecall.spawn_graph.v2","base_sha1":digest,"placed_type_count":len(placed),"placed_placement_count":sum(counts.values()),
        "parent_type_count":len(graph),"unique_edge_count":sum(len(v) for v in graph.values()),
        "runtime_only_child_types":sorted(c for c in children if c not in placed),"placed_child_types":sorted(c for c in children if c in placed),
        "wrapper_semantics":{f"0x{k:06X}":v for k,v in SPAWN_NATIVES.items()},"specialized_projectiles":{f"0x{k:06X}":v for k,v in SPECIALIZED_PROJECTILES.items()},
        "parents":[{"parent_type":p,"parent_is_placed":p in placed,"placements":counts.get(p,0),"scenes":sorted(scenes.get(p,set())),"children":sorted(graph[p])} for p in sorted(graph)],
        "callsites":sorted(edges,key=lambda e:(e["parent_type"],e["child_type"],e["callsite"])),
        "policy":"Only constant reachable VM arguments and independently proven fixed-child projectile natives are emitted as edges.",
    }
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True); args.json.write_text(text+"\n",encoding="utf-8")

if __name__ == "__main__": main()
