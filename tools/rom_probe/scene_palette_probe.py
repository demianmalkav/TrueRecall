#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_palette import (
    BASE_SHA1,
    BASE_SIZE,
    CRAM_MASK,
    PALETTE_WORDS,
    SCENE_COUNT,
    compile_palette,
    export_scene_palette,
)


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

    scenes = {}
    exports = {}
    for scene_index in range(SCENE_COUNT):
        source = export_scene_palette(raw, scene_index)
        assert source["schema"] == "truerecall.scene_palette.v1"
        assert source["scene_index"] == scene_index
        assert len(source["colors"]) == PALETTE_WORDS
        assert all((value & ~CRAM_MASK) == 0 for value in source["colors"])

        encoded = canonical_bytes(source)
        no_op_rom, no_op_report = compile_palette(raw, copy.deepcopy(source))
        assert no_op_rom == raw
        assert no_op_report["noop"] is True
        assert no_op_report["changed_color_indices"] == []
        assert no_op_report["output_sha1"] == BASE_SHA1

        scenes[str(scene_index)] = {
            "retail_pointer": source["retail_pointer"],
            "canonical_json_bytes": len(encoded),
            "canonical_json_sha256": hashlib.sha256(encoded).hexdigest(),
            "exact_rom_noop": True,
        }
        exports[scene_index] = source

    scene_index = 18
    base = exports[scene_index]
    edited = copy.deepcopy(base)
    color_index = 1
    before = edited["colors"][color_index]
    after = 0x0EEE if before != 0x0EEE else 0x0000
    assert after != before
    assert (after & ~CRAM_MASK) == 0
    edited["colors"][color_index] = after

    out, report = compile_palette(raw, edited)
    assert out != raw
    assert len(out) == 0x400000
    assert report["noop"] is False
    assert report["changed_color_indices"] == [color_index]
    assert report["palette_bytes"] == 128
    assert report["new_pointer"] >= 0x200000
    assert set(report["scene_record_changed_offsets"]) <= set(range(0x02, 0x0A))
    assert report["output_sha1"] == hashlib.sha1(out).hexdigest()

    invalid = copy.deepcopy(base)
    invalid["colors"][color_index] = 0x0001
    try:
        compile_palette(raw, invalid)
    except ValueError:
        invalid_rejected = True
    else:
        invalid_rejected = False
    assert invalid_rejected

    result = {
        "schema": "truerecall.m11f.scene_palette.v1",
        "base_sha1": BASE_SHA1,
        "scene_count": SCENE_COUNT,
        "all_scene_noop_exact": True,
        "scenes": scenes,
        "edited_scene18": {
            "color_index": color_index,
            "before": before,
            "after": after,
            "new_pointer": report["new_pointer"],
            "output_sha1": report["output_sha1"],
            "checksum": report["checksum"],
            "scene_record_changed_offsets": report["scene_record_changed_offsets"],
        },
        "invalid_cram_rejected": invalid_rejected,
        "runtime_validation": "pending",
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
