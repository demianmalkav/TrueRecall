#!/usr/bin/env python3
"""M0.6G: re-encode and relocate a gameplay map layer without changing its data.

Scene 0 C000 map data is decoded from retail LZBeam, encoded by TrueRecall,
placed in verified final FF padding, and its map descriptor is redirected.
The original compressed retail block remains untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "lzbeam"))
from lzbeam_codec import decode_stream, encode_stream

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
SCENE_TABLE = 0x013B4A
SCENE_INDEX = 0
NEW_LZ = 0x1FB000
FREE_START = 0x1FABC3
FREE_END = 0x200000
CHECKSUM_OFFSET = 0x018E


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(raw)}")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    record = u32(raw, SCENE_TABLE + SCENE_INDEX * 4)
    plane_block = record + 0x16  # first/C000 gameplay plane
    map_descriptor = u32(raw, plane_block + 4)
    retail_lz = u32(raw, map_descriptor)
    width = u16(raw, map_descriptor + 4)
    height = u16(raw, map_descriptor + 6)

    decoded = decode_stream(raw, retail_lz)
    if len(decoded) != width * height * 2:
        raise SystemExit("retail map does not match descriptor dimensions")
    encoded = encode_stream(decoded)
    if decode_stream(encoded) != decoded:
        raise AssertionError("new LZBeam stream does not round-trip")

    if NEW_LZ < FREE_START or NEW_LZ + len(encoded) > FREE_END:
        raise SystemExit("relocated stream does not fit verified FF padding")
    if any(x != 0xFF for x in raw[NEW_LZ:NEW_LZ + len(encoded)]):
        raise SystemExit("target relocation space is not pristine FF padding")

    out = bytearray(raw)
    out[NEW_LZ:NEW_LZ + len(encoded)] = encoded
    out[map_descriptor:map_descriptor + 4] = NEW_LZ.to_bytes(4, "big")
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = checksum(out).to_bytes(2, "big")

    if u32(out, map_descriptor) != NEW_LZ:
        raise AssertionError("map descriptor pointer was not redirected")
    if decode_stream(bytes(out), NEW_LZ) != decoded:
        raise AssertionError("generated ROM map data differs after relocation")
    if raw[retail_lz:retail_lz + 4] != out[retail_lz:retail_lz + 4]:
        raise AssertionError("retail compressed block was unexpectedly overwritten")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"base_sha1={digest}")
    print(f"scene={SCENE_INDEX} plane=C000 dimensions={width}x{height}")
    print(f"retail_lz=0x{retail_lz:06X}")
    print(f"relocated_lz=0x{NEW_LZ:06X} encoded_bytes={len(encoded)} decoded_bytes={len(decoded)}")
    print(f"checksum=0x{checksum(out):04X}")
    print(f"output_sha1={hashlib.sha1(out).hexdigest()}")


if __name__ == "__main__":
    main()
