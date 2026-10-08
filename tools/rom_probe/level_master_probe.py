#!/usr/bin/env python3
"""Recover and validate the True Lies master gameplay-scene resource table.

The probe is locked to the canonical True Lies (World) ROM. It emits metadata
only: pointers, dimensions and validated structural facts. No extracted art is
stored in the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
POINTER_TABLE = 0x013B4A
RECORD_COUNT = 19
RECORD_SIZE = 0x2E


def u16(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 2], "big")


def u32(data: bytes, off: int) -> int:
    return int.from_bytes(data[off:off + 4], "big")


def lzbeam_decode(data: bytes, off: int) -> bytes:
    out_len = u16(data, off)
    command_offset = u16(data, off + 2)
    read_pos = off + 4
    command_pos = off + command_offset + 2
    bits_left = 0
    current = 0
    out = bytearray()

    if out_len <= 0 or command_offset < 4:
        raise ValueError(f"invalid LZBeam header at 0x{off:06X}")

    def bit() -> int:
        nonlocal command_pos, bits_left, current
        if bits_left == 0:
            current = data[command_pos]
            command_pos += 1
            bits_left = 8
        value = (current >> 7) & 1
        current = (current << 1) & 0xFF
        bits_left -= 1
        return value

    def bits(count: int) -> int:
        value = 0
        for _ in range(count):
            value = (value << 1) | bit()
        return value

    def count() -> int:
        value = 1
        while bit() == 0:
            value = (value << 1) | bit()
        return value

    literal_count = count()
    out.extend(data[read_pos:read_pos + literal_count])
    read_pos += literal_count

    while len(out) < out_len:
        written = len(out)
        index_bits = written.bit_length() if written < 256 else 8 + (written >> 8).bit_length()
        source = bits(index_bits)
        copy_count = count() + 2
        if source >= len(out):
            raise ValueError(f"bad LZBeam backref at 0x{off:06X}")
        for i in range(copy_count):
            out.append(out[source + i])
            if len(out) >= out_len:
                break
        if len(out) < out_len and bit() == 0:
            literal_count = count()
            out.extend(data[read_pos:read_pos + literal_count])
            read_pos += literal_count

    return bytes(out[:out_len])


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

    record_ptrs = [u32(data, POINTER_TABLE + i * 4) for i in range(RECORD_COUNT)]
    assert u32(data, POINTER_TABLE + RECORD_COUNT * 4) == 0
    assert all(record_ptrs[i + 1] - record_ptrs[i] == RECORD_SIZE for i in range(RECORD_COUNT - 1))

    records = []
    for index, record in enumerate(record_ptrs):
        header = u16(data, record)
        fields = [u32(data, record + 2 + i * 4) for i in range(11)]
        assert header == 3

        palette0, palette1 = fields[0], fields[1]
        assert palette0 == palette1
        cram = [u16(data, palette0 + i * 2) for i in range(64)]
        assert all((color & ~0x0EEE) == 0 for color in cram)

        graphics_descriptor = fields[5]
        graphics_lz = u32(data, graphics_descriptor)
        graphics_secondary = u32(data, graphics_descriptor + 4)
        graphics_aux = u32(data, graphics_descriptor + 8)
        graphics = lzbeam_decode(data, graphics_lz)
        assert len(graphics) % 32 == 0

        plane_c_descriptor = fields[6]
        plane_e_descriptor = fields[9]
        assert fields[7] == 0xC000
        assert fields[8] == 0
        assert fields[10] == 0xE000

        def plane(desc: int) -> dict:
            map_lz = u32(data, desc)
            width = u16(data, desc + 4)
            height = u16(data, desc + 6)
            decoded = lzbeam_decode(data, map_lz)
            assert len(decoded) == width * height * 2
            return {
                "descriptor": f"0x{desc:06X}",
                "map_lz": f"0x{map_lz:06X}",
                "width": width,
                "height": height,
                "decoded_bytes": len(decoded),
            }

        records.append({
            "index": index,
            "record": f"0x{record:06X}",
            "header_word": header,
            "palette": f"0x{palette0:06X}",
            "aux_l2": f"0x{fields[2]:06X}",
            "aux_l3": f"0x{fields[3]:06X}",
            "aux_l4": f"0x{fields[4]:06X}",
            "graphics": {
                "descriptor": f"0x{graphics_descriptor:06X}",
                "lz": f"0x{graphics_lz:06X}",
                "decoded_bytes": len(graphics),
                "tiles_8x8": len(graphics) // 32,
                "secondary": f"0x{graphics_secondary:08X}",
                "aux": f"0x{graphics_aux:06X}",
            },
            "plane_c000": plane(plane_c_descriptor),
            "plane_e000": plane(plane_e_descriptor),
        })

    report = {
        "schema": "truerecall.level_master.v1",
        "base_sha1": digest,
        "pointer_table": f"0x{POINTER_TABLE:06X}",
        "record_count": RECORD_COUNT,
        "record_size": RECORD_SIZE,
        "confirmed": {
            "palette_fields": "record fields L0/L1 are identical 128-byte Genesis CRAM images",
            "graphics_field": "record L5 points to a 3-long graphics/resource descriptor; first long is an LZBeam tile resource",
            "plane_c_field": "record L6 points to a map descriptor loaded for VRAM base 0xC000 (record L7)",
            "plane_e_field": "record L9 points to a map descriptor loaded for VRAM base 0xE000 (record L10)",
            "plane_descriptor": "long LZBeam map pointer + word width + word height",
            "independent_plane_dimensions": "the C000 and E000 planes can have different widths/heights",
        },
        "unresolved": {
            "L2": "auxiliary scene resource; often LZBeam-decodable, exact consumer/semantics unresolved",
            "L3": "auxiliary raw scene resource, exact consumer/semantics unresolved",
            "L4": "shared/alternate auxiliary pointer, exact semantics unresolved",
            "graphics_secondary": "second graphics-descriptor pointer; high bit is frequently set and exact semantics remain unresolved",
            "graphics_aux": "third graphics-descriptor pointer; optional and exact semantics remain unresolved",
        },
        "records": records,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
