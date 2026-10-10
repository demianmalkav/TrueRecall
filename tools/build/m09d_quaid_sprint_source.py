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

# Preview palette is the confirmed runtime player CRAM line in the M09D
# validation scene. Source art is indexed; indices, not RGB values, are the
# ROM-facing contract. Index 0 remains transparent.
PALETTE = [
    (0, 0, 0),
    (49, 49, 0),
    (87, 87, 0),
    (119, 87, 0),
    (146, 119, 87),
    (255, 146, 0),
    (206, 206, 87),
    (49, 49, 49),
    (119, 119, 119),
    (174, 174, 174),
    (255, 255, 255),
    (174, 0, 0),
    (87, 87, 0),
    (119, 119, 0),
    (146, 146, 0),
    (0, 0, 0),
]

OUTLINE = 15
PANTS_D = 1
PANTS_M = 2
HAIR = 3
SKIN = 4
SKIN_HI = 5
SHIRT_D = 7
SHIRT_M = 8
SHIRT_L = 9
SHIRT_HI = 10
ACCENT = 11


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


def _poly(draw: ImageDraw.ImageDraw, pts, fill: int, outline: int | None = None) -> None:
    draw.polygon(pts, fill=fill)
    if outline is not None:
        draw.line(list(pts) + [pts[0]], fill=outline, width=1)


def _draw_head(draw: ImageDraw.ImageDraw, direction: str, phase: int, x: int, y: int) -> int:
    """Draw a directionally correct Quaid head.

    N is the back of the head, NE rear three-quarter, E right profile, SE front
    three-quarter and S front. This prevents mirrored/front-facing facial cues
    from leaking into rear-facing families.
    """
    y += (0, 1, 1, 0, -1, -1)[phase]
    if direction == "N":
        _poly(draw, [(x-4,y+1),(x-3,y),(x+3,y),(x+4,y+2),(x+3,y+7),(x-3,y+7),(x-4,y+5)], HAIR, OUTLINE)
        draw.rectangle((x-2,y+5,x+2,y+7), fill=HAIR)
        draw.line((x-2,y+7,x+2,y+7), fill=SKIN, width=1)
    elif direction == "NE":
        _poly(draw, [(x-4,y+1),(x-3,y),(x+2,y),(x+4,y+2),(x+3,y+7),(x-2,y+7),(x-4,y+5)], HAIR, OUTLINE)
        draw.rectangle((x+1,y+3,x+3,y+6), fill=SKIN)
        draw.point((x+3,y+3), fill=SKIN_HI)
        draw.point((x-2,y+6), fill=HAIR)
    elif direction == "E":
        _poly(draw, [(x-3,y+1),(x-2,y),(x+2,y),(x+3,y+2),(x+4,y+3),(x+3,y+4),(x+3,y+6),(x+1,y+8),(x-2,y+7),(x-3,y+5)], SKIN, OUTLINE)
        draw.rectangle((x-3,y,x+1,y+2), fill=HAIR)
        draw.point((x+2,y+3), fill=OUTLINE)
        draw.point((x+4,y+3), fill=SKIN_HI)
        draw.line((x+1,y+6,x+3,y+6), fill=HAIR, width=1)
    elif direction == "SE":
        _poly(draw, [(x-4,y+2),(x-3,y),(x+2,y),(x+4,y+2),(x+4,y+4),(x+2,y+7),(x,y+8),(x-3,y+7),(x-4,y+5)], SKIN, OUTLINE)
        draw.rectangle((x-3,y,x+2,y+2), fill=HAIR)
        draw.point((x+2,y+3), fill=OUTLINE)
        draw.point((x+4,y+4), fill=SKIN_HI)
        draw.line((x,y+6,x+2,y+6), fill=HAIR, width=1)
    else:
        _poly(draw, [(x-4,y+2),(x-3,y),(x+3,y),(x+4,y+2),(x+4,y+5),(x+2,y+8),(x-2,y+8),(x-4,y+5)], SKIN, OUTLINE)
        draw.rectangle((x-3,y,x+3,y+2), fill=HAIR)
        draw.point((x-2,y+4), fill=OUTLINE)
        draw.point((x+2,y+4), fill=OUTLINE)
        draw.point((x+1,y+5), fill=SKIN_HI)
        draw.line((x-2,y+7,x+2,y+7), fill=HAIR, width=1)
    return y


