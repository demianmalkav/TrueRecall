#!/usr/bin/env python3
"""Scene-source v3: v2 scene/palette source plus confirmed primary graphics.

v1 and v2 remain immutable regression anchors. v3 adds only the primary gameplay
graphics payload whose descriptor semantics were runtime-confirmed by M1.1B.
Secondary/auxiliary graphics identities are preserved but not interpreted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from scene_graphics import TILE_BYTES, export_primary_graphics
from scene_source_v2 import (
    PATCH_SCHEMA_V2,
    SCHEMA_V2,
    export_scene_source_v2,
    patch_v2_is_noop,
    source_v2_to_patch,
    validate_v2_source,
)

SCHEMA_V3 = "truerecall.scene_source.v3"
PATCH_SCHEMA_V3 = "truerecall.scene_patch.v3"
GRAPHICS_SCHEMA_V1 = "truerecall.scene_primary_graphics.v1"
IDENTITY_FIELDS = (
    "retail_descriptor",
    "retail_primary_lz",
    "secondary_pointer",
    "aux_pointer",
    "secondary_plane_descriptor",
    "retail_decoded_sha256",
)


def _graphics_section_from_v1(graphics: dict[str, Any]) -> dict[str, Any]:
    if graphics.get("schema") != GRAPHICS_SCHEMA_V1:
        raise ValueError("expected scene_primary_graphics.v1")
    payload = bytes.fromhex(graphics["tile_bytes_hex"])
    if not payload or len(payload) % TILE_BYTES:
        raise ValueError("primary graphics payload must contain complete Genesis tiles")
    tile_count = len(payload) // TILE_BYTES
    if int(graphics["tile_count"]) != tile_count:
        raise ValueError("primary graphics tile_count mismatch")
    decoded_sha256 = hashlib.sha256(payload).hexdigest()
    if decoded_sha256 != str(graphics["decoded_sha256"]):
        raise ValueError("primary graphics decoded fingerprint mismatch")
    return {
        "retail_descriptor": int(graphics["retail_descriptor"]),
        "retail_primary_lz": int(graphics["retail_primary_lz"]),
        "secondary_pointer": int(graphics["secondary_pointer"]),
        "aux_pointer": int(graphics["aux_pointer"]),
        "secondary_plane_descriptor": int(graphics["secondary_plane_descriptor"]),
        "retail_decoded_sha256": decoded_sha256,
        "tile_count": tile_count,
        "tile_bytes_hex": payload.hex(),
    }


def upgrade_v2_source(source_v2: dict[str, Any], graphics: dict[str, Any]) -> dict[str, Any]:
    validate_v2_source(source_v2)
    if int(source_v2["scene_index"]) != int(graphics["scene_index"]):
        raise ValueError("scene index mismatch between source v2 and primary graphics")
    out = deepcopy(source_v2)
    out["schema"] = SCHEMA_V3
    out["primary_graphics"] = _graphics_section_from_v1(graphics)
    validate_v3_source(out)
    return out


def validate_v3_source(source: dict[str, Any]) -> None:
    if source.get("schema") != SCHEMA_V3:
        raise ValueError("expected scene_source.v3")
    v2 = deepcopy(source)
    graphics = v2.pop("primary_graphics", None)
    v2["schema"] = SCHEMA_V2
    validate_v2_source(v2)
    if not isinstance(graphics, dict):
        raise ValueError("scene_source.v3 primary_graphics section missing")
    for field in IDENTITY_FIELDS[:-1]:
        value = int(graphics[field])
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError(f"primary graphics identity out of range: {field}")
    fingerprint = str(graphics["retail_decoded_sha256"])
    if len(fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in fingerprint.lower()):
        raise ValueError("invalid primary graphics retail_decoded_sha256")
    payload = bytes.fromhex(graphics["tile_bytes_hex"])
    if not payload or len(payload) % TILE_BYTES:
        raise ValueError("primary graphics payload must contain complete Genesis tiles")
    if int(graphics["tile_count"]) != len(payload) // TILE_BYTES:
        raise ValueError("primary graphics tile_count mismatch")


def downgrade_v3_source(source_v3: dict[str, Any]) -> dict[str, Any]:
    validate_v3_source(source_v3)
    out = deepcopy(source_v3)
    out.pop("primary_graphics")
    out["schema"] = SCHEMA_V2
    return out


def graphics_source_from_v3(source_v3: dict[str, Any]) -> dict[str, Any]:
    validate_v3_source(source_v3)
    g = source_v3["primary_graphics"]
    payload = bytes.fromhex(g["tile_bytes_hex"])
    return {
        "schema": GRAPHICS_SCHEMA_V1,
        "scene_index": int(source_v3["scene_index"]),
        "retail_descriptor": int(g["retail_descriptor"]),
        "retail_primary_lz": int(g["retail_primary_lz"]),
        "secondary_pointer": int(g["secondary_pointer"]),
        "aux_pointer": int(g["aux_pointer"]),
        "secondary_plane_descriptor": int(g["secondary_plane_descriptor"]),
        "tile_count": int(g["tile_count"]),
        "tile_bytes_hex": payload.hex(),
        "decoded_sha256": hashlib.sha256(payload).hexdigest(),
    }


def export_scene_source_v3(raw: bytes, scene_index: int) -> dict[str, Any]:
    source_v2 = export_scene_source_v2(raw, scene_index)
    graphics = export_primary_graphics(raw, scene_index)
    return upgrade_v2_source(source_v2, graphics)


def source_v3_to_patch(base: dict[str, Any], edited: dict[str, Any]) -> dict[str, Any]:
    validate_v3_source(base)
    validate_v3_source(edited)
    if int(base["scene_index"]) != int(edited["scene_index"]):
        raise ValueError("scene index changed")

    bg = base["primary_graphics"]
    eg = edited["primary_graphics"]
    for field in IDENTITY_FIELDS:
        if str(bg[field]) != str(eg[field]):
            raise ValueError(f"primary graphics immutable identity changed: {field}")

    scene_patch_v2 = source_v2_to_patch(downgrade_v3_source(base), downgrade_v3_source(edited))
    if scene_patch_v2.get("schema") != PATCH_SCHEMA_V2:
        raise AssertionError("v3 lowering failed to produce scene_patch.v2")

    before = bytes.fromhex(bg["tile_bytes_hex"])
    after = bytes.fromhex(eg["tile_bytes_hex"])
    before_count = int(bg["tile_count"])
    after_count = int(eg["tile_count"])
    changed_tiles = [
        index
        for index in range(max(before_count, after_count))
        if before[index*TILE_BYTES:(index+1)*TILE_BYTES]
        != after[index*TILE_BYTES:(index+1)*TILE_BYTES]
    ]
    graphics_operation = None
    if changed_tiles:
        graphics_operation = {
            "op": "replace_primary_graphics",
            "retail_descriptor": int(bg["retail_descriptor"]),
            "retail_primary_lz": int(bg["retail_primary_lz"]),
            "secondary_pointer": int(bg["secondary_pointer"]),
            "aux_pointer": int(bg["aux_pointer"]),
            "secondary_plane_descriptor": int(bg["secondary_plane_descriptor"]),
            "retail_decoded_sha256": str(bg["retail_decoded_sha256"]),
            "changed_tile_indices": changed_tiles,
            "tile_count": after_count,
            "tile_bytes_hex": after.hex(),
        }

    return {
        "schema": PATCH_SCHEMA_V3,
        "scene_index": int(base["scene_index"]),
        "scene_patch_v2": scene_patch_v2,
        "graphics_operation": graphics_operation,
    }


def patch_v3_is_noop(patch: dict[str, Any]) -> bool:
    if patch.get("schema") != PATCH_SCHEMA_V3:
        raise ValueError("expected scene_patch.v3")
    return patch_v2_is_noop(patch["scene_patch_v2"]) and patch.get("graphics_operation") is None


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("rom", type=Path)
    export.add_argument("scene", type=int)
    export.add_argument("output", type=Path)
    diff = sub.add_parser("diff")
    diff.add_argument("base", type=Path)
    diff.add_argument("edited", type=Path)
    args = ap.parse_args()
    if args.command == "export":
        source = export_scene_source_v3(args.rom.read_bytes(), args.scene)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return
    base = json.loads(args.base.read_text(encoding="utf-8"))
    edited = json.loads(args.edited.read_text(encoding="utf-8"))
    print(json.dumps(source_v3_to_patch(base, edited), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
