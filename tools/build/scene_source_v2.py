#!/usr/bin/env python3
"""Versioned unified scene source with editable gameplay palette data.

M11D scene_source.v1 keeps retail palette pointers inside immutable metadata.
M11G introduces scene_source.v2 without redefining v1: the pointer identity moves
into an explicit palette section and the 64 CRAM words become editable source.

This module is intentionally a semantic/source layer. Binary palette integration
with the transactional scene compiler is a later gate; v2 lowering currently
produces the existing scene_patch.v1 plus a separate palette operation.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from scene_palette import export_scene_palette, validate_colors
from scene_source import export_scene_source, source_to_patch

SCHEMA_V1 = "truerecall.scene_source.v1"
SCHEMA_V2 = "truerecall.scene_source.v2"
PATCH_SCHEMA_V2 = "truerecall.scene_patch.v2"
PALETTE_SCHEMA_V1 = "truerecall.scene_palette.v1"


def _validate_v1_palette_identity(source_v1: dict[str, Any], palette: dict[str, Any]) -> int:
    if source_v1.get("schema") != SCHEMA_V1:
        raise ValueError("expected scene_source.v1")
    if palette.get("schema") != PALETTE_SCHEMA_V1:
        raise ValueError("expected scene_palette.v1")
    if source_v1["scene_index"] != palette["scene_index"]:
        raise ValueError("scene index mismatch between scene source and palette")

    palette0 = int(source_v1["immutable"]["palette_0"])
    palette1 = int(source_v1["immutable"]["palette_1"])
    retail_pointer = int(palette["retail_pointer"])
    if palette0 != palette1:
        raise ValueError("scene_source.v1 contains split retail palette pointers")
    if palette0 != retail_pointer:
        raise ValueError("scene source and palette retail pointer identities disagree")
    validate_colors(list(palette["colors"]))
    return retail_pointer


def upgrade_v1_source(
    source_v1: dict[str, Any],
    palette: dict[str, Any],
) -> dict[str, Any]:
    retail_pointer = _validate_v1_palette_identity(source_v1, palette)
    out = deepcopy(source_v1)
    out["schema"] = SCHEMA_V2
    immutable = dict(out["immutable"])
    immutable.pop("palette_0")
    immutable.pop("palette_1")
    out["immutable"] = immutable
    out["palette"] = {
        "retail_pointer": retail_pointer,
        "colors": list(validate_colors(list(palette["colors"]))),
    }
    return out


def validate_v2_source(source: dict[str, Any]) -> None:
    if source.get("schema") != SCHEMA_V2:
        raise ValueError("expected scene_source.v2")
    if "palette_0" in source["immutable"] or "palette_1" in source["immutable"]:
        raise ValueError("scene_source.v2 must not duplicate palette pointers in immutable metadata")
    palette = source.get("palette")
    if not isinstance(palette, dict):
        raise ValueError("scene_source.v2 palette section missing")
    if "retail_pointer" not in palette:
        raise ValueError("scene_source.v2 palette retail_pointer missing")
    if int(palette["retail_pointer"]) < 0:
        raise ValueError("negative palette pointer")
    validate_colors(list(palette["colors"]))


def downgrade_v2_source(source_v2: dict[str, Any]) -> dict[str, Any]:
    validate_v2_source(source_v2)
    out = deepcopy(source_v2)
    palette = out.pop("palette")
    retail_pointer = int(palette["retail_pointer"])
    out["schema"] = SCHEMA_V1
    immutable = dict(out["immutable"])
    immutable["palette_0"] = retail_pointer
    immutable["palette_1"] = retail_pointer
    out["immutable"] = immutable
    return out


def palette_source_from_v2(source_v2: dict[str, Any]) -> dict[str, Any]:
    validate_v2_source(source_v2)
    palette = source_v2["palette"]
    return {
        "schema": PALETTE_SCHEMA_V1,
        "scene_index": source_v2["scene_index"],
        "retail_pointer": int(palette["retail_pointer"]),
        "colors": list(validate_colors(list(palette["colors"]))),
    }


def export_scene_source_v2(raw: bytes, scene_index: int) -> dict[str, Any]:
    source_v1 = export_scene_source(raw, scene_index)
    palette = export_scene_palette(raw, scene_index)
    return upgrade_v1_source(source_v1, palette)


def source_v2_to_patch(base: dict[str, Any], edited: dict[str, Any]) -> dict[str, Any]:
    validate_v2_source(base)
    validate_v2_source(edited)
    if base["scene_index"] != edited["scene_index"]:
        raise ValueError("scene index changed")

    base_pointer = int(base["palette"]["retail_pointer"])
    edited_pointer = int(edited["palette"]["retail_pointer"])
    if base_pointer != edited_pointer:
        raise ValueError("palette retail pointer identity changed")

    scene_patch = source_to_patch(
        downgrade_v2_source(base),
        downgrade_v2_source(edited),
    )

    before_colors = list(validate_colors(list(base["palette"]["colors"])))
    after_colors = list(validate_colors(list(edited["palette"]["colors"])))
    changed_indices = [
        index
        for index, (before, after) in enumerate(zip(before_colors, after_colors))
        if before != after
    ]
    palette_operation = None
    if changed_indices:
        palette_operation = {
            "op": "replace_palette",
            "retail_pointer": base_pointer,
            "changed_indices": changed_indices,
            "colors": after_colors,
        }

    return {
        "schema": PATCH_SCHEMA_V2,
        "scene_index": base["scene_index"],
        "scene_patch": scene_patch,
        "palette_operation": palette_operation,
    }


def patch_v2_is_noop(patch: dict[str, Any]) -> bool:
    if patch.get("schema") != PATCH_SCHEMA_V2:
        raise ValueError("expected scene_patch.v2")
    scene_patch = patch["scene_patch"]
    return (
        not scene_patch["map_operations"]
        and not scene_patch["object_operations"]
        and not scene_patch["world_operations"]
        and patch["palette_operation"] is None
    )


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
        source = export_scene_source_v2(args.rom.read_bytes(), args.scene)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
        print(args.output)
        return

    base = json.loads(args.base.read_text(encoding="utf-8"))
    edited = json.loads(args.edited.read_text(encoding="utf-8"))
    print(json.dumps(source_v2_to_patch(base, edited), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
