#!/usr/bin/env python3
"""Corrected canonical F9F8 animation-state tracer for M09C.

The first M09C tracer treated FFFFF9F8/FFFFFB6E as adjacent 32-bit globals.
Canonical execution disproved that assumption: retail code accesses both globals
with MOVEA.W and the stored values are signed 16-bit RAM pointers.  This wrapper
keeps the already-tested BlastEm PTY/control/watchpoint harness from v1, but
patches its pointer reader and expected F9F8 descriptor to the canonical runtime
facts established after raw ROM access became available.

Historical v1 remains in-tree as evidence of the falsified hypothesis.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import m09c_animation_state_trace as legacy

EXPECTED_F9F8_DESCRIPTOR = 0x000A0000


def sign_extend_pointer_word(value: int) -> int:
    value &= 0xFFFF
    return (0xFFFF0000 | value) if value & 0x8000 else value


def read_word_pointer(debugger: legacy.BlastEmDebugger, address: int) -> int:
    value = debugger.print_expressions([f"[0x{address:06X}]"])[0]
    return sign_extend_pointer_word(value)


def trace_v2(
    blastem: Path,
    rom: Path,
    *,
    wide_state: bool,
    max_events: int,
    xvfb: bool,
) -> dict:
    # Preserve the v1 harness while replacing only the two canonically falsified
    # assumptions.  legacy.trace resolves these names at call time.
    old_reader = legacy.read_long_pointer
    old_descriptor = legacy.EXPECTED_VISUAL_DESCRIPTOR
    legacy.read_long_pointer = read_word_pointer
    legacy.EXPECTED_VISUAL_DESCRIPTOR = EXPECTED_F9F8_DESCRIPTOR
    try:
        report = legacy.trace(
            blastem,
            rom,
            wide_state=wide_state,
            max_events=max_events,
            xvfb=xvfb,
        )
    finally:
        legacy.read_long_pointer = old_reader
        legacy.EXPECTED_VISUAL_DESCRIPTOR = old_descriptor

    report["schema"] = "truerecall.m09c.animation_state_trace.v2"
    report["pointer_globals"] = {
        "FFFFF9F8": "signed 16-bit F9F8 world/render-avatar pointer",
        "FFFFFB6E": "signed 16-bit FB6E control-proxy pointer",
    }
    report["pointer_width_bits"] = 16
    report["expected_f9f8_descriptor"] = EXPECTED_F9F8_DESCRIPTOR
    report["v1_correction"] = (
        "v1 combined two adjacent words into a false 32-bit pointer and expected "
        "descriptor 0x0F0000; canonical runtime evidence corrected both assumptions"
    )
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--blastem", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--wide-state", action="store_true")
    ap.add_argument("--max-events", type=int, default=256)
    ap.add_argument("--xvfb", action="store_true")
    args = ap.parse_args()

    report = trace_v2(
        args.blastem,
        args.rom,
        wide_state=args.wide_state,
        max_events=args.max_events,
        xvfb=args.xvfb,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
