#!/usr/bin/env python3
"""Reproduce the M0.6D controlled data-patch experiment.

Input must be the canonical True Lies (World) ROM. The script changes only the
initial shotgun-shell amount granted by the shotgun-weapon pickup from 5 to a
user-specified amount (default 6), then recomputes the Sega checksum.

The base ROM is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
CHECKSUM_OFFSET = 0x018E
PICKUP_AMOUNT_OFFSET = 0x1762C1
EXPECTED_ORIGINAL_AMOUNT = 5


def sega_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x0200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--amount", type=int, default=6)
    args = ap.parse_args()

    raw = args.rom.read_bytes()
    if len(raw) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(raw)}")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")
    if raw[PICKUP_AMOUNT_OFFSET] != EXPECTED_ORIGINAL_AMOUNT:
        raise SystemExit(
            f"unexpected base byte at 0x{PICKUP_AMOUNT_OFFSET:06X}: "
            f"0x{raw[PICKUP_AMOUNT_OFFSET]:02X}"
        )
    if not 0 <= args.amount <= 99:
        raise SystemExit("amount must be in range 0..99")

    out = bytearray(raw)
    out[PICKUP_AMOUNT_OFFSET] = args.amount
    checksum = sega_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = checksum.to_bytes(2, "big")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"base_sha1={digest}")
    print(f"patch=0x{PICKUP_AMOUNT_OFFSET:06X}: {EXPECTED_ORIGINAL_AMOUNT} -> {args.amount}")
    print(f"checksum=0x{checksum:04X}")
    print(f"output_sha1={hashlib.sha1(out).hexdigest()}")


if __name__ == "__main__":
    main()