def _draw_torso(draw: ImageDraw.ImageDraw, direction: str, phase: int, x: int, y: int) -> tuple[int, int]:
    """Broad-shouldered work-shirt silhouette with cloth folds, not armor panels."""
    lean = (-1, -1, 0, 1, 1, 0)[phase]
    x += lean
    if direction == "E":
        pts = [(x-5,y+1),(x-3,y),(x+4,y),(x+6,y+2),(x+4,y+11),(x+2,y+13),(x-3,y+12),(x-6,y+5)]
    elif direction in ("NE", "SE"):
        pts = [(x-7,y+2),(x-5,y),(x+5,y),(x+7,y+2),(x+5,y+11),(x+2,y+13),(x-3,y+13),(x-6,y+10),(x-8,y+4)]
    else:
        pts = [(x-7,y+2),(x-5,y),(x+5,y),(x+7,y+2),(x+5,y+10),(x+3,y+13),(x-3,y+13),(x-5,y+10)]
    _poly(draw, pts, SHIRT_D, OUTLINE)

    if direction == "N":
        draw.polygon([(x-4,y+2),(x-1,y+1),(x-2,y+10),(x-4,y+9)], fill=SHIRT_M)
        draw.polygon([(x+1,y+1),(x+4,y+2),(x+3,y+9),(x+1,y+10)], fill=SHIRT_M)
        draw.line((x-3,y+5,x+3,y+5), fill=SHIRT_L)
        draw.line((x,y+3,x,y+11), fill=SHIRT_D)
        draw.point((x+3,y+3), fill=SHIRT_L)
    elif direction == "S":
        draw.polygon([(x-4,y+2),(x-1,y+1),(x-2,y+10),(x-4,y+9)], fill=SHIRT_M)
        draw.polygon([(x,y+1),(x+4,y+2),(x+3,y+9),(x+1,y+10)], fill=SHIRT_M)
        draw.line((x-2,y+4,x+2,y+4), fill=SHIRT_L)
        draw.line((x-1,y+2,x-2,y+10), fill=SHIRT_D)
        draw.point((x+2,y+2), fill=SHIRT_HI)
    else:
        draw.polygon([(x-4,y+2),(x-1,y+1),(x-2,y+10),(x-4,y+9)], fill=SHIRT_M)
        draw.polygon([(x,y+1),(x+4,y+2),(x+3,y+8),(x+1,y+10)], fill=SHIRT_L)
        draw.line((x-2,y+5,x+2,y+5), fill=SHIRT_D)
        draw.point((x+2,y+2), fill=SHIRT_HI)

    draw.line((x-4,y+12,x+4,y+12), fill=OUTLINE, width=1)
    draw.point((x,y+12), fill=ACCENT)
    return x, y + 12


