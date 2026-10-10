#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

from m100b_vertical_slice_runtime import BlastEmSession, EXPECTED_BLASTEM_SHA256, sha1, sha256

EXPECTED_M110A_SHA1 = "270e1d633db7883c9170bb1e4eb367abdf97a2bd"
EXPECTED_CANDIDATE_SHA1 = "b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0"
SAVE_HEADER = b"BLSTSZ\x01\x07"
VDP_SECTION_ID = 3
VDP_STATE_VERSION = 5
VRAM_BYTES = 64 * 1024
CRAM_WORDS = 64
CRAM_BYTES = CRAM_WORDS * 2
TILE_INDEX = 2
TILE_BYTES = 32
TILE_VRAM_START = TILE_INDEX * TILE_BYTES
TILE_VRAM_END = TILE_VRAM_START + TILE_BYTES
RETAIL_TILE_SHA256 = "e0e77a507412b120f6ede61f62295b1a7b2ff19d3dcc8f7253e51663470c888e"
AUTHORED_TILE_BYTES = bytes.fromhex(
    "e000000e"
    "0e0000e0"
    "00e00e00"
    "000ee000"
    "000ee000"
    "00e00e00"
    "0e0000e0"
    "e000000e"
)


def parse_vdp_state(state: bytes) -> dict[str, Any]:
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
            if len(payload) < 2 + VRAM_BYTES + CRAM_BYTES:
                raise ValueError("VDP section too small")
            version = payload[0]
            vram_kb = payload[1]
            if version != VDP_STATE_VERSION or vram_kb != 64:
                raise ValueError(f"unexpected VDP state header: version={version} vram_kb={vram_kb}")
            vram = payload[2:2 + VRAM_BYTES]
            cram_start = 2 + VRAM_BYTES
            cram = payload[cram_start:cram_start + CRAM_BYTES]
            cram_words = [int.from_bytes(cram[i:i + 2], "big") for i in range(0, CRAM_BYTES, 2)]
            return {
                "section_id": section_id,
                "section_size": section_size,
                "vdp_state_version": version,
                "vram_kb": vram_kb,
                "vram": vram,
                "cram_words": cram_words,
            }
        pos = end
    raise ValueError("VDP section not found")


def _latest_screenshot(home: Path) -> Path:
    shots = sorted(home.glob("blastem_*.png"), key=lambda path: path.stat().st_mtime_ns)
    if not shots:
        raise RuntimeError("BlastEm screenshot missing")
    return shots[-1]


def run_scene0_snapshot(blastem: Path, rom: Path, display: str) -> dict[str, Any]:
    old_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory(prefix="truerecall_m111d_") as home_text:
        home = Path(home_text)
        os.environ["HOME"] = home_text
        try:
            with BlastEmSession(blastem, rom, display) as session:
                session.navigate_scene0()
                session.key("p", True)
                session.key("p", False)
                session.command("frames 1")
                screenshot = _latest_screenshot(home).read_bytes()
                session.key("grave", True)
                session.key("grave", False)
                log = session.command("frames 1")
                if "Saved state to" not in log:
                    raise RuntimeError(f"BlastEm did not confirm quicksave: {log[-1000:]!r}")
            state_path = home / ".local" / "share" / "blastem" / rom.stem / "quicksave.state"
            if not state_path.is_file():
                raise RuntimeError(f"quicksave missing: {state_path}")
            state = state_path.read_bytes()
            return {
                "vdp": parse_vdp_state(state),
                "state_sha256": hashlib.sha256(state).hexdigest(),
                "screenshot": screenshot,
            }
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home


def byte_diff_ranges(before: bytes, after: bytes) -> list[list[int]]:
    if len(before) != len(after):
        raise ValueError("buffers differ in length")
    changed = [index for index, (a, b) in enumerate(zip(before, after)) if a != b]
    if not changed:
        return []
    out: list[list[int]] = []
    start = previous = changed[0]
    for index in changed[1:]:
        if index != previous + 1:
            out.append([start, previous + 1])
            start = index
        previous = index
    out.append([start, previous + 1])
    return out


