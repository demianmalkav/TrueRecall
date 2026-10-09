#!/usr/bin/env python3
"""Export/edit/compile a canonical scene-source representation.

Exported scene sources are local derived artifacts and must not be committed when
containing retail tilemaps/placements. This module itself is source-controlled.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from lzbeam_codec import decode_stream
from object_stream_codec import parse_scene
from world_collision_manifest import export_scene as export_world_scene
from scene_compiler import build as build_patch

SCENE_TABLE = 0x013B4A
PLANE_BLOCKS = {"C000": 0x16, "E000": 0x22}


def u16(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off+2], "big")


def u32(buf: bytes, off: int) -> int:
    return int.from_bytes(buf[off:off+4], "big")


def _unique_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row["id"]
        if row_id in result:
            raise ValueError(f"duplicate {label} id: {row_id}")
        result[row_id] = row
    return result


def export_scene_source(raw: bytes, scene_index: int) -> dict[str, Any]:
    scene = u32(raw, SCENE_TABLE + scene_index * 4)
    source: dict[str, Any] = {
        "schema": "truerecall.scene_source.v1",
        "scene_index": scene_index,
        "immutable": {
            "scene_flags": u16(raw, scene),
            "palette_0": u32(raw, scene + 0x02),
            "palette_1": u32(raw, scene + 0x06),
            "collision_resource_mode": u16(raw, scene + 0x12),
            "primary_plane_state_ram": u16(raw, scene + 0x14),
        },
        "planes": {},
        "objects": {},
        "world": {},
    }

    for plane_name, block_offset in PLANE_BLOCKS.items():
        graphics_descriptor = u32(raw, scene + block_offset)
        map_descriptor = u32(raw, scene + block_offset + 4)
        map_lz = u32(raw, map_descriptor)
        width = u16(raw, map_descriptor + 4)
        height = u16(raw, map_descriptor + 6)
        decoded = decode_stream(raw, map_lz)
        if len(decoded) != width * height * 2:
            raise ValueError((scene_index, plane_name, width, height, len(decoded)))
        source["planes"][plane_name] = {
            "graphics_descriptor": graphics_descriptor,
            "width": width,
            "height": height,
            "tile_words": [u16(decoded, off) for off in range(0, len(decoded), 2)],
        }

    stream = parse_scene(raw, scene_index)
    source["objects"] = {
        "prefix_hex": stream.prefix.hex(),
        "records": [
            {
                "id": f"retail_{p.index:04d}",
                "type_id": p.type_id,
                "status_flags": p.status_flags,
                "stride": p.stride,
                "x": p.x,
                "y": p.y,
                "param": p.param,
            }
            for p in stream.placements
        ],
    }

    world = export_world_scene(raw, scene_index)
    source["world"] = {
        "grid": list(world["grid"]),
        "records": [
            {"id": row["id"], "type": row["type"], "rect": list(row["rect"])}
            for row in world["records"]
        ],
    }
    return source


def source_to_patch(base: dict[str, Any], edited: dict[str, Any]) -> dict[str, Any]:
    if base.get("schema") != "truerecall.scene_source.v1" or edited.get("schema") != base.get("schema"):
        raise ValueError("unsupported scene source schema")
    if base["scene_index"] != edited["scene_index"]:
        raise ValueError("scene index changed")
    if base["immutable"] != edited["immutable"]:
        raise ValueError("immutable scene metadata changed")

    patch: dict[str, Any] = {
        "schema": "truerecall.scene_patch.v1",
        "scene_index": base["scene_index"],
        "map_operations": [],
        "object_operations": [],
        "world_operations": [],
    }

    for plane_name in PLANE_BLOCKS:
        original = base["planes"][plane_name]
        current = edited["planes"][plane_name]
        for key in ("graphics_descriptor", "width", "height"):
            if original[key] != current[key]:
                raise ValueError(f"{plane_name} immutable layout changed: {key}")
        if len(original["tile_words"]) != len(current["tile_words"]):
            raise ValueError(f"{plane_name} tile count changed")
        width = original["width"]
        for index, (before, after) in enumerate(zip(original["tile_words"], current["tile_words"])):
            if before != after:
                patch["map_operations"].append({
                    "op": "set_tile",
                    "plane": plane_name,
                    "x": index % width,
                    "y": index // width,
                    "value": after,
                })

    if base["objects"]["prefix_hex"] != edited["objects"]["prefix_hex"]:
        raise ValueError("object-stream opaque prefix changed")
    base_objects = _unique_by_id(base["objects"]["records"], "object")
    edited_objects = _unique_by_id(edited["objects"]["records"], "object")

    for object_id, original in base_objects.items():
        if object_id not in edited_objects:
            if not object_id.startswith("retail_"):
                raise ValueError(object_id)
            patch["object_operations"].append({
                "op": "remove",
                "base_index": int(object_id.split("_")[1]),
            })
            continue
        current = edited_objects[object_id]
        changes = {}
        for key in ("type_id", "status_flags", "stride", "x", "y", "param"):
            if original[key] != current[key]:
                changes[key] = current[key]
        if changes:
            if not object_id.startswith("retail_"):
                raise ValueError(f"cannot replace non-retail source id {object_id}")
            patch["object_operations"].append({
                "op": "replace",
                "base_index": int(object_id.split("_")[1]),
                **changes,
            })

    for object_id, current in edited_objects.items():
        if object_id in base_objects:
            continue
        operation = {"op": "add"}
        for key in ("type_id", "status_flags", "stride", "x", "y", "param"):
            if current.get(key) is not None:
                operation[key] = current[key]
        patch["object_operations"].append(operation)

    if base["world"]["grid"] != edited["world"]["grid"]:
        raise ValueError("world broadphase dimensions changed")
    base_world = _unique_by_id(base["world"]["records"], "world record")
    edited_world = _unique_by_id(edited["world"]["records"], "world record")

    for record_id, original in base_world.items():
        if record_id not in edited_world:
            patch["world_operations"].append({"op": "remove", "id": record_id})
            continue
        current = edited_world[record_id]
        operation = {"op": "replace", "id": record_id}
        changed = False
        for key in ("type", "rect"):
            if original[key] != current[key]:
                operation[key] = current[key]
                changed = True
        if changed:
            patch["world_operations"].append(operation)

    for record_id, current in edited_world.items():
        if record_id in base_world:
            continue
        patch["world_operations"].append({
            "op": "add",
            "id": record_id,
            "type": current["type"],
            "rect": current["rect"],
        })

    return patch


def compile_source(raw: bytes, source: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    base = export_scene_source(raw, source["scene_index"])
    patch = source_to_patch(base, source)
    if not patch["map_operations"] and not patch["object_operations"] and not patch["world_operations"]:
        return raw, {
            "schema": "truerecall.scene_source_build.v1",
            "scene_index": source["scene_index"],
            "noop": True,
            "patch": patch,
        }
    out, build_report = build_patch(raw, patch)
    return out, {
        "schema": "truerecall.scene_source_build.v1",
        "scene_index": source["scene_index"],
        "noop": False,
        "patch": patch,
        "build": build_report,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export")
    export.add_argument("rom", type=Path)
    export.add_argument("scene", type=int)
    export.add_argument("output", type=Path)

    compile_cmd = sub.add_parser("compile")
    compile_cmd.add_argument("rom", type=Path)
    compile_cmd.add_argument("source", type=Path)
    compile_cmd.add_argument("output", type=Path)
    compile_cmd.add_argument("--report", type=Path)

    args = ap.parse_args()
    raw = args.rom.read_bytes()
    if args.command == "export":
        source = export_scene_source(raw, args.scene)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return

    source = json.loads(args.source.read_text(encoding="utf-8"))
    out, report = compile_source(raw, source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
