#!/usr/bin/env python3
"""Parser/serializer/compiler primitives for True Lies scene placement streams."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sys

HERE = Path(__file__).resolve().parent
ROM_PROBE = HERE.parent / "rom_probe"
if str(ROM_PROBE) not in sys.path:
    sys.path.insert(0, str(ROM_PROBE))

from level_objects_probe import SCENE_TABLE, SCENE_COUNT, u16, u32, lzbeam_decode

TYPE_MASK = 0x03FF


@dataclass
class Placement:
    index: int
    stride: int
    status: int
    x: int
    y: int
    param: Optional[int]
    decoded_offset: int

    @property
    def type_id(self) -> int:
        return self.status & TYPE_MASK

    @property
    def status_flags(self) -> int:
        return self.status & ~TYPE_MASK

    def with_type(self, type_id: int) -> "Placement":
        if not 0 <= type_id <= TYPE_MASK:
            raise ValueError(type_id)
        return Placement(self.index, self.stride, self.status_flags | type_id, self.x, self.y, self.param, self.decoded_offset)


@dataclass
class SceneObjectStream:
    scene_index: int
    scene_ptr: int
    descriptor: int
    source_lz: int
    placement_count: int
    start_offset: int
    end_offset: int
    prefix: bytes
    placements: list[Placement]
    stride_runs: list[tuple[int, int]]
    decoded_size: int


def read_stride_runs(rom: bytes, descriptor: int, count: int) -> list[tuple[int, int]]:
    runs = []; pos = descriptor + 0x0A; total = 0
    while total < count:
        stride = rom[pos]; quantity = rom[pos + 1]; pos += 2
        if stride not in (6, 8) or quantity == 0:
            raise ValueError((hex(descriptor), stride, quantity, total, count))
        runs.append((stride, quantity)); total += quantity
    if total != count:
        raise ValueError((total, count))
    return runs


def parse_scene(rom: bytes, scene_index: int) -> SceneObjectStream:
    if not 0 <= scene_index < SCENE_COUNT:
        raise ValueError(scene_index)
    scene = u32(rom, SCENE_TABLE + scene_index * 4)
    descriptor = u32(rom, scene + 0x0A)
    count = u16(rom, descriptor); start = u16(rom, descriptor + 2); end = u16(rom, descriptor + 4)
    source = u32(rom, descriptor + 6); decoded = lzbeam_decode(rom, source)
    runs = read_stride_runs(rom, descriptor, count)
    placements = []; off = start; index = 0
    for stride, quantity in runs:
        for _ in range(quantity):
            status = u16(decoded, off); x = u16(decoded, off + 2); y = u16(decoded, off + 4)
            param = u16(decoded, off + 6) if stride == 8 else None
            placements.append(Placement(index, stride, status, x, y, param, off)); off += stride; index += 1
    if off != end or end != len(decoded):
        raise ValueError((scene_index, off, end, len(decoded)))
    if any(placements[i].y > placements[i+1].y for i in range(len(placements)-1)):
        raise ValueError(f"scene {scene_index} retail placements are not y-sorted")
    return SceneObjectStream(scene_index, scene, descriptor, source, count, start, end, decoded[:start], placements, runs, len(decoded))


def serialize_preserving_layout(stream: SceneObjectStream, placements: list[Placement] | None = None) -> bytes:
    rows = stream.placements if placements is None else placements
    if len(rows) != stream.placement_count:
        raise ValueError("placement count changed")
    if [p.stride for p in rows] != [p.stride for p in stream.placements]:
        raise ValueError("stride layout changed; descriptor run rewrite required")
    if any(rows[i].y > rows[i+1].y for i in range(len(rows)-1)):
        raise ValueError("placements must remain sorted by Y")
    out = bytearray(stream.prefix)
    for p in rows:
        out += int(p.status & 0xFFFF).to_bytes(2, "big")
        out += int(p.x & 0xFFFF).to_bytes(2, "big")
        out += int(p.y & 0xFFFF).to_bytes(2, "big")
        if p.stride == 8:
            if p.param is None:
                raise ValueError("8-byte placement missing param")
            out += int(p.param & 0xFFFF).to_bytes(2, "big")
    if len(out) != stream.end_offset:
        raise ValueError((len(out), stream.end_offset))
    return bytes(out)


def collapse_stride_runs(placements: list[Placement]) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    for p in placements:
        if p.stride not in (6, 8):
            raise ValueError(p.stride)
        if runs and runs[-1][0] == p.stride and runs[-1][1] < 255:
            runs[-1] = (p.stride, runs[-1][1] + 1)
        else:
            runs.append((p.stride, 1))
    return runs


def serialize_compiled(prefix: bytes, placements: list[Placement]) -> tuple[bytes, list[tuple[int, int]]]:
    if any(placements[i].y > placements[i+1].y for i in range(len(placements)-1)):
        raise ValueError("placements must be sorted by Y")
    out = bytearray(prefix)
    for p in placements:
        out += (p.status & 0xFFFF).to_bytes(2, "big") + (p.x & 0xFFFF).to_bytes(2, "big") + (p.y & 0xFFFF).to_bytes(2, "big")
        if p.stride == 8:
            if p.param is None:
                raise ValueError("8-byte placement requires param")
            out += (p.param & 0xFFFF).to_bytes(2, "big")
        elif p.param is not None:
            raise ValueError("6-byte placement must not carry param")
    return bytes(out), collapse_stride_runs(placements)


def build_descriptor(*, count: int, start: int, end: int, source_lz: int, runs: list[tuple[int, int]]) -> bytes:
    if count != sum(q for _, q in runs):
        raise ValueError("run count mismatch")
    if not (0 <= count <= 0xFFFF and 0 <= start <= end <= 0xFFFF):
        raise ValueError("descriptor word overflow")
    raw = bytearray()
    raw += count.to_bytes(2, "big") + start.to_bytes(2, "big") + end.to_bytes(2, "big") + source_lz.to_bytes(4, "big")
    for stride, quantity in runs:
        if stride not in (6, 8) or not 1 <= quantity <= 255:
            raise ValueError((stride, quantity))
        raw += bytes((stride, quantity))
    return bytes(raw)


def main() -> None:
    import argparse, json
    ap = argparse.ArgumentParser(); ap.add_argument("rom", type=Path); ap.add_argument("--scene", type=int); args = ap.parse_args()
    rom = args.rom.read_bytes(); scenes = range(SCENE_COUNT) if args.scene is None else [args.scene]; rows = []
    for scene_index in scenes:
        stream = parse_scene(rom, scene_index); original = lzbeam_decode(rom, stream.source_lz); rebuilt = serialize_preserving_layout(stream)
        assert rebuilt == original
        rows.append({"scene":scene_index,"placements":stream.placement_count,"prefix_bytes":len(stream.prefix),"decoded_bytes":len(rebuilt),"stride_runs":stream.stride_runs})
    print(json.dumps(rows, indent=2))

if __name__ == "__main__": main()
