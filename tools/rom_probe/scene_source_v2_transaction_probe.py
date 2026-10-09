#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from lzbeam_codec import decode_stream
from scene_compiler import BASE_SHA1, BASE_SIZE, CHECKSUM_OFFSET, SCENE_TABLE, genesis_checksum, u16, u32
from scene_compiler_v2 import compile_source_v2
from scene_source_v2 import export_scene_source_v2, source_v2_to_patch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    scene_index = 18
    base = export_scene_source_v2(raw, scene_index)

    no_op, no_op_report = compile_source_v2(raw, copy.deepcopy(base))
    assert no_op == raw
    assert no_op_report["noop"] is True

    edited = copy.deepcopy(base)

    before_tile = edited["planes"]["C000"]["tile_words"][0]
    after_tile = 0x0001 if before_tile != 0x0001 else 0x0002
    edited["planes"]["C000"]["tile_words"][0] = after_tile

    color_index = 1
    before_color = edited["palette"]["colors"][color_index]
    after_color = 0x0EEE if before_color != 0x0EEE else 0x0000
    edited["palette"]["colors"][color_index] = after_color

    patch = source_v2_to_patch(base, edited)
    assert len(patch["scene_patch"]["map_operations"]) == 1
    assert patch["scene_patch"]["object_operations"] == []
    assert patch["scene_patch"]["world_operations"] == []
    assert patch["palette_operation"] is not None
    assert patch["palette_operation"]["changed_indices"] == [color_index]

    out, report = compile_source_v2(raw, edited)
    assert report["noop"] is False
    build = report["build"]
    assert len(out) == 0x400000
    assert build["scene_stage"]["maps"]["C000"]["changed_words"] == 1
    assert build["palette"]["changed_color_indices"] == [color_index]
    assert build["output_sha1"] == hashlib.sha1(out).hexdigest()

    allocations = sorted(build["allocations"], key=lambda row: row["address"])
    for left, right in zip(allocations, allocations[1:]):
        assert left["address"] + left["size"] <= right["address"]
    assert allocations[-1]["name"] == "scene_palette"

    scene = u32(out, SCENE_TABLE + scene_index * 4)
    map_descriptor = u32(out, scene + 0x1A)
    map_lz = u32(out, map_descriptor)
    rebuilt_map = decode_stream(out, map_lz)
    assert u16(rebuilt_map, 0) == after_tile

    palette_pointer0 = u32(out, scene + 0x02)
    palette_pointer1 = u32(out, scene + 0x06)
    assert palette_pointer0 == palette_pointer1 == build["palette"]["new_pointer"]
    assert u16(out, palette_pointer0 + color_index * 2) == after_color

    assert u16(out, CHECKSUM_OFFSET) == genesis_checksum(out)

    result = {
        "schema": "truerecall.m11h.scene_source_v2_transaction.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": scene_index,
        "no_op_exact": True,
        "authored": {
            "tile": {
                "index": 0,
                "before": before_tile,
                "after": after_tile,
            },
            "palette": {
                "index": color_index,
                "before": before_color,
                "after": after_color,
                "new_pointer": build["palette"]["new_pointer"],
            },
            "allocation_count": len(allocations),
            "allocations": allocations,
            "scene_record_changed_offsets": build["scene_record_changed_offsets"],
            "output_sha1": build["output_sha1"],
            "checksum": build["checksum"],
        },
        "runtime_validation": "pending",
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
