#!/usr/bin/env python3
"""Static M0.6 player-control probe for True Lies (World), Mega Drive/Genesis.

The probe is intentionally ROM-hash locked and emits only reproducible facts plus
explicitly-qualified interpretations. It stores no copyrighted ROM data.
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


def assert_bytes(data: bytes, offset: int, raw: str, label: str) -> None:
    expected = bytes.fromhex(raw)
    actual = data[offset:offset + len(expected)]
    assert actual == expected, f"{label} mismatch at {offset:06X}"


def immediate_ops(data: bytes, address: int) -> list[dict]:
    """Collect simple immediate writes to a short absolute RAM address."""
    out: list[dict] = []
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
                rec = {"rom": f"0x{start:06X}", "op": names[opcode]}
                if opcode != 0x4278:
                    rec["value"] = f"0x{u16(data, start + 2):04X}"
                out.append(rec)
        cursor = hit + 1


def bit_tests(data: bytes, address: int) -> list[dict]:
    """Collect BTST #imm,$addr.w uses."""
    out: list[dict] = []
    cursor = 0
    needle = address.to_bytes(2, "big")
    while True:
        hit = data.find(b"\x08\x38", cursor)
        if hit < 0:
            return out
        if hit + 6 <= len(data) and data[hit + 4:hit + 6] == needle:
            out.append({"rom": f"0x{hit:06X}", "bit": u16(data, hit + 2)})
        cursor = hit + 2


