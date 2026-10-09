#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
ROM_SIZE = 2_097_152
CHECKSUM = 0x18E

DIR_TABLE_SRC = 0x013F32
DIR_TABLE_DST = 0x1FB000
DIR_TABLE_COPY_SIZE = 0x2000
SPRINT_BASE_SELECTOR = 0x1FF0
DIR_TABLE_REFS = [0x19AE, 0x1A24, 0x1A80, 0x1AA4, 0x1B0E, 0x1B32]

ANIM_HOOK = 0x0083A6
MOVE_HOOK = 0x009864
ANIM_TRAMP = 0x1FE000
MOVE_TRAMP = 0x1FE080
RETAIL_OVERLAY_TEST = bytes.fromhex("08380006FB7F")


def jmp(addr: int) -> bytes:
    return b"\x4E\xF9" + addr.to_bytes(4, "big")


def checksum(buf: bytes) -> int:
    total = 0
    for i in range(0x200, len(buf) - 1, 2):
        total = (total + int.from_bytes(buf[i:i + 2], "big")) & 0xFFFF
    return total


def build(raw: bytes):
    assert len(raw) == ROM_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1
    assert all(raw[p:p + 4] == DIR_TABLE_SRC.to_bytes(4, "big") for p in DIR_TABLE_REFS)
    assert raw[ANIM_HOOK:ANIM_HOOK + 6] == RETAIL_OVERLAY_TEST
    assert raw[MOVE_HOOK:MOVE_HOOK + 6] == RETAIL_OVERLAY_TEST
    assert all(x == 0xFF for x in raw[DIR_TABLE_DST:DIR_TABLE_DST + DIR_TABLE_COPY_SIZE])
    assert all(x == 0xFF for x in raw[ANIM_TRAMP:ANIM_TRAMP + 0x100])

    out = bytearray(raw)

    # Relocate the common animation-direction table byte-identically.
    out[DIR_TABLE_DST:DIR_TABLE_DST + DIR_TABLE_COPY_SIZE] = raw[
        DIR_TABLE_SRC:DIR_TABLE_SRC + DIR_TABLE_COPY_SIZE
    ]
    for p in DIR_TABLE_REFS:
        out[p:p + 4] = DIR_TABLE_DST.to_bytes(4, "big")

    # Add a new sprint-only base row. For the proof milestone the row deliberately
    # clones the retail JLLBFR presentation (base 0x00F2), but it has a new selector
    # identity and independent ROM-resident data. Retail row 0x00F2 remains untouched.
    retail_row = raw[DIR_TABLE_SRC + 0x00F2:DIR_TABLE_SRC + 0x00F2 + 16]
    row_address = DIR_TABLE_DST + SPRINT_BASE_SELECTOR
    out[row_address:row_address + 16] = retail_row

    # Y is normalized bit 13, i.e. bit 5 of the high byte at F6EC.
    # When held, select the new animation base then resume the standard 0x1A8E path.
    # Otherwise execute the original JLLBFR overlay test unchanged.
    anim_trampoline = (
        bytes.fromhex("08380005F6EC") +      # BTST #5,($F6EC).w
        bytes.fromhex("670A") +              # BEQ fallback
        bytes.fromhex("303C1FF0") +          # MOVE.W #$1FF0,D0
        jmp(0x0083C2) +                      # standard caller -> 0x1A8E
        RETAIL_OVERLAY_TEST +
        jmp(0x0083AC)
    )

    # Sprint movement uses a faster parameter pair but preserves the retail
    # JLLBFR path exactly when Y is clear.
    move_trampoline = (
        bytes.fromhex("08380005F6EC") +
        bytes.fromhex("6714") +
        bytes.fromhex("303C0300") +
        bytes.fromhex("323C0280") +
        bytes.fromhex("4EB900009D8A") +
        jmp(0x0097FA) +
        RETAIL_OVERLAY_TEST +
        jmp(0x00986A)
    )
    assert len(anim_trampoline) == 30
    assert len(move_trampoline) == 40

    out[ANIM_TRAMP:ANIM_TRAMP + len(anim_trampoline)] = anim_trampoline
    out[MOVE_TRAMP:MOVE_TRAMP + len(move_trampoline)] = move_trampoline
    out[ANIM_HOOK:ANIM_HOOK + 6] = jmp(ANIM_TRAMP)
    out[MOVE_HOOK:MOVE_HOOK + 6] = jmp(MOVE_TRAMP)

    out[CHECKSUM:CHECKSUM + 2] = b"\0\0"
    csum = checksum(out)
    out[CHECKSUM:CHECKSUM + 2] = csum.to_bytes(2, "big")

    report = {
        "schema": "truerecall.m07c.sprint_new_animation_row.v1",
        "base_sha1": BASE_SHA1,
        "trigger": {"physical": "Y", "normalized_bit": 13},
        "table_relocation": {
            "src": hex(DIR_TABLE_SRC),
            "dst": hex(DIR_TABLE_DST),
            "size": hex(DIR_TABLE_COPY_SIZE),
            "refs": [hex(x) for x in DIR_TABLE_REFS],
        },
        "new_animation": {
            "base_selector": f"0x{SPRINT_BASE_SELECTOR:04X}",
            "row_address": hex(row_address),
            "source_for_safe_proof": "retail JLLBFR row 0x00F2 copied byte-identically",
            "retail_row_unchanged": True,
        },
        "hooks": {"animation": hex(ANIM_HOOK), "movement": hex(MOVE_HOOK)},
        "sprint_params": ["0x0300", "0x0280"],
        "checksum": f"0x{csum:04X}",
        "output_sha1": hashlib.sha1(out).hexdigest(),
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    out, report = build(args.rom.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
