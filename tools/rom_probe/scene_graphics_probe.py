#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
from scene_graphics import (
    BASE_SHA1,
    BASE_SIZE,
    DEFAULT_ALLOCATION_BASE,
    compile_primary_graphics,
    export_primary_graphics,
)

SCENE_INDEX = 0
EXPECTED_DESCRIPTOR = 0x00FFAA
EXPECTED_PRIMARY_LZ = 0x014898
EXPECTED_SECONDARY = 0x800178DA
EXPECTED_AUX = 0x01BF7A
EXPECTED_TILE_COUNT = 780
EXPECTED_DECODED_BYTES = 24960
EXPECTED_DECODED_SHA256 = "0f73aff41d28f9cae5b17368f78979f720474ce342c85e53f9a46174e3bbb171"
EXPECTED_ENCODED_BYTES = 12084
EXPECTED_ENCODED_SHA256 = "259f7cc90397ce25c5babd3ad8bab601dd13c87e1c86feeb02a6fc9ec880360b"
EXPECTED_RELOCATED_SHA1 = "b61ae28d9ead8928f4dbe94f2ecd7eaa057e90d5"
EXPECTED_RELOCATED_CHECKSUM = "0xF6E0"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    assert len(raw) == BASE_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    source = export_primary_graphics(raw, SCENE_INDEX)
    assert source["retail_descriptor"] == EXPECTED_DESCRIPTOR
    assert source["retail_primary_lz"] == EXPECTED_PRIMARY_LZ
    assert source["secondary_pointer"] == EXPECTED_SECONDARY
    assert source["aux_pointer"] == EXPECTED_AUX
    assert source["secondary_plane_descriptor"] == 0
    assert source["tile_count"] == EXPECTED_TILE_COUNT
    assert len(bytes.fromhex(source["tile_bytes_hex"])) == EXPECTED_DECODED_BYTES
    assert source["decoded_sha256"] == EXPECTED_DECODED_SHA256
    assert source["map_reference_stats"]["C000"]["max_tile_index"] == 564
    assert source["map_reference_stats"]["E000"]["max_tile_index"] == 519

    no_op, no_op_report = compile_primary_graphics(raw, source)
    assert no_op == raw
    assert no_op_report["noop"] is True

    relocated, relocated_report = compile_primary_graphics(raw, source, force_relocate=True)
    assert len(relocated) == 0x400000
    assert relocated_report["noop"] is False
    assert relocated_report["force_relocate"] is True
    assert relocated_report["new_descriptor"] == DEFAULT_ALLOCATION_BASE
    assert relocated_report["new_primary_lz"] == DEFAULT_ALLOCATION_BASE + 0x10
    assert relocated_report["encoded_bytes"] == EXPECTED_ENCODED_BYTES
    assert relocated_report["encoded_sha256"] == EXPECTED_ENCODED_SHA256
    assert relocated_report["decoded_sha256"] == EXPECTED_DECODED_SHA256
    assert relocated_report["changed_tile_indices"] == []
    assert relocated_report["output_sha1"] == EXPECTED_RELOCATED_SHA1
    assert relocated_report["checksum"] == EXPECTED_RELOCATED_CHECKSUM

    result = {
        "schema": "truerecall.m111b.scene_graphics_primary.v1",
        "base_sha1": BASE_SHA1,
        "scene_index": SCENE_INDEX,
        "descriptor": EXPECTED_DESCRIPTOR,
        "primary_lz": EXPECTED_PRIMARY_LZ,
        "secondary_pointer": EXPECTED_SECONDARY,
        "aux_pointer": EXPECTED_AUX,
        "secondary_plane_descriptor": 0,
        "decoded_bytes": EXPECTED_DECODED_BYTES,
        "tile_count": EXPECTED_TILE_COUNT,
        "decoded_sha256": EXPECTED_DECODED_SHA256,
        "map_reference_stats": source["map_reference_stats"],
        "exact_raw_noop": True,
        "relocated_noop": {
            "allocation_base": DEFAULT_ALLOCATION_BASE,
            "descriptor": relocated_report["new_descriptor"],
            "primary_lz": relocated_report["new_primary_lz"],
            "encoded_bytes": relocated_report["encoded_bytes"],
            "encoded_sha256": relocated_report["encoded_sha256"],
            "decoded_sha256": relocated_report["decoded_sha256"],
            "changed_tile_indices": relocated_report["changed_tile_indices"],
            "output_sha1": relocated_report["output_sha1"],
            "checksum": relocated_report["checksum"],
        },
        "runtime_validation": "pending",
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
