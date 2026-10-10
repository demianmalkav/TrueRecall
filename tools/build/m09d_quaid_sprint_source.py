#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

AUTHORED_DIRECTIONS = ("N", "NE", "E", "SE", "S")
PHASE_DELTAS = (0, 2, 4, 6, 8, 10)

# Original production-prototype palette. Index 0 is transparent by contract.
PALETTE = [
    (0, 0, 0),
    (22, 19, 20),
    (48, 38, 34),
    (112, 67, 47),
    (180, 116, 76),
    (218, 155, 103),
    (31, 48, 58),
    (45, 72, 88),
    (68, 101, 119),
    (25, 31, 39),
    (44, 52, 66),
    (70, 80, 96),
    (91, 39, 35),
    (135, 58, 46),
    (177, 89, 61),
    (214, 135, 77),
]


def _piece_info(contract: dict[str, Any], direction: str, phase_index: int):
    family = contract["families"][direction]
    key = f"record_{family['phase_record_pattern'][phase_index]}"
    record = family[key]
    pieces = [
        (int(x), int(y), int(slot, 0) if isinstance(slot, str) else int(slot))
        for x, y, slot in record["pieces"]
    ]
    return record, pieces


def _install_palette(img: Image.Image) -> None:
    flat: list[int] = []
    for color in PALETTE:
        flat.extend(color)
    flat += [0] * (768 - len(flat))
    img.putpalette(flat)


def _clip_to_piece_mask(img: Image.Image, pieces) -> None:
    mask = Image.new("1", img.size, 0)
    draw = ImageDraw.Draw(mask)
    for x, y, _ in pieces:
        draw.rectangle((x, y, x + 15, y + 15), fill=1)
    px = img.load()
    mx = mask.load()
    for y in range(img.height):
        for x in range(img.width):
            if not mx[x, y]:
                px[x, y] = 0


