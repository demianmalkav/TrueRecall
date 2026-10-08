#!/usr/bin/env python3
"""Static M0.6 player-control probe for True Lies (World), Mega Drive/Genesis.

Requires only Python stdlib. It refuses non-canonical ROMs and emits reproducible
metadata about the normalized input buffer, player action word, overlay flags,
roll-fire, lock/strafe, invulnerability and terminal-event routing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"


def u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def words(data: bytes, offset: int, count: int) -> list[int]:
    return [u16(data, offset + i * 2) for i in range(count)]


def verify(data: bytes) -> str:
    sha1 = hashlib.sha1(data).hexdigest()
    if sha1 != EXPECTED_SHA1:
        raise SystemExit(f"Wrong base ROM SHA-1: {sha1}")
    return sha1


def immediate_ops(data: bytes, address: int) -> list[dict]:
    out = []
    needle = address.to_bytes(2, "big")
    names = {
        0x0078: "ORI.W",
        0x0278: "ANDI.W",
        0x0A78: "EORI.W",
        0x31FC: "MOVE.W_IMM",
        0x4278: "CLR.W",
    }
    cursor = 0
    while True:
        hit = data.find(needle, cursor)
        if hit < 0:
            return out
        start = hit - 4
        if start >= 0:
            opcode = u16(data, start)
            if opcode in names:
                record = {"rom": start, "op": names[opcode]}
                if opcode != 0x4278:
                    record["value"] = u16(data, start + 2)
                out.append(record)
        cursor = hit + 1


def bit_tests(data: bytes, address: int) -> list[dict]:
    out = []
    needle = address.to_bytes(2, "big")
    cursor = 0
    while True:
        hit = data.find(b"\x08\x38", cursor)
        if hit < 0:
            return out
        if hit + 6 <= len(data) and data[hit + 4:hit + 6] == needle:
            out.append({"rom": hit, "bit": u16(data, hit + 2)})
        cursor = hit + 2


def hx(value: int, width: int = 4) -> str:
    return f"0x{value:0{width}X}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    sha1 = verify(data)

    dpad = words(data, 0x147C4, 16)
    assert dpad == [0, 0, 4, 0, 6, 7, 5, 0, 2, 1, 3, 0, 0, 0, 0, 0]
    walk = words(data, 0x147E4, 6)
    idle = words(data, 0x147F0, 6)
    assert walk == [0x02, 0x12, 0x22, 0x32, 0x32, 0x42]
    assert idle == [0x52, 0x62, 0x72, 0x82, 0x82, 0x92]

    signatures = {
        "input_copy_previous": (0x12B62, "31 F8 F6 EC F6 EA"),
        "main_action_edge_filter": (0x82DA, "30 38 F6 EE 02 40 50 30"),
        "normalize_control_flags": (0x8316, "00 78 00 08 FB 7E 02 78 9F FF FB 7E"),
        "idle_action_word": (0x832A, "42 78 FB 7C"),
        "walk_action_word": (0x83A0, "31 FC 00 02 FB 7C"),
        "primary_weapon_dispatch": (0x845E, "30 38 FB 8C"),
        "secondary_roll_fire_dispatch": (0x84BA, "30 38 FB 8C"),
        "roll_entry": (0x8600, "30 38 F6 EC 02 40 00 0F"),
        "roll_active_flag": (0x8614, "00 78 00 01 FB 7E"),
        "roll_fire_held_test": (0x86B0, "30 38 F6 EC 08 00 00 04"),
        "begin_invulnerability": (0x9714, "08 2D 00 05 00 07 67 02 4E 75 31 FC 00 18 FB 90"),
        "kneeling_fire_control": (0x98BA, "02 78 FF F7 FB 7E"),
        "lock_or_fire_pose": (0x99D2, "30 38 F6 EC 08 00 00 06"),
        "dpad_to_facing": (0x9B12, "30 38 F6 EC 02 40 00 0F E3 40"),
        "invulnerability_tick": (0x9CA0, "32 78 F9 F8 3A 78 FB 6E 53 78 FB 90"),
    }
    for name, (offset, raw) in signatures.items():
        expected = bytes.fromhex(raw)
        actual = data[offset:offset + len(expected)]
        assert actual == expected, f"{name} mismatch at {offset:06X}"

    terminal_refs = []
    pattern = bytes.fromhex("2C 07 02 86 00 00 00 63 66 00")
    for off in range(0x8100, 0x9244, 2):
        if data[off:off + len(pattern)] != pattern:
            continue
        disp = int.from_bytes(data[off + 10:off + 12], "big", signed=True)
        target = off + 10 + disp
        if target == 0x9244:
            terminal_refs.append(off)
    assert len(terminal_refs) >= 20

    action_ops = immediate_ops(data, 0xFB7C)
    flag_ops = immediate_ops(data, 0xFB7E)
    action_values = sorted({r["value"] for r in action_ops if r["op"] == "MOVE.W_IMM"})

    report = {
        "base_sha1": sha1,
        "input_buffer": {
            "previous": "0xFFFFF6EA",
            "current": "0xFFFFF6EC",
            "pressed_edges": "0xFFFFF6EE",
            "auxiliary": "0xFFFFF6F0",
            "pressed_edge_formula": "current & (current XOR previous)",
        },
        "normalized_input": {
            "direction_mask": "0x000F",
            "lock_current_bit": 6,
            "fire_edge_bit": 4,
            "roll_edge_bit": 5,
            "weapon_cycle_edge_bits": [12, 14],
            "main_action_edge_mask": "0x5030",
        },
        "facing": {
            "table": "0x0147C4",
            "mask_to_facing": dpad,
            "valid_masks": {
                "0x0": "none", "0x1": "N", "0x2": "S", "0x4": "W",
                "0x5": "NW", "0x6": "SW", "0x8": "E", "0x9": "NE", "0xA": "SE"
            },
            "update_helper": "0x009B12",
        },
        "action_word": {
            "address": "0xFFFFFB7C",
            "low_byte": "0xFFFFFB7D",
            "direct_values": [hx(v) for v in action_values],
            "classes": {
                "0x0000": "idle/neutral",
                "0x0002": "walking",
                "0x0004": "normal weapon fire",
                "0x0008": "special-action base bit",
                "0x000C": "special action + normal fire",
                "0x0028": "special action + 0x20 modifier; Uzi/flamethrower phases",
                "0x0048": "special action + 0x40 modifier; grenade phase",
                "0x0001": "auxiliary/transition; unresolved",
            },
            "writes": action_ops,
            "bit_tests": bit_tests(data, 0xFB7D),
        },
        "overlay_flags": {
            "address": "0xFFFFFB7E",
            "low_byte": "0xFFFFFB7F",
            "known": {
                "0x0001": "roll active phase (high confidence)",
                "0x0002": "post-roll transition (high confidence)",
                "0x0004": "roll-fire/kneeling-fire context (confirmed)",
                "0x0008": "normal-control/update; exact label unresolved",
                "0x0040": "hidden/special visual-control toggle; unresolved",
                "0x0080": "lock/fire pose latch (high confidence)",
            },
            "writes": flag_ops,
            "bit_tests": bit_tests(data, 0xFB7F),
        },
        "invulnerability_overlay": {
            "begin": "0x009714",
            "tick": "0x009CA0",
            "timer": "0xFFFFFB90",
            "blink_cadence": "0xFFFFFB92",
            "object_flag": "object+0x06 bit 0x0020",
            "spawn_duration": 100,
            "nonfatal_event_duration": 24,
            "trigger": "D7 bit 13 in normal/action update loops",
        },
        "terminal_event_dispatch": {
            "entry": "0x009244",
            "mask": "0x00000063",
            "bits": [0, 1, 5, 6],
            "call_sites": [hx(x, 6) for x in terminal_refs],
            "routing": {
                "bit1_or_FC47_bit5": "0x0096B6; no lives decrement observed",
                "bit5": "0x00944E; life-loss path",
                "bit0": "0x00960C; life-loss path",
                "remaining_bit6_case": "default life-loss path",
            },
        },
        "lock_strafe": {
            "input": "F6EC bit 6",
            "pose_latch": "FB7E bit 7",
            "sync_region": "0x009BC0-0x009BE8",
            "model": "overlay: Lock prevents aim/display facing from being resynchronized to locomotion facing",
        },
        "animations": {
            "walk_table": "0x0147E4",
            "walk_ids": [hx(v) for v in walk],
            "idle_table": "0x0147F0",
            "idle_ids": [hx(v) for v in idle],
            "roll": "0x0142",
            "kneeling_fire_transition": "0x0172",
        },
    }

    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
