#!/usr/bin/env python3
"""Export and compile gameplay-scene Genesis CRAM palettes.

Retail True Lies gameplay scenes point scene-record fields +0x02 and +0x06 at the
same raw 128-byte CRAM image (64 words). This module keeps palette authoring
isolated from the M11D scene-source schema so existing canonical-source
fingerprints remain stable until a versioned scene-source migration is ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19
SCENE_RECORD_SIZE = 0x2E
BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 0x200000
DEFAULT_ROM_SIZE = 0x400000
DEFAULT_ALLOCATION_BASE = 0x300000
ROM_END_OFFSET = 0x01A4
CHECKSUM_OFFSET = 0x018E
PALETTE_BYTES = 128
PALETTE_WORDS = 64
CRAM_MASK = 0x0EEE


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, "big")


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def align(value: int, alignment: int = 0x10) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + u16(buf, off)) & 0xFFFF
    return total


def validate_base(raw: bytes) -> None:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")


def scene_address(raw: bytes | bytearray, scene_index: int) -> int:
    if not 0 <= scene_index < SCENE_COUNT:
        raise ValueError(scene_index)
    return u32(raw, SCENE_TABLE + scene_index * 4)


def validate_colors(colors: list[int]) -> list[int]:
    if len(colors) != PALETTE_WORDS:
        raise ValueError(f"palette must contain {PALETTE_WORDS} colors")
    out = []
    for index, value in enumerate(colors):
        if not isinstance(value, int):
            raise TypeError(f"palette color {index} is not an integer")
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"palette color {index} out of word range: {value}")
        if value & ~CRAM_MASK:
            raise ValueError(
                f"palette color {index} is not a canonical Genesis CRAM word: 0x{value:04X}"
            )
        out.append(value)
    return out


def export_scene_palette(raw: bytes, scene_index: int) -> dict[str, Any]:
    validate_base(raw)
    scene = scene_address(raw, scene_index)
    palette0 = u32(raw, scene + 0x02)
    palette1 = u32(raw, scene + 0x06)
    if palette0 != palette1:
        raise ValueError(
            f"scene {scene_index} uses split palette pointers: 0x{palette0:06X} / 0x{palette1:06X}"
        )
    if palette0 + PALETTE_BYTES > len(raw):
        raise ValueError(f"scene {scene_index} palette pointer out of range: 0x{palette0:06X}")

    colors = [u16(raw, palette0 + i * 2) for i in range(PALETTE_WORDS)]
    validate_colors(colors)
    return {
        "schema": "truerecall.scene_palette.v1",
        "scene_index": scene_index,
        "retail_pointer": palette0,
        "colors": colors,
    }


def compile_palette(
    raw: bytes,
    source: dict[str, Any],
    *,
    rom_size: int = DEFAULT_ROM_SIZE,
    allocation_base: int = DEFAULT_ALLOCATION_BASE,
) -> tuple[bytes, dict[str, Any]]:
    validate_base(raw)
    if source.get("schema") != "truerecall.scene_palette.v1":
        raise ValueError("unsupported scene palette schema")

    scene_index = int(source["scene_index"])
    scene = scene_address(raw, scene_index)
    retail = export_scene_palette(raw, scene_index)

    if "retail_pointer" in source and int(source["retail_pointer"]) != retail["retail_pointer"]:
        raise ValueError("retail palette pointer identity changed")

    colors = validate_colors(list(source["colors"]))
    original_colors = retail["colors"]
    changed = [
        index
        for index, (before, after) in enumerate(zip(original_colors, colors))
        if before != after
    ]

    if not changed:
        return raw, {
            "schema": "truerecall.scene_palette_build.v1",
            "base_sha1": BASE_SHA1,
            "scene_index": scene_index,
            "noop": True,
            "retail_pointer": retail["retail_pointer"],
            "changed_color_indices": [],
            "output_sha1": BASE_SHA1,
        }

    if rom_size < BASE_SIZE:
        raise ValueError("output ROM cannot shrink below canonical base")
    if allocation_base < BASE_SIZE:
        raise ValueError("palette allocation must live in expanded ROM")

    palette_address = align(allocation_base, 0x10)
    if palette_address + PALETTE_BYTES > rom_size:
        raise ValueError("palette allocation overflows expanded ROM")

    out = bytearray(raw) + bytearray([0xFF]) * (rom_size - len(raw))
    out[ROM_END_OFFSET:ROM_END_OFFSET + 4] = p32(rom_size - 1)

    cursor = palette_address
    for value in colors:
        out[cursor:cursor + 2] = p16(value)
        cursor += 2

    retail_scene_record = bytes(raw[scene:scene + SCENE_RECORD_SIZE])
    out[scene + 0x02:scene + 0x06] = p32(palette_address)
    out[scene + 0x06:scene + 0x0A] = p32(palette_address)

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)

    authored_scene_record = bytes(out[scene:scene + SCENE_RECORD_SIZE])
    changed_scene_offsets = [
        i
        for i, (before, after) in enumerate(zip(retail_scene_record, authored_scene_record))
        if before != after
    ]
    if not set(changed_scene_offsets) <= set(range(0x02, 0x0A)):
        raise AssertionError(changed_scene_offsets)

    if u32(out, scene + 0x02) != palette_address:
        raise AssertionError("palette0 pointer patch failed")
    if u32(out, scene + 0x06) != palette_address:
        raise AssertionError("palette1 pointer patch failed")
    rebuilt_colors = [u16(out, palette_address + i * 2) for i in range(PALETTE_WORDS)]
    if rebuilt_colors != colors:
        raise AssertionError("palette round-trip mismatch")

    report = {
        "schema": "truerecall.scene_palette_build.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "noop": False,
        "retail_pointer": retail["retail_pointer"],
        "new_pointer": palette_address,
        "palette_bytes": PALETTE_BYTES,
        "changed_color_indices": changed,
        "scene_record_changed_offsets": changed_scene_offsets,
        "rom_size": len(out),
        "checksum": f"0x{checksum:04X}",
        "output_sha1": hashlib.sha1(out).hexdigest(),
        "runtime_validation": "pending",
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export")
    export.add_argument("rom", type=Path)
    export.add_argument("scene", type=int)
    export.add_argument("output", type=Path)

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("rom", type=Path)
    compile_cmd.add_argument("source", type=Path)
    compile_cmd.add_argument("output", type=Path)
    compile_cmd.add_argument("--report", type=Path)

    args = ap.parse_args()
    raw = args.rom.read_bytes()

    if args.command == "export":
        source = export_scene_palette(raw, args.scene)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return

    source = json.loads(args.source.read_text(encoding="utf-8"))
    out, report = compile_palette(raw, source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
