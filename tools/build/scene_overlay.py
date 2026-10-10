#!/usr/bin/env python3
"""Apply source-controlled authored deltas above canonical scene_source.v3.

Overlay manifests intentionally contain only project-authored changes plus stable
retail identity guards. They must never embed a full exported retail scene.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from scene_compiler import BASE_SHA1
from scene_compiler_v3 import compile_source_v3
from scene_graphics import TILE_BYTES
from scene_source_v3 import export_scene_source_v3, validate_v3_source

SCHEMA_OVERLAY_V1 = "truerecall.scene_overlay.v1"


def parse_int(value: Any) -> int:
    if isinstance(value, str):
        return int(value, 0)
    return int(value)


def _rows_by_id(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row["id"])
        if row_id in out:
            raise ValueError(f"duplicate {label} id: {row_id}")
        out[row_id] = row
    return out


def validate_overlay(overlay: dict[str, Any]) -> None:
    if overlay.get("schema") != SCHEMA_OVERLAY_V1:
        raise ValueError("expected scene_overlay.v1")
    if parse_int(overlay.get("scene_index", -1)) < 0:
        raise ValueError("invalid scene_index")
    identity = overlay.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("overlay identity missing")
    if str(identity.get("base_sha1", "")).lower() != BASE_SHA1:
        raise ValueError("overlay canonical base identity mismatch")
    for section in ("palette", "maps", "objects", "world", "primary_graphics"):
        if section not in overlay or not isinstance(overlay[section], list):
            raise ValueError(f"overlay {section} must be a list")


def _validate_identity(source: dict[str, Any], overlay: dict[str, Any]) -> None:
    validate_v3_source(source)
    validate_overlay(overlay)
    if int(source["scene_index"]) != parse_int(overlay["scene_index"]):
        raise ValueError("overlay scene index mismatch")
    identity = overlay["identity"]
    if parse_int(identity["palette_retail_pointer"]) != int(source["palette"]["retail_pointer"]):
        raise ValueError("overlay palette retail identity mismatch")
    graphics = source["primary_graphics"]
    expected = identity["primary_graphics"]
    for field in ("retail_descriptor", "retail_primary_lz", "secondary_pointer", "aux_pointer", "secondary_plane_descriptor"):
        if parse_int(expected[field]) != int(graphics[field]):
            raise ValueError(f"overlay primary graphics identity mismatch: {field}")
    if str(expected["retail_decoded_sha256"]).lower() != str(graphics["retail_decoded_sha256"]).lower():
        raise ValueError("overlay primary graphics fingerprint mismatch")


def apply_overlay_to_source(source: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    _validate_identity(source, overlay)
    edited = deepcopy(source)

    seen_palette: set[int] = set()
    for op in overlay["palette"]:
        index = parse_int(op["index"])
        if index in seen_palette or not 0 <= index < 64:
            raise ValueError(f"invalid/duplicate palette index: {index}")
        seen_palette.add(index)
        before = int(edited["palette"]["colors"][index])
        if "expect" in op and before != parse_int(op["expect"]):
            raise ValueError(f"palette expectation mismatch at {index}: 0x{before:04X}")
        edited["palette"]["colors"][index] = parse_int(op["value"])

    for op in overlay["maps"]:
        plane = str(op["plane"])
        if plane not in edited["planes"]:
            raise ValueError(f"unknown plane: {plane}")
        action = str(op.get("op", "set_tile"))
        plane_row = edited["planes"][plane]
        plane_width = int(plane_row["width"])
        plane_height = int(plane_row["height"])
        x, y = parse_int(op["x"]), parse_int(op["y"])
        if action == "set_tile":
            if not (0 <= x < plane_width and 0 <= y < plane_height):
                raise ValueError(f"map coordinate outside {plane}: {(x, y)}")
            index = y * plane_width + x
            before = int(plane_row["tile_words"][index])
            if "expect" in op and before != parse_int(op["expect"]):
                raise ValueError(f"map expectation mismatch {plane} {(x, y)}: 0x{before:04X}")
            plane_row["tile_words"][index] = parse_int(op["value"])
        elif action == "replace_rect":
            rect_width = parse_int(op["width"])
            rect_height = parse_int(op["height"])
            if rect_width <= 0 or rect_height <= 0 or x < 0 or y < 0 or x + rect_width > plane_width or y + rect_height > plane_height:
                raise ValueError(f"map rectangle outside {plane}: {(x, y, rect_width, rect_height)}")
            indices = [
                (y + dy) * plane_width + (x + dx)
                for dy in range(rect_height)
                for dx in range(rect_width)
            ]
            original_words = [int(plane_row["tile_words"][index]) for index in indices]
            original_bytes = b"".join(word.to_bytes(2, "big") for word in original_words)
            if "expect_sha256" in op and hashlib.sha256(original_bytes).hexdigest() != str(op["expect_sha256"]).lower():
                raise ValueError(f"map rectangle expectation mismatch {plane} {(x, y, rect_width, rect_height)}")
            authored_words = [parse_int(value) for value in op["tile_words"]]
            if len(authored_words) != len(indices):
                raise ValueError("map replace_rect tile_words length mismatch")
            for index, value in zip(indices, authored_words):
                plane_row["tile_words"][index] = value
        else:
            raise ValueError(f"unsupported map overlay operation: {action}")

    object_rows = edited["objects"]["records"]
    for op in overlay["objects"]:
        by_id = _rows_by_id(object_rows, "object")
        action = str(op["op"])
        row_id = str(op["id"])
        if action == "add":
            if row_id in by_id:
                raise ValueError(f"object already exists: {row_id}")
            row = {"id": row_id}
            for key in ("type_id", "status_flags", "stride", "x", "y", "param"):
                row[key] = None if op.get(key) is None else parse_int(op[key])
            for required in ("type_id", "status_flags", "stride", "x", "y"):
                if row[required] is None:
                    raise ValueError(f"missing object field {required}")
            object_rows.append(row)
        elif action == "remove":
            if row_id not in by_id:
                raise ValueError(f"object not found: {row_id}")
            object_rows.remove(by_id[row_id])
        elif action == "replace":
            if row_id not in by_id:
                raise ValueError(f"object not found: {row_id}")
            row = by_id[row_id]
            for key in ("type_id", "status_flags", "stride", "x", "y", "param"):
                if key in op:
                    row[key] = None if op[key] is None else parse_int(op[key])
        else:
            raise ValueError(f"unsupported object overlay operation: {action}")

    world_rows = edited["world"]["records"]
    for op in overlay["world"]:
        by_id = _rows_by_id(world_rows, "world record")
        action = str(op["op"])
        row_id = str(op["id"])
        if action == "add":
            if row_id in by_id:
                raise ValueError(f"world record already exists: {row_id}")
            rect = [parse_int(v) for v in op["rect"]]
            if len(rect) != 4:
                raise ValueError("world rect must have four coordinates")
            world_rows.append({"id": row_id, "type": parse_int(op["type"]), "rect": rect})
        elif action == "remove":
            if row_id not in by_id:
                raise ValueError(f"world record not found: {row_id}")
            world_rows.remove(by_id[row_id])
        elif action == "replace":
            if row_id not in by_id:
                raise ValueError(f"world record not found: {row_id}")
            row = by_id[row_id]
            if "type" in op:
                row["type"] = parse_int(op["type"])
            if "rect" in op:
                rect = [parse_int(v) for v in op["rect"]]
                if len(rect) != 4:
                    raise ValueError("world rect must have four coordinates")
                row["rect"] = rect
        else:
            raise ValueError(f"unsupported world overlay operation: {action}")

    graphics_payload = bytearray.fromhex(edited["primary_graphics"]["tile_bytes_hex"])
    seen_tiles: set[int] = set()
    for op in overlay["primary_graphics"]:
        index = parse_int(op["tile_index"])
        if index in seen_tiles:
            raise ValueError(f"duplicate primary graphics tile: {index}")
        seen_tiles.add(index)
        start, end = index * TILE_BYTES, (index + 1) * TILE_BYTES
        if not 0 <= start < end <= len(graphics_payload):
            raise ValueError(f"primary graphics tile outside payload: {index}")
        before = bytes(graphics_payload[start:end])
        if "expect_sha256" in op and hashlib.sha256(before).hexdigest() != str(op["expect_sha256"]).lower():
            raise ValueError(f"primary graphics expectation mismatch at tile {index}")
        authored = bytes.fromhex(str(op["tile_hex"]))
        if len(authored) != TILE_BYTES:
            raise ValueError(f"authored tile {index} must be exactly {TILE_BYTES} bytes")
        graphics_payload[start:end] = authored
    edited["primary_graphics"]["tile_bytes_hex"] = bytes(graphics_payload).hex()

    validate_v3_source(edited)
    return edited


def compile_overlay(raw: bytes, overlay: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    if hashlib.sha1(raw).hexdigest() != BASE_SHA1:
        raise ValueError("wrong canonical ROM")
    validate_overlay(overlay)
    source = export_scene_source_v3(raw, parse_int(overlay["scene_index"]))
    edited = apply_overlay_to_source(source, overlay)
    out, source_report = compile_source_v3(raw, edited)
    return out, {
        "schema": "truerecall.scene_overlay_build.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": parse_int(overlay["scene_index"]),
        "overlay_id": str(overlay.get("id", "unnamed")),
        "source_build": source_report,
        "output_sha1": hashlib.sha1(out).hexdigest(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("overlay", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    out, report = compile_overlay(args.rom.read_bytes(), overlay)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
