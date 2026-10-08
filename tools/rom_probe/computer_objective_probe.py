#!/usr/bin/env python3
"""Prove the HQ computer objective and FC4E mission-counter reuse."""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32
from vm_disasm import EXPECTED_SIZE, EXPECTED_SHA1, TYPE_SELECTOR_TABLE, TYPE_POINTER_TABLE, reachable

MESSAGE_TABLE = 0x0063DC
FC4E = 0xFFFFFC4E
COMPUTER_TYPE = 96
CONTROLLER_TYPE = 125
HP_NORMAL = 0x07A066
HP_HARD = 0x079F74
SHOW_MESSAGE = 0x00AF08


def placement_info(rom: bytes):
    counts = Counter()
    scenes = defaultdict(set)
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc)
        pos = u16(rom, desc + 2)
        decoded = lzbeam_decode(rom, u32(rom, desc + 6))
        run_pos = desc + 0x0A
        total = 0
        runs = []
        while total < count:
            stride, quantity = rom[run_pos], rom[run_pos + 1]
            run_pos += 2
            assert stride in (6, 8) and quantity > 0
            runs.append((stride, quantity))
            total += quantity
        assert total == count
        for stride, quantity in runs:
            for _ in range(quantity):
                type_id = u16(decoded, pos) & 0x03FF
                counts[type_id] += 1
                scenes[type_id].add(scene_index)
                pos += stride
    return counts, scenes


def message(rom: bytes, message_id: int) -> str:
    ptr = u16(rom, MESSAGE_TABLE + message_id)
    end = rom.find(b"$", ptr)
    assert end >= ptr
    return rom[ptr:end].decode("latin1").replace(">", " ").replace("<", " ")


def instructions(rom: bytes, type_id: int):
    assert rom[TYPE_SELECTOR_TABLE + type_id] == 1
    start = u32(rom, TYPE_POINTER_TABLE + type_id * 4)
    insns, _labels, _states = reachable(rom, start, max_states=200000, max_stack=32)
    return insns


def abs_refs(insns: dict[int, dict], address: int):
    hits = []
    for pc, ins in insns.items():
        if ins["op"] in (0x0024, 0x0028, 0x0030, 0x0054, 0x0058, 0x0060) and ins.get("operand") == address:
            hits.append(pc)
    return sorted(hits)


def immediate_values(insns: dict[int, dict]):
    return {ins.get("operand") for ins in insns.values() if ins["op"] in (0x001C, 0x0080)}


def native_calls(insns: dict[int, dict]):
    return {ins.get("operand") for ins in insns.values() if ins["op"] == 0x00E4}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest()
    assert digest == EXPECTED_SHA1

    counts, scenes = placement_info(rom)
    assert counts[COMPUTER_TYPE] == 4
    assert scenes[COMPUTER_TYPE] == {5}
    assert counts[CONTROLLER_TYPE] == 1
    assert scenes[CONTROLLER_TYPE] == {5}

    comp = instructions(rom, COMPUTER_TYPE)
    ctl = instructions(rom, CONTROLLER_TYPE)

    # Type 96 initializes the shared mission counter by +2 for each computer.
    assert rom[0x17F890:0x17F8A2] == bytes.fromhex(
        "0028fffffc4e0080000200c40058fffffc4e"
    )
    # Reachable destruction/damage paths decrement that same counter.
    for start, end in ((0x17F922, 0x17F934), (0x17FA04, 0x17FA16), (0x17FA26, 0x17FA38)):
        assert rom[start:end] == bytes.fromhex(
            "0028fffffc4e0080000100c80058fffffc4e"
        )

    comp_fc4e = abs_refs(comp, FC4E)
    ctl_fc4e = abs_refs(ctl, FC4E)
    assert len(comp_fc4e) >= 8
    assert len(ctl_fc4e) >= 8

    # Type 125 owns the mission messaging/state machine for the computer objective.
    assert SHOW_MESSAGE in native_calls(ctl)
    imm = immediate_values(ctl)
    assert 0x003E in imm and 0x0040 in imm
    msg_start = message(rom, 0x3E)
    msg_done = message(rom, 0x40)
    assert "Destroy all of the computers" in msg_start
    assert "destroyed their HQ" in msg_done

    # The visible computer actor is genuinely destructible and difficulty-indexed.
    assert rom[HP_NORMAL + COMPUTER_TYPE] == 30
    assert rom[HP_HARD + COMPUTER_TYPE] == 20

    report = {
        "schema": "truerecall.computer_objective.v1",
        "base_sha1": digest,
        "scene": 5,
        "computer": {
            "type_id": COMPUTER_TYPE,
            "label": "destructible_computer_objective_prop",
            "status": "CONFIRMED",
            "placements": counts[COMPUTER_TYPE],
            "hp_normal": rom[HP_NORMAL + COMPUTER_TYPE],
            "hp_hard": rom[HP_HARD + COMPUTER_TYPE],
            "fc4e_references": [f"0x{x:06X}" for x in comp_fc4e],
            "counter_initialization": "+2 per placed computer",
            "counter_decrements": ["0x17F922", "0x17FA04", "0x17FA26"],
        },
        "controller": {
            "type_id": CONTROLLER_TYPE,
            "label": "computer_destruction_objective_controller",
            "status": "CONFIRMED",
            "placements": counts[CONTROLLER_TYPE],
            "fc4e_references": [f"0x{x:06X}" for x in ctl_fc4e],
            "message_start_id": "0x3E",
            "message_start": msg_start,
            "message_complete_id": "0x40",
            "message_complete": msg_done,
        },
        "fc4e": {
            "architectural_label": "mission-scoped script counter/state",
            "status": "CONFIRMED reusable semantics",
            "reason": "HQ computer actors and their mission controller use FC4E as an objective counter, proving it is not globally a fixed civilian-kill counter.",
        },
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