def decode_passwords(data: bytes) -> list[str]:
    key = data[0x4C26:0x4C2E]
    result: list[str] = []
    for index in range(12):
        enc = data[0x4C36 + index * 8:0x4C36 + (index + 1) * 8]
        dec = bytes(a ^ b for a, b in zip(enc, key))
        # Last byte is a control byte (0xDF); strip spaces/control for the label.
        result.append(dec[:7].decode("ascii", errors="replace").strip())
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    sha1 = verify(data)

    # Input normalizer: previous/current/new-edge/held for controller 1.
    assert_bytes(data, 0x12B62, "31 F8 F6 EC F6 EA", "copy previous input")
    assert_bytes(
        data,
        0x12B72,
        "41 F8 F6 EA 31 40 00 02 32 28 00 00 B1 41 34 00 C2 40 31 41 00 04 C4 68 00 00 31 42 00 06",
        "derive current/pressed/held input",
    )

    dpad = words(data, 0x147C4, 16)
    walk = words(data, 0x147E4, 6)
    idle = words(data, 0x147F0, 6)
    assert dpad == [0, 0, 4, 0, 6, 7, 5, 0, 2, 1, 3, 0, 0, 0, 0, 0]
    assert walk == [0x02, 0x12, 0x22, 0x32, 0x32, 0x42]
    assert idle == [0x52, 0x62, 0x72, 0x82, 0x82, 0x92]

    signatures = {
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
    for label, (offset, raw) in signatures.items():
        assert_bytes(data, offset, raw, label)

    # Hidden JLLBFR mode proof chain.
    passwords = decode_passwords(data)
    assert passwords[8:12] == ["HNDFGD", "JLLBFR", "LTHLWPN", "JHPSSBY"]
    assert_bytes(data, 0x4A62, "00 79 00 02 FF FF FB EE", "JLLBFR -> FBEE bit1")
    assert_bytes(data, 0x842A, "08 39 00 01 FF FF FB EE", "JLLBFR enabled test")
    assert_bytes(data, 0x8434, "30 38 F6 EC 0C 40 10 10 67 D8", "hidden Z+B combo")
    assert_bytes(data, 0x8416, "0A 78 00 40 FB 7E", "toggle maniac overlay")
    assert_bytes(data, 0x832E, "08 38 00 06 FB 7F 67 0A 30 3C 00 F2", "maniac idle animation")
    assert_bytes(data, 0x83A6, "08 38 00 06 FB 7F 67 06 30 3C 00 F2", "maniac walk animation")
    assert_bytes(
        data,
        0x9864,
        "08 38 00 06 FB 7F 67 12 30 3C 02 80 32 3C 02 20 4E B9 00 00 9D 8A",
        "maniac movement parameters",
    )

    terminal_refs: list[str] = []
    pattern = bytes.fromhex("2C 07 02 86 00 00 00 63 66 00")
    for off in range(0x8100, 0x9244, 2):
        if data[off:off + len(pattern)] != pattern:
            continue
        disp = int.from_bytes(data[off + 10:off + 12], "big", signed=True)
        target = off + 10 + disp
        if target == 0x9244:
            terminal_refs.append(f"0x{off:06X}")
    assert len(terminal_refs) >= 20

    report = {
        "schema": "truerecall.m06.player_control.v2",
        "base_sha1": sha1,
        "input_buffer": {
            "controller_1": {
                "previous": "0xFFFFF6EA",
                "current": "0xFFFFF6EC",
                "pressed_edges": "0xFFFFF6EE",
                "held_previous_and_current": "0xFFFFF6F0",
            },
            "controller_2": {
                "previous": "0xFFFFF6F2",
                "current": "0xFFFFF6F4",
                "pressed_edges": "0xFFFFF6F6",
                "held_previous_and_current": "0xFFFFF6F8",
            },
            "pressed_formula": "current & (current XOR previous)",
            "held_formula": "current & previous",
        },
        "normalized_input": {
            "direction_mask": "0x000F",
            "fire_B_bit": 4,
            "roll_bit": 5,
            "lock_bit": 6,
            "Z_weapon_cycle_bit": 12,
            "other_weapon_cycle_bit": 14,
            "main_action_edge_mask": "0x5030",
        },
        "facing": {
            "field": "object+0x50",
            "table": "0x0147C4",
            "mask_to_facing": dpad,
            "update_helper": "0x009B12",
        },
        "action_word": {
            "address": "0xFFFFFB7C",
            "low_byte": "0xFFFFFB7D",
            "model": "composable action-class bitfield, not an enum",
            "classes": {
                "0x0000": "idle/neutral",
                "0x0002": "walk",
                "0x0004": "normal fire",
                "0x0008": "special/deployable base",
                "0x000C": "special + fire; automatic-weapon sustain/recovery",
                "0x0028": "Uzi/flamethrower active phase",
                "0x0048": "grenade priming/held phase",
                "0x0001": "auxiliary/transition unresolved",
            },
            "writes": immediate_ops(data, 0xFB7C),
            "bit_tests": bit_tests(data, 0xFB7D),
        },
        "overlay_flags": {
            "address": "0xFFFFFB7E",
            "low_byte": "0xFFFFFB7F",
            "model": "overlay/context bitfield",
            "known": {
                "0x0001": "roll active phase (high confidence)",
                "0x0002": "post-roll transition (high confidence)",
                "0x0004": "roll-fire/kneeling context (confirmed)",
                "0x0008": "normal-control/update context; exact label unresolved",
                "0x0040": "JLLBFR maniac/chainsaw alternate-player mode (confirmed chain; external behavior corroborated)",
                "0x0080": "lock/fire pose latch (high confidence)",
            },
            "writes": immediate_ops(data, 0xFB7E),
            "bit_tests": bit_tests(data, 0xFB7F),
        },
        "hidden_maniac_mode": {
            "password_key": "0x004C26",
            "encrypted_password_table": "0x004C36",
            "decoded_special_passwords": passwords[8:12],
            "JLLBFR_password_index": 9,
            "JLLBFR_flag": "FBEE bit 1",
            "enable_flag_write": "0x004A62",
            "toggle_combo_normalized": "0x1010 = Z + B",
            "toggle_routine": "0x008416",
            "active_overlay": "FB7E bit 6 / 0x0040",
            "alternate_animation": "0x00F2",
            "fast_parameters": ["0x0280", "0x0220"],
            "normal_parameters": ["0x0180", "0x0120"],
            "movement_parameter_region": "0x009864",
            "architectural_value": "retail precedent for alternate player form implemented as an overlay over the normal control architecture",
        },
        "invulnerability_overlay": {
            "begin": "0x009714",
            "tick": "0x009CA0",
            "timer": "0xFFFFFB90",
            "blink_cadence": "0xFFFFFB92",
            "object_flag": "object+0x06 bit 0x0020",
            "spawn_duration": 100,
            "nonfatal_event_duration": 24,
            "trigger": "D7 bit 13",
        },
        "terminal_event_dispatch": {
            "entry": "0x009244",
            "mask": "0x00000063",
            "bits": [0, 1, 5, 6],
            "call_sites": terminal_refs,
            "bit1_or_FC47_bit5": "0x0096B6; no lives decrement observed",
            "bit5": "0x00944E; life-loss path",
            "bit0": "0x00960C; life-loss path",
            "remaining_bit6_case": "default life-loss path",
        },
        "lock_strafe": {
            "input": "F6EC bit 6",
            "pose_latch": "FB7E bit 7",
            "sync_region": "0x009BC0-0x009BE8",
        },
        "animations": {
            "walk_table": "0x0147E4",
            "walk_ids": [f"0x{x:04X}" for x in walk],
            "idle_table": "0x0147F0",
            "idle_ids": [f"0x{x:04X}" for x in idle],
            "roll": "0x0142",
            "kneeling_transition": "0x0172",
            "maniac_alternate": "0x00F2",
        },
        "spatial_field": {
            "field": "object+0x54",
            "classification": "collision/spatial response or positional correction; not player control mode",
            "exact_unit_axis": "unresolved",
        },
    }

    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
