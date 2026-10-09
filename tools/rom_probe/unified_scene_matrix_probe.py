#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_compiler import build

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 2_097_152

CASES = {
    "scene18_full": {
        "manifest": {
            "schema": "truerecall.scene_patch.v1",
            "scene_index": 18,
            "allocation_base": "0x300000",
            "map_operations": [
                {"op": "set_tile", "plane": "C000", "x": 0, "y": 0, "value": "0x0001"}
            ],
            "object_operations": [
                {"op": "add", "type_id": 54, "x": 128, "y": 120, "stride": 6, "status_flags": "0x7800"}
            ],
            "world_operations": [
                {"op": "add", "id": "authored_wall_0", "type": 9, "rect": [64, 64, 80, 256]}
            ],
        },
        "sha1": "fac81fdc87b76a75c9b590d58707b16fcd6a5f04",
        "checksum": "0x3E9A",
    },
    "scene5_dual_maps": {
        "manifest": {
            "schema": "truerecall.scene_patch.v1",
            "scene_index": 5,
            "allocation_base": "0x300000",
            "map_operations": [
                {"op": "set_tile", "plane": "C000", "x": 0, "y": 0, "value": "0x0002"},
                {"op": "set_tile", "plane": "E000", "x": 0, "y": 0, "value": "0x0003"},
            ],
        },
        "sha1": "b11173030e8a587e2e7d4633f8aba0e65d0116b9",
        "checksum": "0x8EF4",
    },
    "scene0_mixed_objects": {
        "manifest": {
            "schema": "truerecall.scene_patch.v1",
            "scene_index": 0,
            "allocation_base": "0x300000",
            "object_operations": [
                {"op": "replace", "base_index": 0, "x": 161}
            ],
        },
        "sha1": "c57a73e8f6ea8967a3f45b9d40b200ba8f9404c9",
        "checksum": "0x575A",
    },
    "scene6_factorized_world": {
        "manifest": {
            "schema": "truerecall.scene_patch.v1",
            "scene_index": 6,
            "allocation_base": "0x300000",
            "world_operations": [
                {"op": "replace", "id": "retail_000", "type": 11}
            ],
        },
        "sha1": "f0c146a285a7c065045179f6ea22d93d3c91ab4e",
        "checksum": "0xA53C",
    },
}


def summarize(report: dict) -> dict:
    return {
        "scene": report["scene_index"],
        "sha1": report["output_sha1"],
        "checksum": report["checksum"],
        "maps": {
            plane: {"dimensions": row["dimensions"], "changed_words": row["changed_words"]}
            for plane, row in report["maps"].items()
        },
        "objects": None if report["objects"] is None else {
            "base_count": report["objects"]["base_count"],
            "new_count": report["objects"]["new_count"],
            "stride_run_count": len(report["objects"]["stride_runs"]),
        },
        "world": None if report["world"] is None else {
            "record_count": report["world"]["record_count"],
            "payload_boundary_source": report["world"]["payload_boundary_source"],
            "retail_payload_bytes": report["world"]["retail_payload_bytes"],
            "pool_start": report["world"]["pool_start"],
            "pool_bytes": report["world"]["pool_bytes"],
        },
        "allocation_count": len(report["allocations"]),
        "scene_record_changed_offsets": report["scene_record_changed_offsets"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    results = {}
    for name, case in CASES.items():
        _out, report = build(raw, case["manifest"])
        assert report["output_sha1"] == case["sha1"], (name, report["output_sha1"])
        assert report["checksum"] == case["checksum"], (name, report["checksum"])
        results[name] = summarize(report)

    assert results["scene18_full"]["objects"] == {
        "base_count": 40, "new_count": 41, "stride_run_count": 3
    }
    assert results["scene5_dual_maps"]["maps"]["C000"]["dimensions"] == [104, 48]
    assert results["scene5_dual_maps"]["maps"]["E000"]["dimensions"] == [80, 48]
    assert results["scene0_mixed_objects"]["objects"]["stride_run_count"] == 61
    assert results["scene6_factorized_world"]["world"]["record_count"] == 375
    assert results["scene6_factorized_world"]["world"]["retail_payload_bytes"] == 0x2958

    report = {
        "schema": "truerecall.m11c.unified_scene_matrix.v1",
        "base_sha1": BASE_SHA1,
        "case_count": len(results),
        "cases": results,
        "runtime_validation": "pending",
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
