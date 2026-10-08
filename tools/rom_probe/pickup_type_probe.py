#!/usr/bin/env python3
"""Classify standard True Lies pickup type IDs from their object VM scripts.

The classifications are derived from inventory variables, ownership-mask writes,
player-health access and life-counter access. The probe emits metadata only and
does not dump copyrighted graphics or full scripts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
PICKUP_CALLBACK = 0x009DF8
VM_GRANT_WEAPON_NATIVE = 0x00AEF8


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def script_ranges(rom: bytes) -> dict[int, tuple[int, int]]:
    starts = []
    for type_id in range(139):
        if rom[TYPE_SELECTOR_TABLE + type_id]:
            starts.append((u32(rom, TYPE_POINTER_TABLE + type_id * 4), type_id))
    starts.sort()
    result = {}
    for i, (start, type_id) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else 0x180000
        result[type_id] = (start, end)
    return result


def contains(blob: bytes, raw_hex: str) -> bool:
    return bytes.fromhex(raw_hex.replace(" ", "")) in blob


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest = hashlib.sha1(rom).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    ranges = script_ranges(rom)

    def blob(type_id: int) -> bytes:
        start, end = ranges[type_id]
        return rom[start:end]

    # All standard pickups below are scripted and install the same actor-contact callback.
    for type_id in (51, 52, 53, 54, 61, 62, 68, 69, 70, 71):
        b = blob(type_id)
        assert rom[TYPE_SELECTOR_TABLE + type_id] == 1
        assert contains(b, "008400009df800a8006c0034")

    # Weapon/ammo variables and weapon acquisition semantics.
    # Type 51: flamethrower acquisition: operates on FB7A and calls the VM native
    # that invokes 0x5CF4, whose first operation ORs a selector-derived ownership
    # bit into FB8E.
    assert contains(blob(51), "fffffb7a")
    assert contains(blob(51), "00e40000aef8")
    assert contains(blob(51), "001c000a00f000e40000aef8")

    # Type 52: flamethrower fuel/ammo; same ammo word but no acquisition native.
    assert contains(blob(52), "fffffb7a")
    assert not contains(blob(52), "00e40000aef8")

    # Grenades and mines add to their own ammo words and OR the corresponding
    # weapon-availability bits into FB8E.
    assert contains(blob(53), "0028fffffb760080000300c40058fffffb76")
    assert contains(blob(53), "0028fffffb8e0080000800b40058fffffb8e")
    assert contains(blob(62), "0028fffffb780080000300c40058fffffb78")
    assert contains(blob(62), "0028fffffb8e0080001000b40058fffffb8e")

    # Shotgun ammo versus shotgun acquisition.
    assert contains(blob(68), "fffffb72")
    assert not contains(blob(68), "00e40000aef8")
    assert contains(blob(69), "0028fffffb8e0080000200b000e0")
    assert contains(blob(69), "fffffb72")
    assert contains(blob(69), "001c000200f000e40000aef8")

    # Uzi ammo versus Uzi acquisition.
    assert contains(blob(70), "0028fffffb8e0080000400b000e0")
    assert contains(blob(70), "fffffb74")
    assert contains(blob(70), "001c000400f000e40000aef8")
    assert contains(blob(71), "fffffb74")
    assert not contains(blob(71), "00e40000aef8")

    # Extra life: reads FB8A, caps against 9, increments by one and stores back.
    assert contains(blob(61), "0028fffffb8a0080000900a0")
    assert contains(blob(61), "0028fffffb8a0080000100c40058fffffb8a")

    # Health: dynamically resolves the player-world-object pointer from F9F8,
    # adds field offset +0x6C, reads that word, compares against 0x17 and later
    # writes through the computed address. This ties player object+0x6C to health.
    assert contains(blob(54), "0080006c0100002cf9f8010800c400a80048")
    assert contains(blob(54), "008000170098")
    assert contains(blob(54), "0080000b0090")
    assert contains(blob(54), "001c001701080074")

    # Verify the acquisition native itself: E4 0xAEF8 reaches 0x5CF4; that helper
    # loads a selector-indexed bit and ORs it into FB8E.
    assert rom[VM_GRANT_WEAPON_NATIVE:VM_GRANT_WEAPON_NATIVE + 14] == bytes.fromhex(
        "302f00064eb900005cf44ef90001"
    )
    assert rom[0x005CF4:0x005CFC] == bytes.fromhex("323b00e68378fb8e")

    rows = [
        {"type_id": 54, "label": "health_pickup", "evidence": "player object +0x6C health word"},
        {"type_id": 61, "label": "extra_life_pickup", "evidence": "FB8A life counter"},
        {"type_id": 51, "label": "flamethrower_weapon_pickup", "evidence": "FB7A + grant-weapon native selector 10"},
        {"type_id": 52, "label": "flamethrower_fuel_pickup", "evidence": "FB7A without grant-weapon native"},
        {"type_id": 53, "label": "grenade_pickup", "evidence": "FB76 and FB8E bit 0x08"},
        {"type_id": 62, "label": "mine_pickup", "evidence": "FB78 and FB8E bit 0x10"},
        {"type_id": 68, "label": "shotgun_ammo_pickup", "evidence": "FB72 without grant-weapon native"},
        {"type_id": 69, "label": "shotgun_weapon_pickup", "evidence": "FB72 + FB8E bit 0x02 + grant selector 2"},
        {"type_id": 70, "label": "uzi_weapon_pickup", "evidence": "FB74 + FB8E bit 0x04 + grant selector 4"},
        {"type_id": 71, "label": "uzi_ammo_pickup", "evidence": "FB74 without grant-weapon native"},
    ]

    report = {
        "schema": "truerecall.pickup_types.v1",
        "base_sha1": digest,
        "shared_actor_callback": f"0x{PICKUP_CALLBACK:06X}",
        "types": rows,
        "notes": {
            "health_field": "F9F8-linked world/avatar object +0x6C",
            "weapon_acquisition_native": "0x00AEF8 -> 0x005CF4; ORs selector-derived ownership bit into FB8E",
            "amounts": "This probe intentionally classifies item identity; refill amounts that require branch-path evaluation are left to a later VM control-flow probe."
        }
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
