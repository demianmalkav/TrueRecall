#!/usr/bin/env python3
"""Compare deterministic BlastEm screenshot captures for the M0.7 sprint proof.

This tool never needs the copyrighted ROM. It operates only on locally generated PNG
captures and emits measurements suitable for regression metadata.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

SPARSE_FRAMES = [2080, 2120, 2140, 2160, 2200]
DENSE_FRAMES = [2098] + list(range(2102, 2142, 2)) + [2144]


def load_frame(folder: Path, frame: int) -> np.ndarray:
    candidates = [
        folder / f"frame_{frame}.png",
        folder / f"{frame}.png",
        folder / f"screen_{frame}.png",
    ]
    for path in candidates:
        if path.exists():
            return np.asarray(Image.open(path).convert("RGB"))
    matches = sorted(folder.glob(f"*{frame}*.png"))
    if len(matches) == 1:
        return np.asarray(Image.open(matches[0]).convert("RGB"))
    raise FileNotFoundError(f"no unique screenshot for frame {frame} in {folder}")


def pixel_diff(a: np.ndarray, b: np.ndarray, rows: slice | None = None) -> dict:
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    aa = a if rows is None else a[rows]
    bb = b if rows is None else b[rows]
    mask = np.any(aa != bb, axis=2)
    changed = int(mask.sum())
    if not changed:
        bbox = None
    else:
        ys, xs = np.where(mask)
        yoff = 0 if rows is None or rows.start is None else rows.start
        bbox = [int(xs.min()), int(ys.min() + yoff), int(xs.max()), int(ys.max() + yoff)]
    return {"changed_pixels": changed, "bbox": bbox}


def best_horizontal_shift(reference: np.ndarray, current: np.ndarray,
                          y0: int = 5, y1: int = 75,
                          min_shift: int = -60, max_shift: int = 60) -> tuple[int, float]:
    """Register a static horizontal environment strip with integer translation.

    The signed shift is an image-registration quantity. Its sign depends on movement
    direction; callers should use its magnitude as camera/world progress when comparing
    identical trajectories.
    """
    r = reference[y0:y1].astype(np.int16)
    c = current[y0:y1].astype(np.int16)
    h, w, _ = r.shape
    best: tuple[float, int] | None = None
    for s in range(min_shift, max_shift + 1):
        if s >= 0:
            rr = r[:, s:w]
            cc = c[:, 0:w-s]
        else:
            k = -s
            rr = r[:, 0:w-k]
            cc = c[:, k:w]
        if rr.size == 0:
            continue
        err = float(np.abs(rr - cc).mean())
        key = (err, abs(s))
        if best is None or key < (best[0], abs(best[1])):
            best = (err, s)
    if best is None:
        raise RuntimeError("registration failed")
    err, shift = best
    return shift, err


def compare_sparse(a_dir: Path, b_dir: Path, gameplay_y1: int = 234) -> list[dict]:
    rows = []
    for frame in SPARSE_FRAMES:
        a = load_frame(a_dir, frame)
        b = load_frame(b_dir, frame)
        rows.append({
            "frame": frame,
            "full": pixel_diff(a, b),
            "gameplay_rows": pixel_diff(a, b, slice(0, gameplay_y1)),
        })
    return rows


def camera_curve(folder: Path, reference_frame: int = 2098) -> list[dict]:
    ref = load_frame(folder, reference_frame)
    rows = []
    for frame in DENSE_FRAMES:
        img = load_frame(folder, frame)
        shift, err = best_horizontal_shift(ref, img)
        rows.append({
            "frame": frame,
            "raw_horizontal_shift_px": int(shift),
            "camera_progress_px": int(abs(shift)),
            "alignment_mean_abs_error": err,
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dense", type=Path, required=True)
    ap.add_argument("--sprint-dense", type=Path, required=True)
    ap.add_argument("--diag-active", type=Path)
    ap.add_argument("--m07c-active", type=Path)
    ap.add_argument("--fallback-base", type=Path)
    ap.add_argument("--fallback-patch", type=Path)
    ap.add_argument("--reloc-base", type=Path)
    ap.add_argument("--reloc-noop", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    report: dict = {
        "schema": "truerecall.m07.runtime_sprint_compare.v1",
        "camera_shift_dense": {
            "base": camera_curve(args.base_dense),
            "sprint": camera_curve(args.sprint_dense),
        },
    }

    if args.diag_active and args.m07c_active:
        report["active_path_equivalence"] = compare_sparse(args.diag_active, args.m07c_active)
    if args.fallback_base and args.fallback_patch:
        report["fallback"] = compare_sparse(args.fallback_base, args.fallback_patch)
    if args.reloc_base and args.reloc_noop:
        report["relocation_noop"] = compare_sparse(args.reloc_base, args.reloc_noop)

    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
