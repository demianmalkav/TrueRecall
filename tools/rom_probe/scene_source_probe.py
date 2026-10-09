#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_source import export_scene_source, source_to_patch, compile_source

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
BASE_SIZE = 2_097_152
EDITED_SHA1 = "fac81fdc87b76a75c9b590d58707b16fcd6a5f04"
EDITED_CHECKSUM = "0x3E9A"

EXPECTED_EXPORTS = {
    0:  {"bytes": 62331, "sha256": "1c90c93e179f4c129dbc1731f952c33219eb97ca6024ad0396d9685b0aa64506", "c000": 4815, "e000": 4815, "objects": 168, "world": 375},
    5:  {"bytes": 51584, "sha256": "1e6cb5346e9fb0cd8dbd0f98887f4ebc2eda12c07601879a37e064f655ea38c7", "c000": 4992, "e000": 3840, "objects": 139, "world": 314},
    6:  {"bytes": 72949, "sha256": "d730b42284381d5a6aabf363b13311187e337260f6f7456ab4839b165db97e76", "c000": 7810, "e000": 5720, "objects": 206, "world": 375},
    18: {"bytes": 8186,  "sha256": "e9ad0394694941c4cc10d31250ed06cbd394da42c57567e59b244dcaf9f452eb", "c000": 720,  "e000": 720,  "objects": 40,  "world": 0},
}


def canonical_bytes(source: dict) -> bytes:
    return json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    exports = {}
    for scene_index, expected in EXPECTED_EXPORTS.items():
        source = export_scene_source(raw, scene_index)
        encoded = canonical_bytes(source)
        assert len(encoded) == expected["bytes"]
        assert hashlib.sha256(encoded).hexdigest() == expected["sha256"]
        assert len(source["planes"]["C000"]["tile_words"]) == expected["c000"]
        assert len(source["planes"]["E000"]["tile_words"]) == expected["e000"]
        assert len(source["objects"]["records"]) == expected["objects"]
        assert len(source["world"]["records"]) == expected["world"]

        patch = source_to_patch(source, copy.deepcopy(source))
        assert patch["map_operations"] == []
        assert patch["object_operations"] == []
        assert patch["world_operations"] == []
        no_op_rom, no_op_report = compile_source(raw, source)
        assert no_op_rom == raw
        assert no_op_report["noop"] is True

        exports[str(scene_index)] = {
            "canonical_json_bytes": len(encoded),
            "canonical_json_sha256": hashlib.sha256(encoded).hexdigest(),
            "c000_words": expected["c000"],
            "e000_words": expected["e000"],
            "objects": expected["objects"],
            "world_records": expected["world"],
            "exact_rom_noop": True,
        }

    # Edit scene 18 at source level, not by writing patch operations.
    source = export_scene_source(raw, 18)
    source["planes"]["C000"]["tile_words"][0] = 0x0001
    source["objects"]["records"].append({
        "id": "new_health_0",
        "type_id": 54,
        "status_flags": 0x7800,
        "stride": 6,
        "x": 128,
        "y": 120,
        "param": None,
    })
    source["world"]["records"].append({
        "id": "new_wall_0",
        "type": 9,
        "rect": [64, 64, 80, 256],
    })

    base = export_scene_source(raw, 18)
    patch = source_to_patch(base, source)
    assert patch == {
        "schema": "truerecall.scene_patch.v1",
        "scene_index": 18,
        "map_operations": [
            {"op": "set_tile", "plane": "C000", "x": 0, "y": 0, "value": 1}
        ],
        "object_operations": [
            {"op": "add", "type_id": 54, "status_flags": 0x7800, "stride": 6, "x": 128, "y": 120}
        ],
        "world_operations": [
            {"op": "add", "id": "new_wall_0", "type": 9, "rect": [64, 64, 80, 256]}
        ],
    }

    edited_rom, edited_report = compile_source(raw, source)
    assert hashlib.sha1(edited_rom).hexdigest() == EDITED_SHA1
    assert edited_report["build"]["checksum"] == EDITED_CHECKSUM

    report = {
        "schema": "truerecall.m11d.scene_source.v1",
        "base_sha1": BASE_SHA1,
        "representative_exports": exports,
        "edited_scene18": {
            "auto_patch": patch,
            "output_sha1": hashlib.sha1(edited_rom).hexdigest(),
            "checksum": edited_report["build"]["checksum"],
            "matches_m11b": True,
        },
        "policy": "Exported retail-derived scene source files remain local and are not committed.",
        "runtime_validation": "pending",
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
