#!/usr/bin/env python3
"""M09C native-phase authored player pixel sequence.

This build keeps the M07 sprint control seam and the M09B2 renderer/cache
substitution architecture, but removes the diagnostic VBlank-driven frame phase.
The authored resource bank is selected from the rendered actor's native animation
state:

    raw_phase_delta = object+0x1E - object+0x1C

Canonical runtime tracing of F9F8 during held-Y sprint established a six-position
cycle with raw deltas 0,2,4,6,8,10.  The renderer and cache-key trampolines map
those deltas one-to-one to six authored banks/namespaces while preserving D2.

The canonical F9F8 world/render avatar observed in that trace uses descriptor
0x000A0000.  Descriptor 0x000F0000 from M08 remains evidence of a player-local
visual component, but is no longer treated as F9F8 identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
CHECKSUM_OFFSET = 0x18E
ROM_END_OFFSET = 0x1A4

DIR_TABLE_SRC = 0x013F32
DIR_TABLE_DST = 0x200000
DIR_TABLE_SIZE = 0x2000
SPRINT_BASE_SELECTOR = 0x1FF0
DIR_TABLE_REFS = [0x19AE, 0x1A24, 0x1A80, 0x1AA4, 0x1B0E, 0x1B32]

ANIM_HOOK = 0x83A6
MOVE_HOOK = 0x9864
ANIM_TRAMP = 0x207000
MOVE_TRAMP = 0x207080
ORIGINAL_TEST = bytes.fromhex("08380006FB7F")

# Canonical F9F8 world/render avatar descriptor in the M09C runtime trace.
PLAYER_DESC = 0x000A0000

KEY_HOOK = 0x113B4
KEY_ORIGINAL = bytes.fromhex("302d001202403fff")
KEY_TRAMP = 0x208100
RENDER_HOOK = 0x1143C
RENDER_ORIGINAL = bytes.fromhex("223010026a1a")
RENDER_TRAMP = 0x208000

# Six 0x8000-byte raw 256-chunk banks, one for each canonical native phase.
BANKS = [0x210000, 0x218000, 0x220000, 0x228000, 0x230000, 0x238000]
CACHE_NAMESPACES = [0x3A00, 0x3B00, 0x3C00, 0x3D00, 0x3E00, 0x3F00]
RAW_PHASE_DELTAS = [0, 2, 4, 6, 8, 10]


def jmp(address: int) -> bytes:
    return b"\x4e\xf9" + address.to_bytes(4, "big")


def genesis_checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf) - 1, 2):
        total = (total + int.from_bytes(buf[off:off + 2], "big")) & 0xFFFF
    return total


class Assembler:
    def __init__(self) -> None:
        self.buf = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, int, str]] = []

    def emit(self, data: bytes) -> None:
        self.buf += data

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.buf)

    def branch_short(self, opcode: int, label: str) -> None:
        pos = len(self.buf)
        self.buf += bytes([opcode, 0])
        self.fixups.append((pos + 1, pos + 2, label))

    def finish(self) -> bytes:
        for at, base, label in self.fixups:
            if label not in self.labels:
                raise ValueError(f"missing label: {label}")
            delta = self.labels[label] - base
            if delta == 0:
                # 68K Bcc/BRA with an 8-bit displacement of zero switches to the
                # word-extension form.  It is never a two-byte no-op branch.
                raise ValueError(f"zero short-branch displacement is illegal: {label}")
            if not -128 <= delta <= 127:
                raise ValueError(f"short branch out of range: {label} ({delta})")
            self.buf[at] = delta & 0xFF
        return bytes(self.buf)


def native_phase_dispatch(asm: Assembler, emit_case) -> None:
    """Dispatch raw actor phase deltas 0,2,4,6,8,10.

    D2 is saved/restored.  Out-of-family deltas leave the retail D0/D1 value
    untouched and fall through to the caller's normal continuation path.
    """
    asm.emit(bytes.fromhex("2F02"))          # MOVE.L D2,-(A7)
    asm.emit(bytes.fromhex("342E001E"))      # MOVE.W 0x1E(A6),D2
    asm.emit(bytes.fromhex("946E001C"))      # SUB.W  0x1C(A6),D2

    for index, delta in enumerate(RAW_PHASE_DELTAS):
        asm.emit(bytes.fromhex("0C42") + delta.to_bytes(2, "big"))
        asm.branch_short(0x67, f"phase_{index}")  # BEQ.S
    asm.branch_short(0x60, "restore")

    for index in range(len(RAW_PHASE_DELTAS)):
        asm.label(f"phase_{index}")
        emit_case(asm, index)
        # The final case is immediately followed by restore; do not encode BRA.S
        # with displacement zero (0x6000 means BRA.W on 68000).
        if index != len(RAW_PHASE_DELTAS) - 1:
            asm.branch_short(0x60, "restore")

    asm.label("restore")
    asm.emit(bytes.fromhex("241F"))          # MOVE.L (A7)+,D2


def key_trampoline() -> bytes:
    asm = Assembler()
    # Retail instructions replaced at 0x113B4.
    asm.emit(bytes.fromhex("302D001202403FFF"))
    # Authored substitution only while held-Y sprint is active.
    asm.emit(bytes.fromhex("08380005F6EC"))  # BTST.B #5,$F6EC
    asm.branch_short(0x67, "exit")
    # Scope to the canonical F9F8 descriptor without clobbering A0.
    asm.emit(bytes.fromhex("2F08206E002CB1FC") + PLAYER_DESC.to_bytes(4, "big") + bytes.fromhex("205F"))
    asm.branch_short(0x66, "exit")

    def emit_namespace(a: Assembler, index: int) -> None:
        a.emit(bytes.fromhex("024000FF"))  # keep retail chunk index
        a.emit(bytes.fromhex("0040") + CACHE_NAMESPACES[index].to_bytes(2, "big"))

    native_phase_dispatch(asm, emit_namespace)
    asm.label("exit")
    asm.emit(jmp(0x113BC))
    return asm.finish()


def render_trampoline() -> bytes:
    asm = Assembler()
    # Retail source-pointer load replaced at 0x1143C.
    asm.emit(bytes.fromhex("22301002"))
    asm.emit(bytes.fromhex("08380005F6EC"))
    asm.branch_short(0x67, "finish")
    asm.emit(bytes.fromhex("2F08206E002CB1FC") + PLAYER_DESC.to_bytes(4, "big") + bytes.fromhex("205F"))
    asm.branch_short(0x66, "finish")

    def emit_bank(a: Assembler, index: int) -> None:
        a.emit(bytes.fromhex("223C") + BANKS[index].to_bytes(4, "big"))  # MOVE.L #bank,D1

    native_phase_dispatch(asm, emit_bank)
    asm.label("finish")
    # Reproduce the branch semantics of the overwritten renderer sequence.
    asm.emit(bytes.fromhex("4A81"))          # TST.L D1
    asm.branch_short(0x6A, "positive")       # BPL.S
    asm.emit(jmp(0x11442))
    asm.label("positive")
    asm.emit(jmp(0x1145C))
    return asm.finish()


def encode_tile(pixels: list[list[int]], x0: int, y0: int) -> bytes:
    out = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            out.append((pixels[y0 + y][x0 + x] << 4) | pixels[y0 + y][x0 + x + 1])
    return bytes(out)


def make_diagnostic_chunk(phase: int) -> bytes:
    """Return one visibly distinct 16x16 four-tile diagnostic frame."""
    color = 9 + phase
    px = [[0] * 16 for _ in range(16)]
    for y in range(3, 13):
        for x in range(6, 10):
            px[y][x] = color

    if phase == 0:
        for x in range(3, 13): px[5][x] = color
        for y in range(11, 16): px[y][5] = color; px[y][10] = color
    elif phase == 1:
        for k in range(5): px[5 + k][5 - k // 2] = color; px[5 + k][10 + k // 2] = color
        for k in range(5): px[11 + k][6 - k // 2] = color; px[11 + k][9 + k // 2] = color
    elif phase == 2:
        for x in range(2, 14): px[8][x] = color
        for y in range(11, 16): px[y][7] = color; px[y][8] = color
    elif phase == 3:
        for k in range(6): px[4 + k][3 + k] = color; px[4 + k][12 - k] = color
        for k in range(5): px[11 + k][5 + k // 2] = color; px[11 + k][10 - k // 2] = color
    elif phase == 4:
        for x in range(2, 14): px[4][x] = color; px[11][x] = color
        for y in range(4, 12): px[y][3] = color; px[y][12] = color
    else:
        for k in range(8): px[4 + k][4 + k // 2] = color; px[4 + k][11 - k // 2] = color
        for x in range(5, 11): px[13][x] = color

    return b"".join(
        encode_tile(px, tile_x * 8, tile_y * 8)
        for tile_x in range(2)
        for tile_y in range(2)
    )


def build(raw: bytes) -> tuple[bytes, dict]:
    if len(raw) != OLD_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != EXPECTED_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")
    if raw[KEY_HOOK:KEY_HOOK + len(KEY_ORIGINAL)] != KEY_ORIGINAL:
        raise ValueError("cache-key hook bytes changed")
    if raw[RENDER_HOOK:RENDER_HOOK + len(RENDER_ORIGINAL)] != RENDER_ORIGINAL:
        raise ValueError("renderer hook bytes changed")

    out = bytearray(raw) + bytearray([0xFF]) * (NEW_SIZE - OLD_SIZE)
    out[ROM_END_OFFSET:ROM_END_OFFSET + 4] = (NEW_SIZE - 1).to_bytes(4, "big")

    # M07C sprint seam, relocated into the expanded ROM.
    out[DIR_TABLE_DST:DIR_TABLE_DST + DIR_TABLE_SIZE] = raw[DIR_TABLE_SRC:DIR_TABLE_SRC + DIR_TABLE_SIZE]
    for patch_at in DIR_TABLE_REFS:
        out[patch_at:patch_at + 4] = DIR_TABLE_DST.to_bytes(4, "big")
    out[DIR_TABLE_DST + SPRINT_BASE_SELECTOR:DIR_TABLE_DST + SPRINT_BASE_SELECTOR + 16] = (
        raw[DIR_TABLE_SRC + 0x00F2:DIR_TABLE_SRC + 0x00F2 + 16]
    )

    anim_code = bytes.fromhex("08380005F6EC670A303C1FF0") + jmp(0x83C2) + ORIGINAL_TEST + jmp(0x83AC)
    move_code = bytes.fromhex("08380005F6EC6714303C0300323C02804EB900009D8A") + jmp(0x97FA) + ORIGINAL_TEST + jmp(0x986A)
    out[ANIM_TRAMP:ANIM_TRAMP + len(anim_code)] = anim_code
    out[MOVE_TRAMP:MOVE_TRAMP + len(move_code)] = move_code
    out[ANIM_HOOK:ANIM_HOOK + 6] = jmp(ANIM_TRAMP)
    out[MOVE_HOOK:MOVE_HOOK + 6] = jmp(MOVE_TRAMP)

    phase_hashes = []
    for phase, bank in enumerate(BANKS):
        chunk = make_diagnostic_chunk(phase)
        phase_hashes.append(hashlib.sha1(chunk).hexdigest())
        out[bank:bank + 0x8000] = chunk * 256

    key_code = key_trampoline()
    render_code = render_trampoline()
    if len(key_code) >= 0x100 or len(render_code) >= 0x100:
        raise AssertionError((len(key_code), len(render_code)))
    out[KEY_TRAMP:KEY_TRAMP + len(key_code)] = key_code
    out[KEY_HOOK:KEY_HOOK + 8] = jmp(KEY_TRAMP) + bytes.fromhex("4E71")
    out[RENDER_TRAMP:RENDER_TRAMP + len(render_code)] = render_code
    out[RENDER_HOOK:RENDER_HOOK + 6] = jmp(RENDER_TRAMP)

    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = b"\x00\x00"
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 2] = checksum.to_bytes(2, "big")

    report = {
        "schema": "truerecall.m09c.native_phase_pixel_sequence.v1",
        "base_sha1": EXPECTED_SHA1,
        "output_sha1": hashlib.sha1(out).hexdigest(),
        "rom_size": len(out),
        "player_descriptor_scope": f"0x{PLAYER_DESC:06X}",
        "phase_source": "(object+0x1E)-(object+0x1C)",
        "raw_phase_deltas": RAW_PHASE_DELTAS,
        "banks": [f"0x{x:06X}" for x in BANKS],
        "cache_namespaces": [f"0x{x:04X}" for x in CACHE_NAMESPACES],
        "phase_chunk_sha1": phase_hashes,
        "key_trampoline_bytes": len(key_code),
        "render_trampoline_bytes": len(render_code),
        "checksum": f"0x{checksum:04X}",
        "runtime_validation": "native-phase dispatch proven in BlastEm; full visual regression pending",
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    out, report = build(args.rom.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