def screenshot_diff(parent_png: bytes, candidate_png: bytes) -> dict[str, Any]:
    parent = Image.open(io.BytesIO(parent_png)).convert("RGB")
    candidate = Image.open(io.BytesIO(candidate_png)).convert("RGB")
    if parent.size != candidate.size:
        raise ValueError("screenshot dimensions differ")
    width, height = parent.size
    pp = parent.load()
    cp = candidate.load()
    xs: list[int] = []
    ys: list[int] = []
    changed = 0
    for y in range(height):
        for x in range(width):
            if pp[x, y] != cp[x, y]:
                changed += 1
                xs.append(x)
                ys.append(y)
    bbox = [min(xs), min(ys), max(xs) + 1, max(ys) + 1] if xs else None
    return {
        "size": [width, height],
        "changed_pixels": changed,
        "bbox": bbox,
        "parent_sha256": hashlib.sha256(parent_png).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_png).hexdigest(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("blastem", type=Path)
    ap.add_argument("m110a_parent", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--parent-display", default=":241")
    ap.add_argument("--candidate-display", default=":242")
    args = ap.parse_args()

    if sha256(args.blastem) != EXPECTED_BLASTEM_SHA256:
        raise SystemExit("wrong BlastEm binary")
    if sha1(args.m110a_parent) != EXPECTED_M110A_SHA1:
        raise SystemExit("wrong closed M110A parent")
    if sha1(args.candidate) != EXPECTED_CANDIDATE_SHA1:
        raise SystemExit("wrong M1.1B candidate")

    parent = run_scene0_snapshot(args.blastem, args.m110a_parent, args.parent_display)
    candidate = run_scene0_snapshot(args.blastem, args.candidate, args.candidate_display)

    parent_vram = parent["vdp"]["vram"]
    candidate_vram = candidate["vdp"]["vram"]
    vram_ranges = byte_diff_ranges(parent_vram, candidate_vram)
    vram_changed_bytes = sum(end - start for start, end in vram_ranges)
    parent_tile = parent_vram[TILE_VRAM_START:TILE_VRAM_END]
    candidate_tile = candidate_vram[TILE_VRAM_START:TILE_VRAM_END]
    presentation = screenshot_diff(parent["screenshot"], candidate["screenshot"])

    assertions = {
        "m110a_cram_exact": parent["vdp"]["cram_words"] == candidate["vdp"]["cram_words"],
        "vram_diff_exactly_tile2": vram_ranges == [[TILE_VRAM_START, TILE_VRAM_END]],
        "vram_changed_byte_count_exact": vram_changed_bytes == TILE_BYTES,
        "parent_tile2_fingerprint_exact": hashlib.sha256(parent_tile).hexdigest() == RETAIL_TILE_SHA256,
        "authored_tile2_reaches_vram_exact": candidate_tile == AUTHORED_TILE_BYTES,
        "presentation_dimensions_exact": presentation["size"] == [256, 240],
        "presentation_changed": presentation["changed_pixels"] > 0,
        "presentation_diff_confined_to_upper_environment": presentation["bbox"] is not None and presentation["bbox"][3] <= 64,
    }
    report = {
        "schema": "truerecall.m111d.graphics_runtime.v1",
        "blastem_sha256": EXPECTED_BLASTEM_SHA256,
        "m110a_parent_sha1": EXPECTED_M110A_SHA1,
        "candidate_sha1": EXPECTED_CANDIDATE_SHA1,
        "state_sha256": {
            "m110a_parent": parent["state_sha256"],
            "candidate": candidate["state_sha256"],
        },
        "tile_index": TILE_INDEX,
        "vram_range": [TILE_VRAM_START, TILE_VRAM_END],
        "vram_diff_ranges": vram_ranges,
        "vram_changed_bytes": vram_changed_bytes,
        "parent_tile_sha256": hashlib.sha256(parent_tile).hexdigest(),
        "candidate_tile_hex": candidate_tile.hex(),
        "presentation": presentation,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not report["pass"]:
        raise SystemExit("M1.1B graphics runtime proof failed")


if __name__ == "__main__":
    main()
