#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from m100b_vertical_slice_runtime import (
    BlastEmSession,
    EXPECTED_BLASTEM_SHA256,
    evaluate as evaluate_m100b,
    sha1,
    sha256,
)

EXPECTED_PARENT_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_CANDIDATE_SHA1 = "270e1d633db7883c9170bb1e4eb367abdf97a2bd"
SAVE_HEADER = b"BLSTSZ\x01\x07"
VDP_SECTION_ID = 3
VDP_STATE_VERSION = 5
VDP_VRAM_KB = 64
VRAM_BYTES = 64 * 1024
CRAM_WORDS = 64
CRAM_BYTES = CRAM_WORDS * 2
PALETTE_INDEX = 8
PARENT_COLOR = 0x0464
CANDIDATE_COLOR = 0x0648
PLAYER_LINE = slice(32, 48)


def parse_vdp_cram(state: bytes) -> dict[str, Any]:
    if state[: len(SAVE_HEADER)] != SAVE_HEADER:
        raise ValueError("not a BlastEm native save state")
    pos = len(SAVE_HEADER)
    while pos + 6 <= len(state):
        section_id = int.from_bytes(state[pos:pos + 2], "big")
        section_size = int.from_bytes(state[pos + 2:pos + 6], "big")
        start = pos + 6
        end = start + section_size
        if end > len(state):
            raise ValueError("truncated save-state section")
        if section_id == VDP_SECTION_ID:
            payload = state[start:end]
            minimum = 2 + VRAM_BYTES + CRAM_BYTES
            if len(payload) < minimum:
                raise ValueError("VDP section too small")
            version = payload[0]
            vram_kb = payload[1]
            if version != VDP_STATE_VERSION or vram_kb != VDP_VRAM_KB:
                raise ValueError(f"unexpected VDP state header: version={version} vram_kb={vram_kb}")
            cram_start = 2 + VRAM_BYTES
            cram = payload[cram_start:cram_start + CRAM_BYTES]
            words = [int.from_bytes(cram[i:i + 2], "big") for i in range(0, CRAM_BYTES, 2)]
            return {
                "section_id": section_id,
                "section_size": section_size,
                "vdp_state_version": version,
                "vram_kb": vram_kb,
                "cram_words": words,
            }
        pos = end
    raise ValueError("VDP section not found")


def evaluate_cram(parent_words: list[int], candidate_words: list[int]) -> dict[str, Any]:
    if len(parent_words) != CRAM_WORDS or len(candidate_words) != CRAM_WORDS:
        raise ValueError("expected 64 CRAM words")
    differences = [
        {"index": i, "parent": before, "candidate": after}
        for i, (before, after) in enumerate(zip(parent_words, candidate_words))
        if before != after
    ]
    assertions = {
        "exactly_one_cram_word_changed": len(differences) == 1,
        "authored_cram_index_exact": differences == [
            {"index": PALETTE_INDEX, "parent": PARENT_COLOR, "candidate": CANDIDATE_COLOR}
        ],
        "player_palette_line_exact": parent_words[PLAYER_LINE] == candidate_words[PLAYER_LINE],
    }
    return {"differences": differences, "assertions": assertions, "pass": all(assertions.values())}


def run_one(blastem: Path, rom: Path, display: str) -> tuple[dict[str, Any], dict[str, Any], str]:
    old_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory(prefix="truerecall_m110b_") as home:
        os.environ["HOME"] = home
        try:
            with BlastEmSession(blastem, rom, display) as session:
                gameplay = session.run_probe()
                session.key("grave", True)
                session.key("grave", False)
                log = session.command("frames 1")
                if "Saved state to" not in log:
                    raise RuntimeError(f"BlastEm did not confirm quicksave: {log[-1000:]!r}")
            state_path = Path(home) / ".local" / "share" / "blastem" / rom.stem / "quicksave.state"
            if not state_path.is_file():
                raise RuntimeError(f"quicksave missing: {state_path}")
            state = state_path.read_bytes()
            return gameplay, parse_vdp_cram(state), hashlib.sha256(state).hexdigest()
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("blastem", type=Path)
    ap.add_argument("parent", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--parent-display", default=":138")
    ap.add_argument("--candidate-display", default=":139")
    args = ap.parse_args()

    if sha256(args.blastem) != EXPECTED_BLASTEM_SHA256:
        raise SystemExit("wrong BlastEm binary")
    if sha1(args.parent) != EXPECTED_PARENT_SHA1:
        raise SystemExit("wrong frozen M09D direct parent")
    if sha1(args.candidate) != EXPECTED_CANDIDATE_SHA1:
        raise SystemExit("wrong M1.1A candidate")

    parent_gameplay, parent_vdp, parent_state_sha256 = run_one(args.blastem, args.parent, args.parent_display)
    candidate_gameplay, candidate_vdp, candidate_state_sha256 = run_one(args.blastem, args.candidate, args.candidate_display)

    gameplay = evaluate_m100b(parent_gameplay, candidate_gameplay)
    cram = evaluate_cram(parent_vdp["cram_words"], candidate_vdp["cram_words"])
    assertions = {
        "m100b_behavioral_regression": gameplay["pass"],
        **cram["assertions"],
    }
    report = {
        "schema": "truerecall.m110b.palette_runtime.v1",
        "blastem_sha256": EXPECTED_BLASTEM_SHA256,
        "parent_sha1": EXPECTED_PARENT_SHA1,
        "candidate_sha1": EXPECTED_CANDIDATE_SHA1,
        "savestate_format": {
            "header_hex": SAVE_HEADER.hex(),
            "vdp_section_id": VDP_SECTION_ID,
            "vdp_state_version": VDP_STATE_VERSION,
            "vram_kb": VDP_VRAM_KB,
            "cram_words": CRAM_WORDS,
        },
        "parent_state_sha256": parent_state_sha256,
        "candidate_state_sha256": candidate_state_sha256,
        "parent_vdp": parent_vdp,
        "candidate_vdp": candidate_vdp,
        "cram": cram,
        "m100b": {
            "assertions": gameplay["assertions"],
            "pass": gameplay["pass"],
        },
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not report["pass"]:
        raise SystemExit("M1.1A runtime palette regression failed")


if __name__ == "__main__":
    main()
