#!/usr/bin/env python3
"""Render one True Lies archetype animation selector as a debug PNG.

Geometry/chunks/flips follow the recovered retail renderer. Colors are synthetic:
the tool intentionally does not claim runtime palette identity yet.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
ARCHETYPE_TABLE = 0x079906


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def rle128_decode(rom: bytes, off: int) -> bytes:
    out = bytearray()
    p = off
    while True:
        cmd = rom[p]
        p += 1
        if cmd == 0:
            break
        if cmd < 0x80:
            count = 128 - cmd
            out.extend(rom[p:p + count])
            p += count
        else:
            count = 256 - cmd
            value = rom[p]
            p += 1
            out.extend(bytes([value]) * count)
        if len(out) > 128:
            raise ValueError(f"RLE chunk overrun at 0x{off:06X}")
    if len(out) != 128:
        raise ValueError(f"RLE chunk at 0x{off:06X} decoded to {len(out)} bytes")
    return bytes(out)


def resolve_chunk(rom: bytes, descriptor: int, piece_word: int) -> bytes:
    group = (piece_word >> 8) & 0x3F
    index = piece_word & 0xFF
    source = u32(rom, descriptor + 2 + group * 4)
    if source & 0x80000000:
        table = source & 0x7FFFFFFF
        entry = u16(rom, table + index * 2)
        if entry & 0x8000:
            return rle128_decode(rom, table + (entry & 0x7FFF))
        return rom[table + entry:table + entry + 128]
    return rom[source + index * 128:source + (index + 1) * 128]


def tile_pixel(chunk: bytes, tile: int, x: int, y: int) -> int:
    value = chunk[tile * 32 + y * 4 + x // 2]
    return (value >> 4) & 0x0F if (x & 1) == 0 else value & 0x0F


def chunk_image(chunk: bytes, hflip: bool, vflip: bool) -> Image.Image:
    image = Image.new("P", (16, 16), 0)
    palette = []
    for i in range(256):
        if i == 0:
            palette.extend((0, 0, 0))
        else:
            palette.extend((min(255, 28 + i * 14), min(255, 14 + i * 10), min(255, 8 + i * 6)))
    image.putpalette(palette)
    px = image.load()
    for tile_x in range(2):
        for tile_y in range(2):
            # Genesis multi-tile sprite ordering is column-major.
            tile = tile_x * 2 + tile_y
            for y in range(8):
                for x in range(8):
                    dst_x = tile_x * 8 + x
                    dst_y = tile_y * 8 + y
                    if hflip:
                        dst_x = 15 - dst_x
                    if vflip:
                        dst_y = 15 - dst_y
                    px[dst_x, dst_y] = tile_pixel(chunk, tile, x, y)
    return image


def signed_byte(value: int) -> int:
    return value - 256 if value & 0x80 else value


def render_frame(rom: bytes, archetype: int, selector: int) -> Image.Image:
    descriptor = u32(rom, ARCHETYPE_TABLE + archetype * 4)
    if descriptor == 0 or descriptor >= len(rom):
        raise ValueError(f"invalid descriptor for archetype {archetype}: 0x{descriptor:08X}")
    encoded = u16(rom, descriptor + selector)
    alias = encoded & 0x0FFE
    record_offset = u16(rom, descriptor + alias)
    record = descriptor + record_offset
    piece_count = rom[record + 0x0F]
    if not 1 <= piece_count <= 64:
        raise ValueError(f"implausible piece count {piece_count}")

    pieces = []
    for i in range(piece_count):
        off = record + 0x10 + i * 4
        x = signed_byte(rom[off])
        y = signed_byte(rom[off + 1])
        word = u16(rom, off + 2)
        chunk = resolve_chunk(rom, descriptor, word)
        if len(chunk) != 128:
            raise ValueError("short sprite chunk")
        pieces.append((x, y, word, chunk))

    min_x = min(x for x, _, _, _ in pieces)
    min_y = min(y for _, y, _, _ in pieces)
    max_x = max(x + 16 for x, _, _, _ in pieces)
    max_y = max(y + 16 for _, y, _, _ in pieces)
    frame = Image.new("P", (max_x - min_x, max_y - min_y), 0)
    rendered = []
    for x, y, word, chunk in pieces:
        tile = chunk_image(chunk, bool(word & 0x4000), bool(word & 0x8000))
        frame.putpalette(tile.getpalette())
        rendered.append((x, y, tile))
    for x, y, tile in rendered:
        mask = tile.point(lambda p: 255 if p else 0, mode="L")
        frame.paste(tile, (x - min_x, y - min_y), mask)
    return frame


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("archetype", type=parse_int)
    parser.add_argument("selector", type=parse_int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest = hashlib.sha1(rom).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    image = render_frame(rom, args.archetype, args.selector)
    if args.scale > 1:
        image = image.resize((image.width * args.scale, image.height * args.scale), Image.Resampling.NEAREST)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"wrote {args.output} ({image.width}x{image.height}); synthetic debug palette")


if __name__ == "__main__":
    main()
