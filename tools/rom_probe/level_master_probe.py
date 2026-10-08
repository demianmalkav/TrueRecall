#!/usr/bin/env python3
"""Recover and validate the True Lies master gameplay-scene resource table.

Hash-locked to the canonical True Lies (World) ROM. Emits structural metadata
only; no ROM or extracted copyrighted art is stored in the repository.
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
        v = (current >> 7) & 1
        current = (current << 1) & 0xFF
        bits_left -= 1
        return v

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


def plane_descriptor(data: bytes, desc: int) -> dict:
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


def graphics_descriptor(data: bytes, desc: int) -> dict:
    if desc == 0:
        return {"descriptor": "0x000000", "shared_from_previous_plane": True}
    graphics_lz = u32(data, desc)
    secondary = u32(data, desc + 4)
    aux = u32(data, desc + 8)
    graphics = lzbeam_decode(data, graphics_lz)
    assert len(graphics) % 32 == 0
    return {
        "descriptor": f"0x{desc:06X}",
        "lz": f"0x{graphics_lz:06X}",
        "decoded_bytes": len(graphics),
        "tiles_8x8": len(graphics) // 32,
        "secondary": f"0x{secondary:08X}",
        "secondary_mode": "direct/raw" if secondary & 0x80000000 else "decoded/copied",
        "secondary_pointer_without_flag": f"0x{secondary & 0x7FFFFFFF:08X}",
        "aux": f"0x{aux:06X}",
    }


def plane_block(data: bytes, off: int) -> dict:
    gfx_desc = u32(data, off)
    map_desc = u32(data, off + 4)
    vram_offset = u16(data, off + 8)
    name_table_base = u16(data, off + 10)
    return {
        "record_offset": f"0x{off:06X}",
        "graphics": graphics_descriptor(data, gfx_desc),
        "map": plane_descriptor(data, map_desc),
        "vram_offset": f"0x{vram_offset:04X}",
        "name_table_base": f"0x{name_table_base:04X}",
    }


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
        flags = u16(data, record)
        palette0 = u32(data, record + 0x02)
        palette1 = u32(data, record + 0x06)
        object_stream_desc = u32(data, record + 0x0A)
        collision_ptr = u32(data, record + 0x0E)
        collision_mode = u16(data, record + 0x12)
        primary_plane_state = u16(data, record + 0x14)
        assert flags == 3
        assert palette0 == palette1
        cram = [u16(data, palette0 + i * 2) for i in range(64)]
        assert all((color & ~0x0EEE) == 0 for color in cram)

        first = plane_block(data, record + 0x16)
        second = plane_block(data, record + 0x22)
        assert first["name_table_base"] == "0xC000"
        assert second["name_table_base"] == "0xE000"
        assert first["vram_offset"] == "0x0000"
        assert second["vram_offset"] == "0x0000"
        assert u32(data, record + 0x22) == 0  # second plane shares first plane graphics in current retail table

        records.append({
            "index": index,
            "record": f"0x{record:06X}",
            "flags": f"0x{flags:04X}",
            "palette0": f"0x{palette0:06X}",
            "palette1": f"0x{palette1:06X}",
            "object_stream_descriptor": f"0x{object_stream_desc:06X}",
            "collision_geometry": f"0x{collision_ptr:06X}",
            "collision_resource_mode": collision_mode,
            "primary_plane_state_ram": f"0xFFFF{primary_plane_state:04X}",
            "plane_c000": first,
            "plane_e000": second,
        })

    report = {
        "schema": "truerecall.level_master.v2",
        "base_sha1": digest,
        "pointer_table": f"0x{POINTER_TABLE:06X}",
        "record_count": RECORD_COUNT,
        "record_size": RECORD_SIZE,
        "confirmed": {
            "scene_selector": "FC42 indexes this pointer table; selected record is cached in FA1E",
            "flags": "word +0x00; retail value 0x0003 enables both current plane contexts",
            "palette_fields": "longs +0x02/+0x06 point to identical 128-byte Genesis CRAM images in all 19 retail records",
            "object_stream_descriptor": "long +0x0A feeds the spatial object activation/streaming subsystem; exact subrecord semantics are partially decoded",
            "collision_geometry": "long +0x0E is world collision geometry consumed by the generic object+0x38 collision loop",
            "collision_resource_mode": "word +0x12 controls direct versus copied/decoded collision resource handling; retail records currently use 1/direct",
            "primary_plane_state": "word +0x14 is sign-extended as a RAM pointer (typically FA62; one retail scene uses FA2A)",
            "plane_blocks": "two 12-byte plane blocks at +0x16 and +0x22: long graphics descriptor, long map descriptor, word VRAM offset, word name-table base",
            "first_plane_name_table": "0xC000",
            "second_plane_name_table": "0xE000",
            "second_plane_graphics": "zero in all current retail records, causing graphics reuse from the first plane",
            "plane_descriptor": "long LZBeam map pointer + word width + word height",
            "independent_plane_dimensions": "C000 and E000 planes can have different dimensions",
            "graphics_secondary_high_bit": "if bit31 is set, loader clears it and keeps a direct/raw pointer instead of decompressing the secondary graphics resource",
        },
        "partially_resolved": {
            "object_stream_descriptor": "descriptor drives F9B8/F9C2/F9C4 spatial lookup and ultimately generic object allocation; exact placement-record field meanings still being recovered",
            "graphics_aux": "optional third pointer in graphics descriptor; iterated by the graphics-support path, exact entry semantics unresolved",
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
