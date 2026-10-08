#!/usr/bin/env python3
"""Render a True Lies archetype frame using a scene's real CRAM palette.

The caller supplies the live object render-attribute word when needed. For a
fresh generic placement this word is initialized to zero; some scripts may alter
priority/palette/flip bits before or during later states.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
ARCHETYPE_TABLE = 0x079906
SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def signed_byte(value: int) -> int:
    return value - 256 if value & 0x80 else value


def cram_palette(rom: bytes, scene_index: int) -> list[tuple[int, int, int]]:
    if not 0 <= scene_index < SCENE_COUNT:
        raise ValueError(f"scene must be 0..{SCENE_COUNT - 1}")
    scene = u32(rom, SCENE_TABLE + scene_index * 4)
    palette_ptr = u32(rom, scene + 0x02)
    colors = []
    for i in range(64):
        value = u16(rom, palette_ptr + i * 2)
        r = ((value >> 1) & 7) * 36
        g = ((value >> 5) & 7) * 36
        b = ((value >> 9) & 7) * 36
        colors.append((r, g, b))
    return colors


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
            raise ValueError(f"RLE overrun at 0x{off:06X}")
    if len(out) != 128:
        raise ValueError(f"RLE chunk at 0x{off:06X} decoded to {len(out)} bytes")
    return bytes(out)


def resolve_chunk(rom: bytes, descriptor: int, piece_word: int) -> bytes:
    group = (piece_word >> 8) & 0x3F
    index = piece_word & 0xFF
    source = u32(rom, descriptor + 0x02 + group * 4)
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


def render_frame(rom: bytes, archetype: int, selector: int, scene: int, object_attr: int) -> tuple[Image.Image, int]:
    descriptor = u32(rom, ARCHETYPE_TABLE + archetype * 4)
    encoded = u16(rom, descriptor + selector)
    alias_offset = encoded & 0x0FFE
    record_offset = u16(rom, descriptor + alias_offset)
    record = descriptor + record_offset
    record_flags = rom[record + 0x0E]
    piece_count = rom[record + 0x0F]
    if not 1 <= piece_count <= 64:
        raise ValueError(f"implausible piece count {piece_count}")

    # Retail renderer: ((encoded & C000) >> 3) XOR object+8 XOR word(record+E),
    # then mask F800. The selector contribution lands only in H/V flip bits;
    # palette bits therefore come from object_attr XOR record_flags<<8.
    base_attributes = (((encoded & 0xC000) >> 3) ^ (object_attr & 0xFFFF) ^ (record_flags << 8)) & 0xF800
    palette_bank = (base_attributes >> 13) & 3
    palette = cram_palette(rom, scene)

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
    image = Image.new("RGBA", (max_x - min_x, max_y - min_y), (0, 0, 0, 0))

    for x, y, word, chunk in pieces:
        hflip = bool(word & 0x4000) ^ bool(base_attributes & 0x0800)
        vflip = bool(word & 0x8000) ^ bool(base_attributes & 0x1000)
        piece = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        px = piece.load()
        for tile_x in range(2):
            for tile_y in range(2):
                tile = tile_x * 2 + tile_y  # Genesis multi-tile sprite order
                for yy in range(8):
                    for xx in range(8):
                        color_index = tile_pixel(chunk, tile, xx, yy)
                        if color_index == 0:
                            continue
                        dx = tile_x * 8 + xx
                        dy = tile_y * 8 + yy
                        if hflip:
                            dx = 15 - dx
                        if vflip:
                            dy = 15 - dy
                        px[dx, dy] = (*palette[palette_bank * 16 + color_index], 255)
        image.alpha_composite(piece, (x - min_x, y - min_y))
    return image, palette_bank


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("archetype", type=parse_int)
    parser.add_argument("selector", type=parse_int)
    parser.add_argument("scene", type=parse_int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--object-attr", type=parse_int, default=0, help="live object+0x08 word; fresh generic placements start at 0")
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest = hashlib.sha1(rom).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    image, palette_bank = render_frame(rom, args.archetype, args.selector, args.scene, args.object_attr)
    if args.scale > 1:
        image = image.resize((image.width * args.scale, image.height * args.scale), Image.Resampling.NEAREST)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"wrote {args.output} ({image.width}x{image.height}); scene={args.scene} palette_bank={palette_bank}")


if __name__ == "__main__":
    main()
