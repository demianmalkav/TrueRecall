#!/usr/bin/env python3
"""Validate the True Lies archetype animation-descriptor indirection and frame records.

Structural metadata only; does not export sprites or copyrighted graphics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
ARCHETYPE_TABLE = 0x079906


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def resolve_record(rom: bytes, archetype_id: int, animation_selector: int):
    descriptor = u32(rom, ARCHETYPE_TABLE + archetype_id * 4)
    encoded = u16(rom, descriptor + animation_selector)
    alias_offset = encoded & 0x0FFE
    record_offset = u16(rom, descriptor + alias_offset)
    record = descriptor + record_offset
    flags = rom[record + 0x0E]
    piece_count = rom[record + 0x0F]
    return {
        "archetype_id": archetype_id,
        "descriptor": descriptor,
        "animation_selector": animation_selector,
        "encoded_entry": encoded,
        "alias_offset": alias_offset,
        "record_offset": record_offset,
        "record": record,
        "record_flags": flags,
        "piece_count": piece_count,
        "record_size": 0x10 + piece_count * 4,
        "geometry_words": [u16(rom, record + o) for o in (0x06, 0x08, 0x0A, 0x0C)],
    }


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

    # FDDC proves the descriptor indirection:
    #   A1=object+2C; entry=(A1,D0.W); entry&0x0FFE indexes the descriptor again;
    #   that second word is stored as object+0x20 (current mapping-record offset).
    assert rom[0x00FDEC:0x00FE04] == bytes.fromhex(
        "2268002c3231000031410024300102400ffe317100000020"
    )

    samples = [
        resolve_record(rom, 191, 2),  # player/world avatar
        resolve_record(rom, 176, 2),
        resolve_record(rom, 166, 2),
        resolve_record(rom, 8, 2),
    ]

    expected = {
        191: {"record_offset": 0x0168, "piece_count": 2, "next_offset": 0x0180},
        176: {"record_offset": 0x015E, "piece_count": 1, "next_offset": 0x0172},
        166: {"record_offset": 0x0114, "piece_count": 7, "next_offset": 0x0140},
        8: {"record_offset": 0x00EA, "piece_count": 11, "next_offset": 0x0126},
    }
    for sample in samples:
        exp = expected[sample["archetype_id"]]
        assert sample["record_offset"] == exp["record_offset"]
        assert sample["piece_count"] == exp["piece_count"]
        assert sample["record_offset"] + sample["record_size"] == exp["next_offset"]

    # Geometry consumers around 0x194A use record +0x06/+0x08/+0x0A/+0x0C.
    assert rom[0x00194A:0x00197E] == bytes.fromhex(
        "3028002067302268002cd2c03029000ae24890690006082800030008670248803229000ce2499269000808280004000867024881"
    )

    report_samples = []
    for sample in samples:
        report_samples.append({
            "archetype_id": sample["archetype_id"],
            "descriptor": f"0x{sample['descriptor']:06X}",
            "animation_selector": f"0x{sample['animation_selector']:04X}",
            "encoded_entry": f"0x{sample['encoded_entry']:04X}",
            "alias_offset": f"0x{sample['alias_offset']:04X}",
            "record_offset": f"0x{sample['record_offset']:04X}",
            "record_flags_byte": f"0x{sample['record_flags']:02X}",
            "piece_count": sample["piece_count"],
            "record_size": sample["record_size"],
            "geometry_words": sample["geometry_words"],
        })

    report = {
        "schema": "truerecall.animation_descriptor.v1",
        "base_sha1": digest,
        "confirmed": {
            "descriptor_field": "object+0x2C",
            "current_record_offset_field": "object+0x20",
            "encoded_animation_entry_field": "object+0x24",
            "entry_alias_mask": "0x0FFE",
            "record_header_bytes": 16,
            "piece_entry_bytes": 4,
            "piece_count_byte": "record+0x0F",
            "record_flags_byte": "record+0x0E",
            "geometry_words": ["record+0x06", "record+0x08", "record+0x0A", "record+0x0C"]
        },
        "samples": report_samples,
        "notes": {
            "piece_semantics": "The four-byte pieces are structurally confirmed; exact bit packing of piece position/shape and the second word's tile/mapping semantics remain under study.",
            "header_0_4": "record words +0x00/+0x02/+0x04 remain unresolved and may participate in animation sequencing/timing."
        }
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
