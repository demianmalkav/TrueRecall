#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_source import export_scene_source, source_to_patch, compile_source

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 2_097_152
SCENE_COUNT = 19

M11D_ADD_SHA1 = "fac81fdc87b76a75c9b590d58707b16fcd6a5f04"
M11D_ADD_CHECKSUM = "0x3E9A"
M11C_OBJECT_REPLACE_SHA1 = "c57a73e8f6ea8967a3f45b9d40b200ba8f9404c9"
M11C_OBJECT_REPLACE_CHECKSUM = "0x575A"
M11C_WORLD_REPLACE_SHA1 = "f0c146a285a7c065045179f6ea22d93d3c91ab4e"
M11C_WORLD_REPLACE_CHECKSUM = "0xA53C"


def canonical_bytes(source: dict[str, Any]) -> bytes:
    return json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")


def assert_zero_patch(patch: dict[str, Any]) -> None:
    assert patch["map_operations"] == []
    assert patch["object_operations"] == []
    assert patch["world_operations"] == []


def summarize_source(source: dict[str, Any]) -> dict[str, Any]:
    encoded = canonical_bytes(source)
    return {
        "canonical_json_bytes": len(encoded),
        "canonical_json_sha256": hashlib.sha256(encoded).hexdigest(),
        "c000_dimensions": [
            source["planes"]["C000"]["width"],
            source["planes"]["C000"]["height"],
        ],
        "c000_words": len(source["planes"]["C000"]["tile_words"]),
        "e000_dimensions": [
            source["planes"]["E000"]["width"],
            source["planes"]["E000"]["height"],
        ],
        "e000_words": len(source["planes"]["E000"]["tile_words"]),
        "objects": len(source["objects"]["records"]),
        "world_grid": list(source["world"]["grid"]),
        "world_records": len(source["world"]["records"]),
    }


def assert_source_shape(source: dict[str, Any], scene_index: int) -> None:
    assert source["schema"] == "truerecall.scene_source.v1"
    assert source["scene_index"] == scene_index

    for plane_name in ("C000", "E000"):
        plane = source["planes"][plane_name]
        assert plane["width"] > 0
        assert plane["height"] > 0
        assert len(plane["tile_words"]) == plane["width"] * plane["height"]

    object_ids = [row["id"] for row in source["objects"]["records"]]
    assert len(object_ids) == len(set(object_ids))
    assert object_ids == [f"retail_{i:04d}" for i in range(len(object_ids))]

    world_ids = [row["id"] for row in source["world"]["records"]]
    assert len(world_ids) == len(set(world_ids))
    assert world_ids == [f"retail_{i:03d}" for i in range(len(world_ids))]

    grid_w, grid_h = source["world"]["grid"]
    assert grid_w > 0
    assert grid_h > 0


