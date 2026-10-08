#!/usr/bin/env python3
"""Recover True Lies scene placement/object-stream metadata.

The probe parses the scene +0x0A spatial-streaming descriptor and emits only
structural/count metadata. It does not emit the full placement coordinate list.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19
DEFAULT_STREAM_FILTER = 0x3800


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off + 4], "big")


def lzbeam_decode(rom: bytes, off: int) -> bytes:
    out_len = u16(rom, off)
    command_offset = u16(rom, off + 2)
    read_pos = off + 4
    command_pos = off + command_offset + 2
    bits_left = 0
    current = 0
    out = bytearray()

    def bit() -> int:
        nonlocal command_pos, bits_left, current
        if bits_left == 0:
            current = rom[command_pos]
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
    out.extend(rom[read_pos:read_pos + literal_count])
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
            out.extend(rom[read_pos:read_pos + literal_count])
            read_pos += literal_count
    return bytes(out[:out_len])


def conservative_activation_peak(points: list[tuple[int, int]]) -> int:
    """Upper bound using the largest runtime activation footprint: 11×9 32px cells."""
    cells = Counter((x // 32, y // 32) for x, y in points)
    if not cells:
        return 0
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    best = 0
    for x0 in range(min(xs) - 10, max(xs) + 1):
        for y0 in range(min(ys) - 8, max(ys) + 1):
            best = max(best, sum(v for (x, y), v in cells.items() if x0 <= x <= x0 + 10 and y0 <= y <= y0 + 8))
    return best


def retention_peak(points: list[tuple[int, int]]) -> int:
    """Spatial upper bound for ordinary-object keep-alive rectangle.

    Cleanup code keeps ordinary objects while -97 <= dx < 353 and
    -97 <= dy < 257. This ignores path reachability and class-specific exceptions.
    """
    if not points:
        return 0
    candidate_x = set()
    candidate_y = set()
    for x, y in points:
        candidate_x.update((x - 352, x + 96))
        candidate_y.update((y - 256, y + 96))
    best = 0
    for camera_x in candidate_x:
        x_points = [(x, y) for x, y in points if -97 <= x - camera_x < 353]
        if len(x_points) <= best:
            continue
        for camera_y in candidate_y:
            best = max(best, sum(1 for x, y in x_points if -97 <= y - camera_y < 257))
    return best


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

    # Consumer-backed safety signatures.
    assert rom[0x010BB8:0x010BFE] == bytes.fromhex(
        "302900006b443200c278f9c0673c2f082f09024003ff0c4000e664303f004eb90000f7326544301f4eb9000101026532225f31490032316900020010316900040014006980000000"
    )
    assert rom[0x010764:0x0107C8].startswith(bytes.fromhex("48e73e003278fa003029001031c0f9c80640011e0240ffe0"))

    scenes = []
    total_stride = Counter()
    all_types = Counter()
    total_placements = 0
    total_pre_marked = 0

    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        placement_count = u16(rom, desc)
        start_offset = u16(rom, desc + 2)
        end_offset = u16(rom, desc + 4)
        source_lz = u32(rom, desc + 6)
        decoded = lzbeam_decode(rom, source_lz)

        runs = []
        run_pos = desc + 0x0A
        run_total = 0
        encoded_bytes = 0
        while run_total < placement_count:
            stride = rom[run_pos]
            quantity = rom[run_pos + 1]
            run_pos += 2
            assert stride in (6, 8)
            assert quantity > 0
            runs.append((stride, quantity))
            run_total += quantity
            encoded_bytes += stride * quantity
        assert run_total == placement_count
        assert start_offset + encoded_bytes == end_offset
        assert end_offset <= len(decoded)

        offset = start_offset
        scene_types = Counter()
        stride_counts = Counter()
        points = []
        pre_marked = 0
        nonnegative_eligible = 0
        for stride, quantity in runs:
            for _ in range(quantity):
                status_type = u16(decoded, offset)
                type_id = status_type & 0x03FF
                x = u16(decoded, offset + 2)
                y = u16(decoded, offset + 4)
                scene_types[type_id] += 1
                all_types[type_id] += 1
                stride_counts[stride] += 1
                total_stride[stride] += 1
                total_placements += 1
                if status_type & 0x8000:
                    pre_marked += 1
                    total_pre_marked += 1
                elif status_type & DEFAULT_STREAM_FILTER:
                    nonnegative_eligible += 1
                    points.append((x, y))
                offset += stride
        assert offset == end_offset
        assert max(scene_types, default=0) < 0x00E6  # retail scene placements all use generic-allocation path

        scenes.append({
            "scene": scene_index,
            "descriptor": f"0x{desc:06X}",
            "source_lzbeam": f"0x{source_lz:06X}",
            "decoded_bytes": len(decoded),
            "placement_start": f"0x{start_offset:04X}",
            "placement_end": f"0x{end_offset:04X}",
            "placements": placement_count,
            "stride_6_records": stride_counts[6],
            "stride_8_records": stride_counts[8],
            "unique_type_ids": len(scene_types),
            "pre_marked_bit15": pre_marked,
            "normal_stream_candidates": nonnegative_eligible,
            "activation_11x9_cell_upper_bound": conservative_activation_peak(points),
            "keep_alive_rectangle_upper_bound": retention_peak(points),
            "most_common_types": [[type_id, count] for type_id, count in scene_types.most_common(10)],
        })

    report = {
        "schema": "truerecall.level_objects.v1",
        "base_sha1": digest,
        "confirmed": {
            "placement_record_common_prefix": "word status/type + word X + word Y",
            "type_id_mask": "0x03FF",
            "materialized_marker": "bit15; spawn path skips negative records and ORs 0x8000 after successful materialization",
            "stream_filter": "source status/type word is ANDed with F9C0 before normal creation; retail object-stream setup uses 0x3800",
            "record_sizes": [6, 8],
            "extended_record": "8-byte records add one per-instance word parameter at +0x06",
            "descriptor": "word count, word placement_start, word placement_end, long LZBeam source, then (stride,quantity) byte pairs",
            "descriptor_end_proof": "placement_end == placement_start + sum(stride*quantity) for all 19 retail scenes",
            "source_link": "materialized generic object stores the placement low-RAM pointer in object+0x32",
            "streaming": "placements are spatially bucketed on 32px cells; visible-region traversal materializes nearby records through generic allocator 0x00F732",
        },
        "runtime_window_evidence": {
            "activation": "0x010764 computes 32px-aligned bounds around the view; footprint varies up to 11 columns × 9 rows",
            "ordinary_keep_alive": "0x0107D0 cleanup retains ordinary objects while -97 <= dx < 353 and -97 <= dy < 257, with class-specific exceptions",
            "warning": "reported peaks are spatial upper bounds, not measured runtime pool occupancy; camera reachability, filters and object-specific lifetime rules can reduce actual simultaneous usage",
        },
        "totals": {
            "placements": total_placements,
            "record_6_bytes": total_stride[6],
            "record_8_bytes": total_stride[8],
            "unique_type_ids": len(all_types),
            "pre_marked_bit15": total_pre_marked,
            "max_retail_type_id": max(all_types),
        },
        "scenes": scenes,
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
