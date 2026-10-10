#!/usr/bin/env python3
"""Author the primary gameplay-plane Genesis tile resource for a scene.

A non-zero scene plane graphics descriptor is three longs:

    primary_lzbeam_ptr, secondary_ptr, aux_ptr

M1.1B deliberately authors only the primary LZBeam resource. Secondary/aux
identity is preserved byte-for-byte until their semantics are independently
recovered. Exported tile bytes are local derived artifacts and must not be
committed when they contain retail graphics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lzbeam_codec import decode_stream, encode_stream

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 0x200000
DEFAULT_ROM_SIZE = 0x400000
DEFAULT_ALLOCATION_BASE = 0x304000
ROM_END_OFFSET = 0x01A4
CHECKSUM_OFFSET = 0x018E
SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19
PRIMARY_PLANE_OFFSET = 0x16
SECONDARY_PLANE_OFFSET = 0x22
TILE_BYTES = 32
TILE_INDEX_MASK = 0x07FF


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


def descriptor_identity(raw: bytes, scene_index: int) -> dict[str, int]:
    scene = scene_address(raw, scene_index)
    descriptor = u32(raw, scene + PRIMARY_PLANE_OFFSET)
    if descriptor == 0:
        raise ValueError(f"scene {scene_index} has no primary graphics descriptor")
    secondary_plane_descriptor = u32(raw, scene + SECONDARY_PLANE_OFFSET)
    return {
        "descriptor": descriptor,
        "primary_lz": u32(raw, descriptor),
        "secondary": u32(raw, descriptor + 4),
        "aux": u32(raw, descriptor + 8),
        "secondary_plane_descriptor": secondary_plane_descriptor,
    }


def _map_tile_indices(raw: bytes, scene: int, block_offset: int) -> list[int]:
    map_descriptor = u32(raw, scene + block_offset + 4)
    map_lz = u32(raw, map_descriptor)
    width = u16(raw, map_descriptor + 4)
    height = u16(raw, map_descriptor + 6)
    decoded = decode_stream(raw, map_lz)
    expected = width * height * 2
    if len(decoded) != expected:
        raise ValueError((width, height, len(decoded), expected))
    return [u16(decoded, off) & TILE_INDEX_MASK for off in range(0, len(decoded), 2)]


def map_reference_stats(raw: bytes, scene_index: int) -> dict[str, Any]:
    scene = scene_address(raw, scene_index)
    result: dict[str, Any] = {}
    for name, block in (("C000", PRIMARY_PLANE_OFFSET), ("E000", SECONDARY_PLANE_OFFSET)):
        indices = _map_tile_indices(raw, scene, block)
        result[name] = {
            "entry_count": len(indices),
            "min_tile_index": min(indices),
            "max_tile_index": max(indices),
            "unique_tile_indices": len(set(indices)),
        }
    return result


def export_primary_graphics(raw: bytes, scene_index: int) -> dict[str, Any]:
    validate_base(raw)
    identity = descriptor_identity(raw, scene_index)
    decoded = decode_stream(raw, identity["primary_lz"])
    if len(decoded) % TILE_BYTES:
        raise ValueError(f"primary graphics length is not tile-aligned: {len(decoded)}")
    tile_count = len(decoded) // TILE_BYTES
    refs = map_reference_stats(raw, scene_index)
    for plane, row in refs.items():
        if row["max_tile_index"] >= tile_count:
            raise ValueError(f"{plane} references tile outside primary set")
    return {
        "schema": "truerecall.scene_primary_graphics.v1",
        "scene_index": scene_index,
        "retail_descriptor": identity["descriptor"],
        "retail_primary_lz": identity["primary_lz"],
        "secondary_pointer": identity["secondary"],
        "aux_pointer": identity["aux"],
        "secondary_plane_descriptor": identity["secondary_plane_descriptor"],
        "tile_count": tile_count,
        "tile_bytes_hex": decoded.hex(),
        "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "map_reference_stats": refs,
    }


def compile_primary_graphics(
    raw: bytes,
    source: dict[str, Any],
    *,
    force_relocate: bool = False,
    rom_size: int = DEFAULT_ROM_SIZE,
    allocation_base: int = DEFAULT_ALLOCATION_BASE,
) -> tuple[bytes, dict[str, Any]]:
    validate_base(raw)
    if source.get("schema") != "truerecall.scene_primary_graphics.v1":
        raise ValueError("unsupported primary graphics schema")

    scene_index = int(source["scene_index"])
    scene = scene_address(raw, scene_index)
    identity = descriptor_identity(raw, scene_index)
    expected_identity = {
        "retail_descriptor": identity["descriptor"],
        "retail_primary_lz": identity["primary_lz"],
        "secondary_pointer": identity["secondary"],
        "aux_pointer": identity["aux"],
        "secondary_plane_descriptor": identity["secondary_plane_descriptor"],
    }
    for key, value in expected_identity.items():
        if int(source[key]) != value:
            raise ValueError(f"graphics identity changed: {key}")

    edited = bytes.fromhex(source["tile_bytes_hex"])
    if not edited or len(edited) % TILE_BYTES:
        raise ValueError("primary graphics must contain complete 32-byte Genesis tiles")
    tile_count = len(edited) // TILE_BYTES
    if int(source["tile_count"]) != tile_count:
        raise ValueError("tile_count does not match tile bytes")

    original = decode_stream(raw, identity["primary_lz"])
    original_count = len(original) // TILE_BYTES
    refs = map_reference_stats(raw, scene_index)
    for plane, row in refs.items():
        if row["max_tile_index"] >= tile_count:
            raise ValueError(f"edited primary set too small for {plane}")

    changed_tiles = [
        index
        for index in range(max(original_count, tile_count))
        if original[index * TILE_BYTES:(index + 1) * TILE_BYTES]
        != edited[index * TILE_BYTES:(index + 1) * TILE_BYTES]
    ]

    if edited == original and not force_relocate:
        return raw, {
            "schema": "truerecall.scene_primary_graphics_build.v1",
            "base_sha1": BASE_SHA1,
            "scene_index": scene_index,
            "noop": True,
            "force_relocate": False,
            "changed_tile_indices": [],
            "decoded_sha256": hashlib.sha256(original).hexdigest(),
            "output_sha1": BASE_SHA1,
        }

    if rom_size < BASE_SIZE:
        raise ValueError("output ROM cannot shrink below canonical base")
    if allocation_base < BASE_SIZE:
        raise ValueError("graphics allocation must live in expanded ROM")

    encoded = encode_stream(edited)
    descriptor_address = align(allocation_base, 0x10)
    lz_address = align(descriptor_address + 12, 0x10)
    if lz_address + len(encoded) > rom_size:
        raise ValueError("graphics relocation overflows expanded ROM")

    out = bytearray(raw) + bytearray([0xFF]) * (rom_size - len(raw))
    out[ROM_END_OFFSET:ROM_END_OFFSET + 4] = p32(rom_size - 1)
    out[descriptor_address:descriptor_address + 12] = (
        p32(lz_address) + p32(identity["secondary"]) + p32(identity["aux"])
    )
    out[lz_address:lz_address + len(encoded)] = encoded
    out[scene + PRIMARY_PLANE_OFFSET:scene + PRIMARY_PLANE_OFFSET + 4] = p32(descriptor_address)

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = p16(checksum)

    if u32(out, scene + PRIMARY_PLANE_OFFSET) != descriptor_address:
        raise AssertionError("scene graphics descriptor patch failed")
    if u32(out, descriptor_address + 4) != identity["secondary"]:
        raise AssertionError("secondary graphics pointer changed")
    if u32(out, descriptor_address + 8) != identity["aux"]:
        raise AssertionError("aux graphics pointer changed")
    rebuilt = decode_stream(out, lz_address)
    if rebuilt != edited:
        raise AssertionError("relocated primary graphics decode mismatch")

    report = {
        "schema": "truerecall.scene_primary_graphics_build.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "noop": False,
        "force_relocate": force_relocate,
        "retail_descriptor": identity["descriptor"],
        "retail_primary_lz": identity["primary_lz"],
        "secondary_pointer": identity["secondary"],
        "aux_pointer": identity["aux"],
        "new_descriptor": descriptor_address,
        "new_primary_lz": lz_address,
        "encoded_bytes": len(encoded),
        "decoded_bytes": len(edited),
        "tile_count": tile_count,
        "changed_tile_indices": changed_tiles,
        "decoded_sha256": hashlib.sha256(edited).hexdigest(),
        "encoded_sha256": hashlib.sha256(encoded).hexdigest(),
        "map_reference_stats": refs,
        "allocations": [
            {"name": "primary_graphics_descriptor", "address": descriptor_address, "size": 12},
            {"name": "primary_graphics_lz", "address": lz_address, "size": len(encoded)},
        ],
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
    compile_cmd.add_argument("--force-relocate", action="store_true")
    compile_cmd.add_argument("--allocation-base", type=lambda x: int(x, 0), default=DEFAULT_ALLOCATION_BASE)

    args = ap.parse_args()
    raw = args.rom.read_bytes()
    if args.command == "export":
        source = export_primary_graphics(raw, args.scene)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return

    source = json.loads(args.source.read_text(encoding="utf-8"))
    out, report = compile_primary_graphics(
        raw,
        source,
        force_relocate=args.force_relocate,
        allocation_base=args.allocation_base,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