def compile_case(
    raw: bytes,
    name: str,
    base: dict[str, Any],
    edited: dict[str, Any],
) -> dict[str, Any]:
    patch = source_to_patch(base, edited)
    assert (
        patch["map_operations"]
        or patch["object_operations"]
        or patch["world_operations"]
    ), f"{name}: edit unexpectedly produced a no-op patch"

    out, report = compile_source(raw, edited)
    assert out != raw
    assert report["noop"] is False
    assert report["patch"] == patch
    assert report["build"]["output_sha1"] == hashlib.sha1(out).hexdigest()

    return {
        "scene": edited["scene_index"],
        "patch": patch,
        "output_sha1": hashlib.sha1(out).hexdigest(),
        "checksum": report["build"]["checksum"],
        "object_count": None
        if report["build"]["objects"] is None
        else report["build"]["objects"]["new_count"],
        "world_record_count": None
        if report["build"]["world"] is None
        else report["build"]["world"]["record_count"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    exports: dict[str, Any] = {}
    bases: dict[int, dict[str, Any]] = {}

    for scene_index in range(SCENE_COUNT):
        source = export_scene_source(raw, scene_index)
        assert_source_shape(source, scene_index)

        patch = source_to_patch(source, copy.deepcopy(source))
        assert_zero_patch(patch)

        no_op_rom, no_op_report = compile_source(raw, source)
        assert no_op_rom == raw
        assert no_op_report["noop"] is True
        assert_zero_patch(no_op_report["patch"])

        exports[str(scene_index)] = {
            **summarize_source(source),
            "exact_rom_noop": True,
        }
        bases[scene_index] = source

    cases: dict[str, Any] = {}

    # Preserve the M11D add proof as a deterministic regression anchor.
    add_base = bases[18]
    add_edit = copy.deepcopy(add_base)
    add_edit["planes"]["C000"]["tile_words"][0] = 0x0001
    add_edit["objects"]["records"].append(
        {
            "id": "new_health_0",
            "type_id": 54,
            "status_flags": 0x7800,
            "stride": 6,
            "x": 128,
            "y": 120,
            "param": None,
        }
    )
    add_edit["world"]["records"].append(
        {
            "id": "new_wall_0",
            "type": 9,
            "rect": [64, 64, 80, 256],
        }
    )
    add_result = compile_case(raw, "scene18_add", add_base, add_edit)
    assert add_result["output_sha1"] == M11D_ADD_SHA1
    assert add_result["checksum"] == M11D_ADD_CHECKSUM
    assert add_result["object_count"] == len(add_base["objects"]["records"]) + 1
    assert add_result["world_record_count"] == 1
    cases["scene18_add"] = add_result

    # Source-level replace: edit a retail placement by stable source id.
    replace_object_base = bases[0]
    replace_object_edit = copy.deepcopy(replace_object_base)
    replace_object_edit["objects"]["records"][0]["x"] += 1
    replace_object_result = compile_case(
        raw,
        "scene0_object_replace",
        replace_object_base,
        replace_object_edit,
    )
    assert replace_object_result["patch"]["object_operations"] == [
        {
            "op": "replace",
            "base_index": 0,
            "x": replace_object_edit["objects"]["records"][0]["x"],
        }
    ]
    assert replace_object_result["output_sha1"] == M11C_OBJECT_REPLACE_SHA1
    assert replace_object_result["checksum"] == M11C_OBJECT_REPLACE_CHECKSUM
    assert replace_object_result["object_count"] == len(
        replace_object_base["objects"]["records"]
    )
    cases["scene0_object_replace"] = replace_object_result

    # Source-level remove: delete a retail placement by stable source id.
    remove_object_base = bases[0]
    remove_object_edit = copy.deepcopy(remove_object_base)
    removed_object = remove_object_edit["objects"]["records"].pop(0)
    remove_object_result = compile_case(
        raw,
        "scene0_object_remove",
        remove_object_base,
        remove_object_edit,
    )
    assert removed_object["id"] == "retail_0000"
    assert remove_object_result["patch"]["object_operations"] == [
        {"op": "remove", "base_index": 0}
    ]
    assert remove_object_result["object_count"] == len(
        remove_object_base["objects"]["records"]
    ) - 1
    cases["scene0_object_remove"] = remove_object_result

    # Exercise the scene-6 factorized broadphase layout with source-level replace.
    replace_world_base = bases[6]
    assert replace_world_base["world"]["records"]
    replace_world_edit = copy.deepcopy(replace_world_base)
    before_type = replace_world_edit["world"]["records"][0]["type"]
    after_type = 11 if before_type != 11 else 9
    replace_world_edit["world"]["records"][0]["type"] = after_type
    replace_world_result = compile_case(
        raw,
        "scene6_world_replace",
        replace_world_base,
        replace_world_edit,
    )
    assert replace_world_result["patch"]["world_operations"] == [
        {"op": "replace", "id": "retail_000", "type": after_type}
    ]
    assert replace_world_result["output_sha1"] == M11C_WORLD_REPLACE_SHA1
    assert replace_world_result["checksum"] == M11C_WORLD_REPLACE_CHECKSUM
    assert replace_world_result["world_record_count"] == len(
        replace_world_base["world"]["records"]
    )
    cases["scene6_world_replace"] = replace_world_result

    # Source-level remove against the same non-trivial world layout.
    remove_world_base = bases[6]
    remove_world_edit = copy.deepcopy(remove_world_base)
    removed_world = remove_world_edit["world"]["records"].pop(0)
    remove_world_result = compile_case(
        raw,
        "scene6_world_remove",
        remove_world_base,
        remove_world_edit,
    )
    assert removed_world["id"] == "retail_000"
    assert remove_world_result["patch"]["world_operations"] == [
        {"op": "remove", "id": "retail_000"}
    ]
    assert remove_world_result["world_record_count"] == len(
        remove_world_base["world"]["records"]
    ) - 1
    cases["scene6_world_remove"] = remove_world_result

    report = {
        "schema": "truerecall.m11e.scene_source_matrix.v1",
        "base_sha1": BASE_SHA1,
        "scene_count": SCENE_COUNT,
        "all_scene_noop_exact": True,
        "exports": exports,
        "edit_case_count": len(cases),
        "edit_cases": cases,
        "coverage": {
            "add": True,
            "replace": True,
            "remove": True,
            "mixed_stride_object_scene": 0,
            "factorized_world_scene": 6,
            "empty_world_scene": 18,
        },
        "runtime_validation": "pending",
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