def _draw_arms(draw: ImageDraw.ImageDraw, direction: str, phase: int, x: int, shoulder_y: int) -> None:
    """Thick upper arms and tapered forearms give Quaid a heavier physical read."""
    swing = (-4, -2, 0, 4, 2, 0)[phase]
    if direction == "E":
        draw.line((x+4,shoulder_y+2,x+7,shoulder_y+6), fill=SKIN, width=3)
        draw.line((x+7,shoulder_y+6,x+5+swing//2,shoulder_y+12), fill=SKIN, width=2)
        draw.point((x+5+swing//2,shoulder_y+12), fill=SKIN_HI)
        draw.line((x-4,shoulder_y+3,x-6,shoulder_y+7), fill=SKIN, width=2)
        draw.line((x-6,shoulder_y+7,x-3-swing//3,shoulder_y+11), fill=SKIN, width=2)
    elif direction in ("NE", "SE"):
        draw.line((x-6,shoulder_y+3,x-8,shoulder_y+7-swing//4), fill=SKIN, width=3)
        draw.line((x-8,shoulder_y+7-swing//4,x-5-swing//2,shoulder_y+12), fill=SKIN, width=2)
        draw.line((x+6,shoulder_y+3,x+8,shoulder_y+7+swing//4), fill=SKIN, width=3)
        draw.line((x+8,shoulder_y+7+swing//4,x+5+swing//2,shoulder_y+12), fill=SKIN, width=2)
        draw.point((x+5+swing//2,shoulder_y+12), fill=SKIN_HI)
    else:
        draw.line((x-6,shoulder_y+3,x-8,shoulder_y+7-swing//4), fill=SKIN, width=3)
        draw.line((x-8,shoulder_y+7-swing//4,x-6-swing//2,shoulder_y+12), fill=SKIN, width=2)
        draw.line((x+6,shoulder_y+3,x+8,shoulder_y+7+swing//4), fill=SKIN, width=3)
        draw.line((x+8,shoulder_y+7+swing//4,x+6+swing//2,shoulder_y+12), fill=SKIN, width=2)
        if direction == "S":
            draw.point((x+6+swing//2,shoulder_y+12), fill=SKIN_HI)


def _draw_legs(draw: ImageDraw.ImageDraw, direction: str, phase: int, x: int, hip_y: int, usable_bottom: int) -> None:
    """Wider sprint stance with heavier thighs and a clearer six-position gait."""
    stride = (-4, -2, 0, 4, 2, 0)[phase]
    rise = (0, 1, 2, 0, 1, 2)[phase]
    knee_y = min(usable_bottom, hip_y + 5 - rise//2)
    foot_y = min(usable_bottom, hip_y + 10)
    if direction == "E":
        near_k=(x+2+stride//3,knee_y); far_k=(x-2-stride//4,knee_y-1)
        near_f=(x+5+stride,foot_y); far_f=(x-4-stride,foot_y-1)
    elif direction in ("NE", "SE"):
        near_k=(x+2+stride//3,knee_y); far_k=(x-2-stride//3,knee_y-1)
        near_f=(x+4+stride,foot_y); far_f=(x-4-stride,foot_y-1)
    else:
        near_k=(x+2+stride//3,knee_y); far_k=(x-2-stride//3,knee_y)
        near_f=(x+4+stride,foot_y); far_f=(x-4-stride,foot_y)
    draw.line(((x-2,hip_y),far_k), fill=PANTS_D, width=4)
    draw.line((far_k,far_f), fill=PANTS_D, width=3)
    draw.line(((x+2,hip_y),near_k), fill=PANTS_M, width=4)
    draw.line((near_k,near_f), fill=PANTS_M, width=3)
    draw.line((near_f[0]-2,near_f[1],near_f[0]+2,near_f[1]), fill=OUTLINE, width=2)
    draw.line((far_f[0]-2,far_f[1],far_f[0]+2,far_f[1]), fill=OUTLINE, width=2)


def render_frame(contract: dict[str, Any], direction: str, phase_index: int) -> Image.Image:
    if direction not in AUTHORED_DIRECTIONS:
        raise ValueError(f"direction {direction!r} is not an authored family")
    if not 0 <= phase_index < len(PHASE_DELTAS):
        raise ValueError("phase index out of range")

    record, pieces = _piece_info(contract, direction, phase_index)
    width, height = map(int, record["clip"])
    img = Image.new("P", (width, height), 0)
    _install_palette(img)
    draw = ImageDraw.Draw(img)
    min_y = min(y for _, y, _ in pieces)
    max_y = max(y + 15 for _, y, _ in pieces)
    usable_bottom = min(max_y, min_y + 31)

    head_x = {"N":14,"NE":15,"E":11,"SE":13,"S":20}[direction]
    body_x = {"N":15,"NE":15,"E":14,"SE":15,"S":17}[direction]
    head_y = _draw_head(draw, direction, phase_index, head_x, 1)
    shoulder_y = head_y + 8
    body_x, hip_y = _draw_torso(draw, direction, phase_index, body_x, shoulder_y)
    _draw_arms(draw, direction, phase_index, body_x, shoulder_y)
    _draw_legs(draw, direction, phase_index, body_x, hip_y + 1, usable_bottom)
    _clip_to_piece_mask(img, pieces)
    return img


def generate(contract: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    if contract.get("schema") != "truerecall.m09d.quaid_sprint_contract.v1":
        raise ValueError("wrong M09D contract schema")
    out_dir.mkdir(parents=True, exist_ok=True)
    directions: dict[str, list[dict[str, Any]]] = {}
    frame_meta: list[dict[str, Any]] = []
    for direction in AUTHORED_DIRECTIONS:
        rows=[]; png_hashes=[]
        for phase_index, phase_delta in enumerate(PHASE_DELTAS):
            img=render_frame(contract,direction,phase_index)
            name=f"{direction}_p{phase_index}.png"; path=out_dir/name
            img.save(path,optimize=False); digest=hashlib.sha1(path.read_bytes()).hexdigest(); png_hashes.append(digest)
            nonzero=[(x,y) for y in range(img.height) for x in range(img.width) if img.getpixel((x,y))!=0]
            bbox=None
            if nonzero:
                bbox=[min(x for x,_ in nonzero),min(y for _,y in nonzero),max(x for x,_ in nonzero)+1,max(y for _,y in nonzero)+1]
            palette_indices=sorted({img.getpixel((x,y)) for y in range(img.height) for x in range(img.width)})
            rows.append({"phase_delta":phase_delta,"image":name})
            frame_meta.append({"direction":direction,"phase_delta":phase_delta,"image":name,"png_sha1":digest,"canvas":[img.width,img.height],"nonzero_pixels":len(nonzero),"bbox":bbox,"palette_indices":palette_indices})
        if len(set(png_hashes)) != len(PHASE_DELTAS):
            raise ValueError(f"{direction} does not contain six distinct authored phases")
        directions[direction]=rows
    manifest={
        "schema":"truerecall.m09d.quaid_sprint_source.v1",
        "art_status":"production_candidate_v10",
        "generated_by":"tools/build/m09d_quaid_sprint_source.py",
        "palette":PALETTE,
        "directions":directions,
        "frames":frame_meta,
        "assertions":{
            "frame_count":len(frame_meta),
            "authored_direction_count":len(directions),
            "six_phases_each":all(len(v)==6 for v in directions.values()),
            "all_frames_nonempty":all(row["nonzero_pixels"]>0 for row in frame_meta),
            "palette_size":len(PALETTE),
            "transparent_index_zero":PALETTE[0]==(0,0,0),
            "all_palette_indices_within_0_15":all(max(row["palette_indices"])<=15 for row in frame_meta),
        },
    }
    (out_dir/"source_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out_dir/"palette.json").write_text(json.dumps(PALETTE,indent=2)+"\n",encoding="utf-8")
    return manifest


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("contract",type=Path); ap.add_argument("out_dir",type=Path); args=ap.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8")); report=generate(contract,args.out_dir); print(json.dumps(report,indent=2,sort_keys=True))


if __name__ == "__main__":
    main()
