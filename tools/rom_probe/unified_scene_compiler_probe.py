#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_compiler import build

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
EXPECTED_OUTPUT_SHA1 = "fac81fdc87b76a75c9b590d58707b16fcd6a5f04"
EXPECTED_CHECKSUM = "0x3E9A"

MANIFEST = {
    "schema": "truerecall.scene_patch.v1",
    "scene_index": 18,
    "allocation_base": "0x300000",
    "map_operations": [
        {"op": "set_tile", "plane": "C000", "x": 0, "y": 0, "value": "0x0001"}
    ],
    "object_operations": [
        {
            "op": "add",
            "type_id": 54,
            "x": 128,
            "y": 120,
            "stride": 6,
            "status_flags": "0x7800",
        }
    ],
    "world_operations": [
        {
            "op": "add",
            "id": "authored_wall_0",
            "type": 9,
            "rect": [64, 64, 80, 256],
        }
    ],
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == EXPECTED_SIZE
    assert hashlib.sha1(raw).hexdigest() == EXPECTED_SHA1

    out, report = build(raw, MANIFEST)
    assert len(out) == 0x400000
    assert report["output_sha1"] == EXPECTED_OUTPUT_SHA1
    assert report["checksum"] == EXPECTED_CHECKSUM

    c000 = report["maps"]["C000"]
    assert c000["dimensions"] == [18, 40]
    assert c000["changed_words"] == 1
    assert c000["new_descriptor"] == 0x300000
    assert c000["new_lz"] == 0x300010

    objects = report["objects"]
    assert objects["base_count"] == 40 and objects["new_count"] == 41
    assert objects["stride_runs"] == [[8, 2], [6, 1], [8, 38]]
    assert objects["new_descriptor"] == 0x300120
    assert objects["new_lz"] == 0x300130

    world = report["world"]
    assert world["new_base"] == 0x300300
    assert world["retail_payload_bytes"] == 0x017E
    assert world["payload_boundary_source"] == "next_world_base"
    assert world["record_count"] == 1
    assert world["pool_start"] == 0x0190
    assert world["pool_bytes"] == 2
    assert world["operations"][0]["offset"] == 0x0180

    assert report["scene_record_changed_offsets"] == [11, 12, 13, 15, 16, 17, 27, 28, 29]

    summary = {
        "schema": "truerecall.m11b.unified_scene_compiler.v1",
        "base_sha1": EXPECTED_SHA1,
        "output_sha1": report["output_sha1"],
        "checksum": report["checksum"],
        "scene_index": 18,
        "map_changed_words": c000["changed_words"],
        "object_count": [objects["base_count"], objects["new_count"]],
        "object_stride_runs": objects["stride_runs"],
        "world_new_record_offset": "0x0180",
        "world_pool_start": "0x0190",
        "allocation_count": len(report["allocations"]),
        "scene_record_changed_offsets": report["scene_record_changed_offsets"],
        "runtime_validation": "pending",
    }
    text = json.dumps(summary, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
