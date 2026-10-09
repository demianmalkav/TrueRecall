#!/usr/bin/env python3
"""Pixel/geometry round-trip the runtime-proven visual avatar descriptor.

M09A's historical retail round-trip used archetype-191 descriptor 0x0E51FE. M08
runtime evidence later isolated object+0x2C == 0x0F0000 as the descriptor of the
visual avatar actually affected by renderer/cache substitution. M09C therefore
needs an equivalent compiler round-trip against 0x0F0000 before authored native
sequencing is attempted.

The probe emits hashes and structural metrics only; it does not save retail art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "build"))
sys.path.insert(0, str(TOOLS))
from sprite_sequence_compiler import compile_sequence
from sprite_frame_export import chunk_image, resolve_chunk, u16

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
DIR_TABLE = 0x013F32
VISUAL_DESCRIPTOR = 0x0F0000
ARCH191_DESCRIPTOR = 0x0E51FE
MANIAC_BASE = 0x00F2


def facing_selectors(rom: bytes, base: int) -> list[int]:
    return [u16(rom, DIR_TABLE + base + facing * 2) for facing in range(8)]


def unique_preserve(values: list[int]) -> list[int]:
    seen: set[int] = set()
    out = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def record_info(rom: bytes, descriptor: int, selector: int) -> dict[str, Any]:
    encoded = u16(rom, descriptor + selector)
    alias = encoded & 0x0FFE
    record_offset = u16(rom, descriptor + alias)
    record = descriptor + record_offset
    piece_count = rom[record + 0x0F]
    if not 1 <= piece_count <= 64:
        raise ValueError(
            f"descriptor 0x{descriptor:06X} selector 0x{selector:04X}: "
            f"implausible piece count {piece_count}"
        )
    pieces = []
    for index in range(piece_count):
        off = record + 0x10 + index * 4
        raw_x = rom[off]
        raw_y = rom[off + 1]
        piece_word = u16(rom, off + 2)
        chunk = resolve_chunk(rom, descriptor, piece_word)
        if len(chunk) != 128:
            raise ValueError("short chunk")
        pieces.append(
            {
                "raw_x": raw_x,
                "raw_y": raw_y,
                "piece_word": piece_word,
                "chunk": chunk,
            }
        )
    return {
        "selector": selector,
        "encoded_entry": encoded,
        "alias_offset": alias,
        "record_offset": record_offset,
        "record_address": record,
        "piece_count": piece_count,
        "control_words": [u16(rom, record + i * 2) for i in range(3)],
        "origin_x": u16(rom, record + 0x06),
        "origin_y": u16(rom, record + 0x08),
        "clip_width": u16(rom, record + 0x0A),
        "clip_height": u16(rom, record + 0x0C),
        "record_flags": rom[record + 0x0E],
        "pieces": pieces,
    }


def compiler_frame(rom: bytes, descriptor: int, selector: int) -> tuple[dict[str, Any], dict[str, Any]]:
    info = record_info(rom, descriptor, selector)

    # The existing sequence compiler expresses piece positions as 16x16 source
    # cells and encodes each mapping byte as cell_position + 15. Preserve that
    # contract exactly; a failure here means the compiler cannot yet represent
    # this visual descriptor losslessly and M09C must stop.
    normalized = []
    for piece in info["pieces"]:
        x = piece["raw_x"] - 15
        y = piece["raw_y"] - 15
        if x < 0 or y < 0 or x % 16 or y % 16:
            raise ValueError(
                f"selector 0x{selector:04X} is outside current compiler grid contract: "
                f"raw=({piece['raw_x']},{piece['raw_y']})"
            )
        normalized.append((x, y, piece["piece_word"], piece["chunk"]))

    width = max(x + 16 for x, _y, _word, _chunk in normalized)
    height = max(y + 16 for _x, y, _word, _chunk in normalized)
    image = Image.new("P", (width, height), 0)
    palette = []
    for index in range(256):
        palette.extend((index, index, index))
    image.putpalette(palette)

    for x, y, word, chunk in normalized:
        image.paste(
            chunk_image(chunk, bool(word & 0x4000), bool(word & 0x8000)),
            (x, y),
        )

    frame = {
        "image": image,
        "origin_x": info["origin_x"],
        "origin_y": info["origin_y"],
        "clip_width": info["clip_width"],
        "clip_height": info["clip_height"],
        "control0": info["control_words"][0],
        "control1": info["control_words"][1],
        "control2": info["control_words"][2],
        "record_flags": info["record_flags"],
    }
    public = {key: value for key, value in info.items() if key != "pieces"}
    public["piece_words"] = [f"0x{piece['piece_word']:04X}" for piece in info["pieces"]]
    public["pixel_sha1"] = hashlib.sha1(image.tobytes()).hexdigest()
    public["dimensions"] = [image.width, image.height]
    return frame, public


def reconstruct_compiled(record: bytes, chunks: bytes, size: tuple[int, int]) -> Image.Image:
    image = Image.new("P", size, 0)
    palette = []
    for index in range(256):
        palette.extend((index, index, index))
    image.putpalette(palette)
    count = record[0x0F]
    for index in range(count):
        off = 0x10 + index * 4
        x = record[off] - 15
        y = record[off + 1] - 15
        word = int.from_bytes(record[off + 2:off + 4], "big")
        chunk_index = word & 0xFF
        chunk = chunks[chunk_index * 128:(chunk_index + 1) * 128]
        image.paste(
            chunk_image(chunk, bool(word & 0x4000), bool(word & 0x8000)),
            (x, y),
        )
    return image


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

    facing = facing_selectors(rom, MANIAC_BASE)
    selectors = unique_preserve(facing)
    if not selectors:
        raise AssertionError("empty JLLBFR facing family")

    frames = []
    retail_public = []
    for selector in selectors:
        frame, public = compiler_frame(rom, VISUAL_DESCRIPTOR, selector)
        frames.append(frame)
        retail_public.append(public)

    records, chunks, metadata = compile_sequence(frames, group=0)
    if len(records) != len(frames):
        raise AssertionError("frame count mismatch")

    compiled_hashes = []
    for selector, source_frame, record, public in zip(selectors, frames, records, retail_public):
        rebuilt = reconstruct_compiled(
            record,
            chunks,
            (source_frame["image"].width, source_frame["image"].height),
        )
        source_pixels = source_frame["image"].tobytes()
        rebuilt_pixels = rebuilt.tobytes()
        if rebuilt_pixels != source_pixels:
            raise AssertionError(f"pixel mismatch selector 0x{selector:04X}")
        expected_header = b"".join(
            int(source_frame[key]).to_bytes(2, "big")
            for key in (
                "control0", "control1", "control2", "origin_x", "origin_y", "clip_width", "clip_height"
            )
        ) + bytes([source_frame["record_flags"]])
        if record[:0x0F] != expected_header:
            raise AssertionError(f"record header mismatch selector 0x{selector:04X}")
        compiled_hashes.append(
            {
                "selector": selector,
                "record_sha1": hashlib.sha1(record).hexdigest(),
                "pixel_sha1": hashlib.sha1(rebuilt_pixels).hexdigest(),
                "piece_count": record[0x0F],
                "matches_retail_pixels": True,
                "retail_pixel_sha1": public["pixel_sha1"],
            }
        )

    # Resolve the same selectors through archetype 191 only as comparative
    # structural evidence. Do not treat it as the runtime visual descriptor.
    archetype191_comparison = []
    for selector in selectors:
        info = record_info(rom, ARCH191_DESCRIPTOR, selector)
        archetype191_comparison.append(
            {
                "selector": selector,
                "record_offset": info["record_offset"],
                "piece_count": info["piece_count"],
                "control_words": info["control_words"],
            }
        )

    report = {
        "schema": "truerecall.m09c.visual_avatar_roundtrip.v1",
        "base_sha1": digest,
        "runtime_visual_descriptor": VISUAL_DESCRIPTOR,
        "comparison_archetype191_descriptor": ARCH191_DESCRIPTOR,
        "facing_family_base": MANIAC_BASE,
        "facing_selectors": facing,
        "unique_selectors": selectors,
        "frame_count": len(frames),
        "retail_visual_frames": retail_public,
        "compiled_frames": compiled_hashes,
        "compiler_metadata": metadata,
        "chunk_bank_sha1": hashlib.sha1(chunks).hexdigest(),
        "chunk_bank_bytes": len(chunks),
        "archetype191_comparison": archetype191_comparison,
        "conclusion_gate": (
            "PASS means the existing authored-sequence compiler can represent the "
            "runtime-proven visual avatar descriptor's JLLBFR facing family without "
            "pixel or record-header loss."
        ),
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
