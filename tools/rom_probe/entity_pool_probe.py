#!/usr/bin/env python3
"""Static probe for the True Lies generic entity pool/list allocator.

Hash-locked to the canonical True Lies (World) ROM. The probe records structural
metadata only; it does not embed the ROM or extracted game assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
RECORD_SIZE = 0x72
POOL_SIZE = 0x0F96
POOL_COUNT = 35


def check(data: bytes, off: int, raw: str, label: str) -> None:
    expected = bytes.fromhex(raw)
    actual = data[off:off + len(expected)]
    if actual != expected:
        raise AssertionError(
            f"{label} mismatch at 0x{off:06X}: expected={expected.hex()} actual={actual.hex()}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    data = args.rom.read_bytes()
    if len(data) != EXPECTED_SIZE:
        raise SystemExit(f"Wrong ROM size: {len(data)}")
    digest = hashlib.sha1(data).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"Wrong base ROM SHA-1: {digest}")

    assert POOL_SIZE == POOL_COUNT * RECORD_SIZE

    check(data, 0x00F6CA,
          "307cf9f431480000314800024278f9f2303c0f96",
          "active-list sentinel and pool-size initialization")
    check(data, 0x00F6DA,
          "303c0f964eb900012a2a31c8f9fe31c8f9fc303c0021",
          "pool allocation and pointer-variable initialization")
    check(data, 0x00F6EC,
          "303c00213248d2fc007231490000304951c8fff442680000",
          "35-record free-list construction with 0x72 stride")

    check(data, 0x00F734,
          "3238f9fc670000883041720021410004",
          "allocator consumes the pointer stored in F9FC")
    check(data, 0x00F7AC,
          "31e80000f9fc5278f9f261000288201f",
          "allocator advances free-head pointer and increments active count")

    check(data, 0x00F904,
          "32680002336800000000326800003368000200025378f9f23178f9fc000031c8f9fc3049023c",
          "destructor unlinks active object, decrements count and pushes onto free list")

    check(data, 0x00FA40,
          "2f0a3278f9f4b2fcf9f467464a28000b6a1c",
          "active-list insertion starts from F9F4 sentinel")

    # Critical semantic check: the allocator call returns A0, which is then
    # stored into F9FE and F9FC. Therefore those RAM locations are pointer
    # variables; F9FE is not the physical pool address itself.
    check(data, 0x00F6DE,
          "4eb900012a2a31c8f9fe31c8f9fc",
          "heap allocator result stored in pool/free-head pointer variables")
    check(data, 0x00F726,
          "3038f9fe4eb900012ab0",
          "teardown reads stored pool pointer before freeing allocation")

    report = {
        "schema": "truerecall.entity_pool.v2",
        "base_sha1": digest,
        "confirmed": {
            "record_size_bytes": RECORD_SIZE,
            "pool_count": POOL_COUNT,
            "pool_bytes": POOL_SIZE,
            "pool_base_pointer_variable": "0xFFFFF9FE",
            "free_list_head_pointer_variable": "0xFFFFF9FC",
            "active_count": "0xFFFFF9F2",
            "active_list_sentinel": "0xFFFFF9F4",
            "active_links": {"next": "object+0x00", "previous": "object+0x02"},
            "heap_allocator_called_from_pool_init": "0x00012A2A",
            "allocator_entry": "0x00F732",
            "linked_clone_allocator_entry": "0x00F7CC",
            "destructor_free_entry": "0x00F8F8",
            "active_list_insert": "0x00FA40",
        },
        "architecture": {
            "pool_storage": "0x0F96-byte heap allocation; its returned low-RAM pointer is stored in F9FE",
            "free_list": "F9FC stores the current free-head pointer; unused records link through object+0x00",
            "active_list": "doubly linked circular list using +0x00/+0x02 and fixed sentinel F9F4",
            "capacity_note": "The generic allocation contains 35 records; practical simultaneous capacity is lower when persistent entities consume slots."
        },
        "unresolved": [
            "physical heap address returned for the pool in each initialization path",
            "exact allocation ordering for every object class",
            "persistent/system slot consumption by mission",
            "whether specialized auxiliary object pools coexist"
        ]
    }

    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
