#!/usr/bin/env python3
"""M0.6B static probe: held input, weapon-cycle direction and linked player objects.

The probe is hash-locked to the canonical True Lies (World) ROM and stores only
small structural signatures/metadata. It does not contain the ROM or extracted assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"


def check(data: bytes, off: int, raw: str, label: str) -> None:
    expected = bytes.fromhex(raw)
    actual = data[off:off + len(expected)]
    if actual != expected:
        raise AssertionError(
            f"{label} mismatch at 0x{off:06X}: expected={expected.hex()} actual={actual.hex()}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    if len(data) != EXPECTED_SIZE:
        raise SystemExit(f"Wrong ROM size: {len(data)}")
    digest = hashlib.sha1(data).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"Wrong base ROM SHA-1: {digest}")

    # Input update: d2=current; AND.W previous,d2; store at +6 => F6F0.
    check(data, 0x012B82, "3400c468000031420006", "F6F0 held-overlap derivation")

    # Weapon cycle: bit12 falls through to +2 loop; bit14 branches to -2 loop.
    check(data, 0x008448, "3038f6ee0800000c66260800000e6620", "weapon-cycle edge dispatch")
    check(data, 0x0084F4, "4278fb7c3438fb8c3038fb8c54420c42000c", "next-weapon +2 loop")
    check(data, 0x008528, "4278fb7c3438fb8c3038fb8c55420c420000", "previous-weapon -2 loop")

    # Linked player-object construction.
    # F9F8 is created from the stage/world object path; the companion is stored in FB6E.
    check(data, 0x0109D0, "31c8f9f84e75", "world/avatar object stored in F9F8")
    check(data, 0x008284, "31c8fb6e4278fb7c", "companion player object stored in FB6E")

    # F8E8 preserves A0/A5 and then makes the newly allocated A0 object current A5.
    check(data, 0x00F8E8, "48e700843a484eb9000104ec", "new object promoted to A5")

    # The player's entity-interaction callback explicitly ignores F9F8: own linked avatar.
    check(data, 0x00356C, "b4f8f9f866024e75", "player proxy ignores linked F9F8 object")

    # Per-frame synchronization loads F9F8 as A1, FB6E as A5 and copies motion proxy->avatar.
    check(data, 0x009B60, "3278f9f83a78fb6e", "load linked avatar and proxy")
    check(data, 0x009BE8, "336d00180018336d001a001a336d00560056", "copy proxy motion to avatar")

    # Position/collision geometry is also copied between the linked representations.
    check(data, 0x009C7A, "3b69001000103b69001200123b69001400143b6900160016", "copy avatar geometry to proxy")

    report = {
        "schema": "truerecall.m06.player_links.v1",
        "base_sha1": digest,
        "milestone": "M0.6B",
        "confirmed": {
            "held_input": {
                "ram": "0xFFFFF6F0",
                "formula": "current & previous",
                "meaning": "controls continuously active across consecutive samples",
            },
            "weapon_cycle": {
                "next_weapon": {"pressed_bit": 12, "selector_delta": "+2", "wrap": "0x000C -> 0x0000"},
                "previous_weapon": {"pressed_bit": 14, "selector_delta": "-2", "wrap": "below 0 -> 0x000C"},
            },
        },
        "high_confidence": {
            "0xFFFFF9F8": "linked world/render avatar entity",
            "0xFFFFFB6E": "player control/collision proxy/companion entity",
            "relationship": "FB6E drives motion/control state while F9F8 is synchronized as the linked world/avatar representation; own-collision is explicitly suppressed",
        },
        "evidence": {
            "F9F8_store": "0x0109D0",
            "FB6E_store": "0x008284",
            "allocator_promotes_new_object_to_A5": "0x00F8E8",
            "self_collision_ignore": "0x00356C",
            "frame_sync_load": "0x009B60",
            "motion_proxy_to_avatar": "0x009BE8",
            "geometry_avatar_to_proxy": "0x009C7A",
        },
        "unresolved": [
            "whether Beam internally called the linked F9F8 representation a sprite/avatar/body object",
            "exact ownership/lifetime ordering between the two linked player objects",
            "full meaning of every synchronization exception bit in FB7C/FB7E",
        ],
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
