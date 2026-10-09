#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from world_collision_codec import SCENE_COUNT, assert_retail_exact_scene
from world_collision_manifest import export_scene, apply_ops, compile_manifest

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest()
    assert digest == EXPECTED_SHA1

    noops = []
    for scene_index in range(SCENE_COUNT):
        layout = assert_retail_exact_scene(rom, scene_index)
        manifest = export_scene(rom, scene_index)
        built = compile_manifest(manifest)
        resource = rom[layout["world_base"]:]
        assert built["grid"] == bytes(resource[:layout["grid_bytes"]])
        assert built["pool"] == bytes(resource[layout["pool_start"]:layout["pool_end"]])
        assert built["memberships"] == layout["retail_memberships"]
        noops.append(scene_index)

    scene18 = export_scene(rom, 18)
    assert scene18["grid"] == [9, 20]
    assert scene18["records"] == []

    authored = apply_ops(scene18, [{
        "op": "add",
        "id": "authored_wall_0",
        "offset": 0x0200,
        "type": 9,
        "rect": [64, 64, 80, 256],
    }])
    built = compile_manifest(authored, pool_start=0x0180)
    changed = [i for i, refs in enumerate(built["memberships"]) if refs]
    assert changed == [10, 19, 28]
    assert len(built["pool"]) == 2
    assert built["record_bytes"][0x0200] == bytes.fromhex("00090040004000500100")
    assert all(built["memberships"][i] == (0x0200,) for i in changed)

    report = {
        "schema": "truerecall.m10f.world_manifest.v1",
        "base_sha1": digest,
        "noop_roundtrip_scenes": len(noops),
        "scene18_add": {
            "grid": scene18["grid"],
            "record_offset": "0x0200",
            "type": 9,
            "rect": [64, 64, 80, 256],
            "pool_start": "0x0180",
            "pool_bytes": len(built["pool"]),
            "changed_cells": changed,
            "changed_cell_xy": [[i % 9, i // 9] for i in changed],
        },
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