def render_frame(
    contract: dict[str, Any], direction: str, phase_index: int
) -> Image.Image:
    """Render one original indexed Quaid sprint prototype frame.

    The art deliberately derives its writable mask from the canonical mapping
    record. No pixel outside the renderer-proven 16x16 pieces survives, so source
    art and the closed M09D mapping contract cannot silently drift apart.
    """
    if direction not in AUTHORED_DIRECTIONS:
        raise ValueError(f"direction {direction!r} is not an authored family")
    if not 0 <= phase_index < len(PHASE_DELTAS):
        raise ValueError("phase index out of range")

    record, pieces = _piece_info(contract, direction, phase_index)
    width, height = map(int, record["clip"])
    img = Image.new("P", (width, height), 0)
    _install_palette(img)
    draw = ImageDraw.Draw(img)

    xs = [x for x, _, _ in pieces]
    ys = [y for _, y, _ in pieces]
    min_x, min_y = min(xs), min(ys)
    max_x = max(x + 15 for x, _, _ in pieces)
    max_y = max(y + 15 for _, y, _ in pieces)
    center_x = (min_x + max_x) // 2

    gait = (-2, -1, 0, 2, 1, 0)[phase_index]
    bob = (0, 1, 1, 0, -1, -1)[phase_index]
    lean = (-1, -1, 0, 1, 1, 0)[phase_index]

    head_y = min_y + 2 + bob
    head_x = center_x + lean
    if direction == "E":
        head_x += 2
    elif direction in ("NE", "SE"):
        head_x += 1

    # Head / hair / directional face highlight.
    draw.rectangle((head_x - 4, head_y, head_x + 4, head_y + 7), fill=1)
    draw.rectangle((head_x - 3, head_y + 1, head_x + 3, head_y + 6), fill=4)
    draw.rectangle((head_x - 3, head_y, head_x + 3, head_y + 2), fill=2)
    if direction in ("E", "NE", "SE"):
        draw.point((head_x + 4, head_y + 4), fill=5)

    # Broad shoulders / heavy torso. The silhouette is intentionally stockier
    # than the retail Harry Tasker source family.
    shoulder_y = head_y + 8
    shoulder_half = 7 + (1 if direction in ("NE", "SE", "S") else 0)
    draw.polygon(
        [
            (center_x - shoulder_half + lean, shoulder_y),
            (center_x + shoulder_half + lean, shoulder_y),
            (center_x + 6 + lean, shoulder_y + 11),
            (center_x - 6 + lean, shoulder_y + 11),
        ],
        fill=6,
    )

    # Rust-red outer panels / harness create a Total Recall-specific silhouette
    # without copying film or retail source pixels.
    draw.line(
        (
            center_x - shoulder_half + lean,
            shoulder_y + 1,
            center_x - 3 + lean,
            shoulder_y + 10,
        ),
        fill=12,
        width=2,
    )
    draw.line(
        (
            center_x + shoulder_half + lean,
            shoulder_y + 1,
            center_x + 3 + lean,
            shoulder_y + 10,
        ),
        fill=13,
        width=2,
    )
    draw.rectangle(
        (center_x - 3 + lean, shoulder_y + 2, center_x + 3 + lean, shoulder_y + 9),
        fill=7,
    )

    # Arm counter-swing.
    arm = 3 if gait >= 0 else -3
    left_x = center_x - 7 + lean
    right_x = center_x + 7 + lean
    if direction == "E":
        left_x += 2
        right_x -= 1
    draw.line((left_x, shoulder_y + 3, left_x - arm // 2, shoulder_y + 12), fill=3, width=3)
    draw.line((right_x, shoulder_y + 3, right_x + arm // 2, shoulder_y + 12), fill=4, width=3)
    draw.point((left_x - arm // 2, shoulder_y + 13), fill=5)
    draw.point((right_x + arm // 2, shoulder_y + 13), fill=5)

    # Belt / hips / running stride.
    hip_y = shoulder_y + 11
    draw.rectangle((center_x - 5 + lean, hip_y, center_x + 5 + lean, hip_y + 3), fill=9)
    draw.line((center_x - 5 + lean, hip_y, center_x + 5 + lean, hip_y), fill=14, width=1)

    leg_len = max(5, min(13, max_y - (hip_y + 2)))
    left_leg_x = center_x - 3 + lean
    right_leg_x = center_x + 3 + lean
    draw.line(
        (left_leg_x, hip_y + 3, left_leg_x - gait, hip_y + leg_len), fill=10, width=4
    )
    draw.line(
        (right_leg_x, hip_y + 3, right_leg_x + gait, hip_y + leg_len), fill=11, width=4
    )
    draw.line(
        (
            left_leg_x - gait,
            hip_y + leg_len,
            left_leg_x - gait - (1 if gait > 0 else -1),
            min(max_y, hip_y + leg_len + 2),
        ),
        fill=1,
        width=3,
    )
    draw.line(
        (
            right_leg_x + gait,
            hip_y + leg_len,
            right_leg_x + gait + (1 if gait >= 0 else -1),
            min(max_y, hip_y + leg_len + 2),
        ),
        fill=1,
        width=3,
    )

    highlight_x = center_x + (
        3 if direction in ("E", "NE", "SE") else -3 if direction == "N" else 0
    )
    draw.line(
        (highlight_x + lean, shoulder_y + 2, highlight_x + lean, hip_y - 1),
        fill=8,
        width=1,
    )

    _clip_to_piece_mask(img, pieces)
    return img


def generate(contract: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    if contract.get("schema") != "truerecall.m09d.quaid_sprint_contract.v1":
        raise ValueError("wrong M09D contract schema")
    out_dir.mkdir(parents=True, exist_ok=True)

    directions: dict[str, list[dict[str, Any]]] = {}
    frame_meta: list[dict[str, Any]] = []

    for direction in AUTHORED_DIRECTIONS:
        rows = []
        png_hashes = []
        for phase_index, phase_delta in enumerate(PHASE_DELTAS):
            img = render_frame(contract, direction, phase_index)
            name = f"{direction}_p{phase_index}.png"
            path = out_dir / name
            img.save(path, optimize=False)
            digest = hashlib.sha1(path.read_bytes()).hexdigest()
            png_hashes.append(digest)

            nonzero = [
                (x, y)
                for y in range(img.height)
                for x in range(img.width)
                if img.getpixel((x, y)) != 0
            ]
            bbox = None
            if nonzero:
                bbox = [
                    min(x for x, _ in nonzero),
                    min(y for _, y in nonzero),
                    max(x for x, _ in nonzero) + 1,
                    max(y for _, y in nonzero) + 1,
                ]
            palette_indices = sorted(
                {
                    img.getpixel((x, y))
                    for y in range(img.height)
                    for x in range(img.width)
                }
            )
            rows.append({"phase_delta": phase_delta, "image": name})
            frame_meta.append(
                {
                    "direction": direction,
                    "phase_delta": phase_delta,
                    "image": name,
                    "png_sha1": digest,
                    "canvas": [img.width, img.height],
                    "nonzero_pixels": len(nonzero),
                    "bbox": bbox,
                    "palette_indices": palette_indices,
                }
            )

        if len(set(png_hashes)) != len(PHASE_DELTAS):
            raise ValueError(f"{direction} does not contain six distinct authored phases")
        directions[direction] = rows

    manifest = {
        "schema": "truerecall.m09d.quaid_sprint_source.v1",
        "art_status": "original_production_prototype",
        "generated_by": "tools/build/m09d_quaid_sprint_source.py",
        "palette": PALETTE,
        "directions": directions,
        "frames": frame_meta,
        "assertions": {
            "frame_count": len(frame_meta),
            "authored_direction_count": len(directions),
            "six_phases_each": all(len(v) == 6 for v in directions.values()),
            "all_frames_nonempty": all(row["nonzero_pixels"] > 0 for row in frame_meta),
            "palette_size": len(PALETTE),
            "transparent_index_zero": PALETTE[0] == (0, 0, 0),
            "all_palette_indices_within_0_15": all(
                max(row["palette_indices"]) <= 15 for row in frame_meta
            ),
        },
    }
    (out_dir / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "palette.json").write_text(
        json.dumps(PALETTE, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("contract", type=Path)
    ap.add_argument("out_dir", type=Path)
    args = ap.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    report = generate(contract, args.out_dir)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
