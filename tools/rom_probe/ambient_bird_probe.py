#!/usr/bin/env python3
"""Recover the non-combat ambient bird behavior of retail type_id 83."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

from vm_disasm import EXPECTED_SIZE, EXPECTED_SHA1, TYPE_SELECTOR_TABLE, TYPE_POINTER_TABLE, reachable, u32

TYPE_ID = 83
X_DISTANCE_NATIVE = 0x002208
Y_DISTANCE_NATIVE = 0x00221A
RANGED_NATIVE = 0x00DB48
SPREAD_NATIVE = 0x00DAA4
HP_NORMAL = 0x07A066
HP_HARD = 0x079F74
DAMAGE_NORMAL = 0x079E82
DAMAGE_HARD = 0x079D90


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest()
    assert digest == EXPECTED_SHA1

    assert rom[TYPE_SELECTOR_TABLE + TYPE_ID] == 1
    start = u32(rom, TYPE_POINTER_TABLE + TYPE_ID * 4)
    insns, _labels, _states = reachable(rom, start, max_states=200000, max_stack=32)
    calls = {ins.get("operand") for ins in insns.values() if ins["op"] == 0x00E4}

    # X-distance wrapper: current object +0x10 vs player(F9F8)+0x10, absolute difference.
    assert rom[0x002208:0x00221A] == bytes.fromhex(
        "304d3278f9f84eb9000018ac4ef9000119f4"
    )
    assert rom[0x0018AC:0x0018BC] == bytes.fromhex(
        "30280010906900106a0244404e75"
    )
    # Y-distance wrapper: current object +0x14 vs player +0x14, absolute difference.
    assert rom[0x00221A:0x00222C] == bytes.fromhex(
        "304d3278f9f84eb9000018d64ef9000119f4"
    )
    assert rom[0x0018D6:0x0018E4] == bytes.fromhex(
        "30280014906900146a0244404e75"
    )

    assert X_DISTANCE_NATIVE in calls and Y_DISTANCE_NATIVE in calls
    assert RANGED_NATIVE not in calls and SPREAD_NATIVE not in calls
    # Both proximity checks compare against 30.
    threshold_count = sum(
        1 for ins in insns.values()
        if ins["op"] == 0x0080 and ins.get("operand") == 0x001E
    )
    assert threshold_count >= 2

    # Script writes explicit motion values and flips between directional variants.
    writes_58 = [pc for pc, ins in insns.items() if ins["op"] == 0x0068 and ins.get("operand") == 0x0058]
    writes_5a = [pc for pc, ins in insns.items() if ins["op"] == 0x0068 and ins.get("operand") == 0x005A]
    assert writes_58 and writes_5a
    assert rom[HP_NORMAL + TYPE_ID] == 1 and rom[HP_HARD + TYPE_ID] == 1
    assert rom[DAMAGE_NORMAL + TYPE_ID] == 0 and rom[DAMAGE_HARD + TYPE_ID] == 0

    report = {
        "schema": "truerecall.ambient_bird.v1",
        "base_sha1": digest,
        "type_id": TYPE_ID,
        "label": "ambient_bird_actor",
        "status": "HIGH_CONFIDENCE",
        "script_start": f"0x{start:06X}",
        "mechanical_evidence": {
            "x_distance_native": "0x002208",
            "y_distance_native": "0x00221A",
            "player_proximity_threshold_each_axis": 30,
            "motion_field_writes": ["object+0x58", "object+0x5A"],
            "standard_ranged_fire": False,
            "spread_fire": False,
            "hp_normal_hard": [1, 1],
            "damage_normal_hard": [0, 0],
        },
        "presentation_evidence": "Initial true-color frame reconstruction is visually an overhead bird; generated sprite images are kept out of Git.",
        "confidence_note": "Behavior alone proves an ambient mobile proximity-reactive actor; the 'bird' identity additionally uses independently reconstructed presentation evidence.",
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
