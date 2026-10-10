#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_compiler import BASE_SHA1, BASE_SIZE
from scene_compiler_v3 import compile_source_v3
from scene_graphics import export_primary_graphics
from scene_source_v2 import export_scene_source_v2
from scene_source_v3 import downgrade_v3_source, export_scene_source_v3, graphics_source_from_v3

EXPECTED_UNSUPPORTED = {10: "C000 references tile outside primary set"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    supported = []
    unsupported = []
    for scene_index in range(19):
        try:
            v2 = export_scene_source_v2(raw, scene_index)
            v3 = export_scene_source_v3(raw, scene_index)
            assert downgrade_v3_source(v3) == v2
            rebuilt_graphics = graphics_source_from_v3(v3)
            retail_graphics = export_primary_graphics(raw, scene_index)
            for key in (
                "scene_index", "retail_descriptor", "retail_primary_lz", "secondary_pointer",
                "aux_pointer", "secondary_plane_descriptor", "tile_count", "tile_bytes_hex", "decoded_sha256",
            ):
                assert rebuilt_graphics[key] == retail_graphics[key]
            out, report = compile_source_v3(raw, copy.deepcopy(v3))
            assert out == raw
            assert report["noop"] is True
            supported.append({
                "scene_index": scene_index,
                "tile_count": v3["primary_graphics"]["tile_count"],
                "decoded_sha256": v3["primary_graphics"]["retail_decoded_sha256"],
                "v2_v3_v2_lossless": True,
                "exact_noop": True,
            })
        except ValueError as exc:
            reason = str(exc)
            if EXPECTED_UNSUPPORTED.get(scene_index) != reason:
                raise
            unsupported.append({"scene_index": scene_index, "reason": reason})

    assert [row["scene_index"] for row in unsupported] == sorted(EXPECTED_UNSUPPORTED)
    assert len(supported) == 18
    assert supported[0]["scene_index"] == 0
    result = {
        "schema": "truerecall.m112a.scene_source_v3_canonical.v1",
        "base_sha1": BASE_SHA1,
        "scene_count": 19,
        "supported_scene_count": len(supported),
        "supported_scenes": [row["scene_index"] for row in supported],
        "supported_v2_v3_v2_lossless": True,
        "supported_exact_noop": True,
        "unsupported": unsupported,
        "scenes": supported,
        "scope_note": "scene10 remains outside v3 until its multi-resource graphics semantics are independently recovered",
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
