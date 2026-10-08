#!/usr/bin/env python3
"""Static M0.6 player-control probe for True Lies (World), Mega Drive/Genesis.

Hash-locked, stdlib-only and safe to commit: it stores structural metadata, never
copyrighted ROM data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"


def u16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 2], "big")


def words(data: bytes, off: int, count: int) -> list[int]:
    return [u16(data, off + i * 2) for i in range(count)]


def check(data: bytes, off: int, raw: str, label: str) -> None:
    expected = bytes.fromhex(raw)
    actual = data[off:off + len(expected)]
    assert actual == expected, f"{label} mismatch at {off:06X}: {actual.hex()}"


def immediate_ops(data: bytes, addr: int) -> list[dict]:
    names = {0x0078: "ORI.W", 0x0278: "ANDI.W", 0x0A78: "EORI.W", 0x31FC: "MOVE.W_IMM", 0x4278: "CLR.W"}
    out: list[dict] = []
    needle = addr.to_bytes(2, "big")
    pos = 0
    while True:
        hit = data.find(needle, pos)
        if hit < 0:
            break
        start = hit - 4
        if start >= 0 and u16(data, start) in names:
            opcode = u16(data, start)
            rec = {"rom": f"0x{start:06X}", "op": names[opcode]}
            if opcode != 0x4278:
                rec["value"] = f"0x{u16(data, start + 2):04X}"
            out.append(rec)
        pos = hit + 1
    return out


def bit_tests(data: bytes, addr: int) -> list[dict]:
    out: list[dict] = []
    needle = addr.to_bytes(2, "big")
    pos = 0
    while True:
        hit = data.find(b"\x08\x38", pos)
        if hit < 0:
            break
        if hit + 6 <= len(data) and data[hit + 4:hit + 6] == needle:
            out.append({"rom": f"0x{hit:06X}", "bit": u16(data, hit + 2)})
        pos = hit + 2
    return out


def decode_passwords(data: bytes) -> list[str]:
    key = data[0x4C26:0x4C2E]
    labels: list[str] = []
    for i in range(12):
        enc = data[0x4C36 + i * 8:0x4C36 + (i + 1) * 8]
        dec = bytes(a ^ b for a, b in zip(enc, key))
        labels.append(dec[:7].decode("ascii").strip())
    return labels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    sha1 = hashlib.sha1(data).hexdigest()
    if sha1 != EXPECTED_SHA1:
        raise SystemExit(f"Wrong base ROM SHA-1: {sha1}")

    # Controller 1 normalization: previous/current/pressed/held.
    check(data, 0x12B62, "31 F8 F6 EC F6 EA", "copy previous input")
    check(data, 0x12B74,
          "41 F8 F6 EA 31 40 00 02 32 28 00 00 B1 41 34 00 C2 40 31 41 00 04 C4 68 00 00 31 42 00 06",
          "derive current/pressed/held input")

    dpad = words(data, 0x147C4, 16)
    walk = words(data, 0x147E4, 6)
    idle = words(data, 0x147F0, 6)
    assert dpad == [0, 0, 4, 0, 6, 7, 5, 0, 2, 1, 3, 0, 0, 0, 0, 0]
    assert walk == [0x02, 0x12, 0x22, 0x32, 0x32, 0x42]
    assert idle == [0x52, 0x62, 0x72, 0x82, 0x82, 0x92]

    anchors = {
        "action_edge_filter": (0x82DA, "30 38 F6 EE 02 40 50 30"),
        "idle": (0x832A, "42 78 FB 7C"),
        "walk": (0x83A0, "31 FC 00 02 FB 7C"),
        "primary_weapons": (0x845E, "30 38 FB 8C"),
        "roll_fire_weapons": (0x84BA, "30 38 FB 8C"),
        "roll": (0x8600, "30 38 F6 EC 02 40 00 0F"),
        "roll_flag": (0x8614, "00 78 00 01 FB 7E"),
        "roll_fire_test": (0x86B0, "30 38 F6 EC 08 00 00 04"),
        "invulnerability_start": (0x9714, "08 2D 00 05 00 07 67 02 4E 75 31 FC 00 18 FB 90"),
        "kneeling_fire": (0x98BA, "02 78 FF F7 FB 7E"),
        "lock_pose": (0x99D2, "30 38 F6 EC 08 00 00 06"),
        "dpad_facing": (0x9B12, "30 38 F6 EC 02 40 00 0F E3 40"),
        "invulnerability_tick": (0x9CA0, "32 78 F9 F8 3A 78 FB 6E 53 78 FB 90"),
    }
    for label, (off, raw) in anchors.items():
        check(data, off, raw, label)

    # JLLBFR proof chain: encrypted password -> cheat bit -> hidden combo -> overlay -> alt movement.
    passwords = decode_passwords(data)
    assert passwords[8:12] == ["HNDFGD", "JLLBFR", "LTHLWPN", "JHPSSBY"]
    check(data, 0x4A5E, "00 79 00 02 FF FF FB EE", "JLLBFR -> FBEE bit1")
    check(data, 0x842A, "08 39 00 01 FF FF FB EE", "JLLBFR enabled test")
    check(data, 0x8434, "30 38 F6 EC 0C 40 10 10 67 D8", "Z+B hidden combo")
    check(data, 0x8416, "0A 78 00 40 FB 7E", "toggle maniac overlay")
    check(data, 0x832E, "08 38 00 06 FB 7F 67 0A 30 3C 00 F2", "maniac idle anim")
    check(data, 0x83A6, "08 38 00 06 FB 7F 67 06 30 3C 00 F2", "maniac walk anim")
    check(data, 0x9864,
          "08 38 00 06 FB 7F 67 12 30 3C 02 80 32 3C 02 20 4E B9 00 00 9D 8A",
          "maniac movement parameters")

    terminal_refs: list[str] = []
    pattern = bytes.fromhex("2C 07 02 86 00 00 00 63 66 00")
    for off in range(0x8100, 0x9244, 2):
        if data[off:off + len(pattern)] == pattern:
            disp = int.from_bytes(data[off + 10:off + 12], "big", signed=True)
            if off + 10 + disp == 0x9244:
                terminal_refs.append(f"0x{off:06X}")
    assert len(terminal_refs) >= 20

    report = {
        "schema": "truerecall.m06.player_control.v2",
        "base_sha1": sha1,
        "input": {
            "p1": {"previous": "0xFFFFF6EA", "current": "0xFFFFF6EC", "pressed": "0xFFFFF6EE", "held": "0xFFFFF6F0"},
            "p2": {"previous": "0xFFFFF6F2", "current": "0xFFFFF6F4", "pressed": "0xFFFFF6F6", "held": "0xFFFFF6F8"},
            "pressed_formula": "current & (current XOR previous)",
            "held_formula": "current & previous",
            "dpad_mask": "0x000F",
            "B_fire_bit": 4,
            "roll_bit": 5,
            "lock_bit": 6,
            "Z_weapon_cycle_bit": 12,
            "other_weapon_cycle_bit": 14,
        },
        "facing": {"field": "object+0x50", "table": "0x0147C4", "mask_to_facing": dpad, "helper": "0x009B12"},
        "action_word": {
            "ram": "0xFFFFFB7C", "low_byte": "0xFFFFFB7D", "model": "composable action-class bitfield",
            "classes": {"0x0000": "idle", "0x0002": "walk", "0x0004": "normal fire", "0x0008": "special/deployable base", "0x000C": "automatic sustain/recovery", "0x0028": "Uzi/flamethrower active phase", "0x0048": "grenade priming", "0x0001": "unresolved transition"},
            "writes": immediate_ops(data, 0xFB7C), "bit_tests": bit_tests(data, 0xFB7D),
        },
        "overlay_word": {
            "ram": "0xFFFFFB7E", "low_byte": "0xFFFFFB7F",
            "known": {"0x0001": "roll active", "0x0002": "post-roll", "0x0004": "roll-fire/kneeling", "0x0008": "control/update unresolved", "0x0040": "JLLBFR maniac/chainsaw mode", "0x0080": "lock/fire pose latch"},
            "writes": immediate_ops(data, 0xFB7E), "bit_tests": bit_tests(data, 0xFB7F),
        },
        "maniac_mode": {
            "passwords": passwords[8:12], "JLLBFR_index": 9, "enable_flag": "FBEE bit1", "enable_write": "0x004A5E",
            "toggle_combo": "normalized 0x1010 = Z+B", "toggle": "0x008416", "active_overlay": "FB7E bit6 / 0x0040",
            "alternate_animation": "0x00F2", "fast_params": ["0x0280", "0x0220"], "normal_params": ["0x0180", "0x0120"], "movement_region": "0x009864",
            "importance": "retail precedent for alternate player form layered over normal control architecture",
        },
        "roll_fire": {"roll": "0x008600", "secondary_dispatch": "0x0084BA", "kneeling_control": "0x0098BA", "context_flag": "FB7E 0x0004"},
        "lock_strafe": {"input": "F6EC bit6", "pose_latch": "FB7E bit7", "sync_region": "0x009BC0-0x009BE8"},
        "invulnerability": {"start": "0x009714", "tick": "0x009CA0", "timer": "FB90", "blink": "FB92", "object_flag": "object+0x06 bit0x0020", "spawn_duration": 100, "hit_duration": 24, "trigger": "D7 bit13"},
        "terminal_events": {"entry": "0x009244", "mask": "0x63", "bits": [0, 1, 5, 6], "sites": terminal_refs, "bit1_or_FC47bit5": "0x0096B6 no life decrement", "bit5": "0x00944E life loss", "bit0": "0x00960C life loss", "bit6": "default life loss"},
        "animations": {"walk_table": "0x0147E4", "walk_ids": [f"0x{x:04X}" for x in walk], "idle_table": "0x0147F0", "idle_ids": [f"0x{x:04X}" for x in idle], "roll": "0x0142", "kneeling": "0x0172", "maniac": "0x00F2"},
        "object_plus_54": {"classification": "spatial/collision response or positional correction; not control mode", "exact_axis_unit": "unresolved"},
    }

    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
