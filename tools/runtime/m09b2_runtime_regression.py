#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops

FRAMES = [2098] + list(range(2102, 2142, 2)) + [2144]
GAMEPLAY_HEIGHT = 224
ACTIVE_FRAMES = [f for f in FRAMES if 2102 <= f <= 2140]


def write_script(path: Path, capture_dir: Path) -> None:
    lines = [
        '930 down 1 start', '932 up 1 start',
        '1320 down 1 a', '1322 up 1 a',
        '1500 down 1 a', '1502 up 1 a',
        '1680 down 1 a', '1682 up 1 a',
        '1860 down 1 a', '1862 up 1 a',
        '2040 down 1 a', '2042 up 1 a',
        f'2098 shot {capture_dir / "f2098.png"}',
        '2100 down 1 left', '2100 down 1 y',
    ]
    for frame in range(2102, 2142, 2):
        lines.append(f'{frame} shot {capture_dir / f"f{frame}.png"}')
    lines += [
        '2142 up 1 y', '2142 up 1 left',
        f'2144 shot {capture_dir / "f2144.png"}',
    ]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def diff_metrics(a_path: Path, b_path: Path) -> dict:
    a = Image.open(a_path).convert('RGB')
    b = Image.open(b_path).convert('RGB')
    if a.size != b.size:
        raise AssertionError((a.size, b.size))
    diff = ImageChops.difference(a, b)
    w, h = a.size
    gameplay = diff.crop((0, 0, w, min(GAMEPLAY_HEIGHT, h)))
    total_pixels = sum(1 for px in diff.getdata() if px != (0, 0, 0))
    gameplay_pixels = sum(1 for px in gameplay.getdata() if px != (0, 0, 0))
    bbox = gameplay.getbbox()
    bbox_list = list(bbox) if bbox else None
    bbox_w = 0 if bbox is None else bbox[2] - bbox[0]
    bbox_h = 0 if bbox is None else bbox[3] - bbox[1]
    return {
        'total_different_pixels': total_pixels,
        'gameplay_different_pixels': gameplay_pixels,
        'gameplay_bbox': bbox_list,
        'gameplay_bbox_width': bbox_w,
        'gameplay_bbox_height': bbox_h,
    }


def compare(baseline: Path, candidate: Path) -> dict:
    rows = []
    for frame in FRAMES:
        aa = baseline / f'f{frame}.png'
        bb = candidate / f'f{frame}.png'
        if not aa.exists() or not bb.exists():
            raise FileNotFoundError((aa, bb))
        row = {'frame': frame, **diff_metrics(aa, bb)}
        rows.append(row)

    by_frame = {r['frame']: r for r in rows}
    assert by_frame[2098]['gameplay_different_pixels'] == 0
    assert by_frame[2144]['gameplay_different_pixels'] == 0

    for frame in ACTIVE_FRAMES:
        r = by_frame[frame]
        assert r['gameplay_different_pixels'] > 0, (frame, r)
        # The authored-pixel effect must remain avatar-local, not become a map/camera diff.
        assert r['gameplay_bbox_width'] <= 32, (frame, r)
        assert r['gameplay_bbox_height'] <= 20, (frame, r)

    return {
        'schema': 'truerecall.m09b2.runtime_regression.v1',
        'gameplay_height': GAMEPLAY_HEIGHT,
        'frames': rows,
        'assertions': {
            'pre_trigger_gameplay_equivalent': True,
            'active_frames_all_nonzero': True,
            'active_bbox_max_width': max(by_frame[f]['gameplay_bbox_width'] for f in ACTIVE_FRAMES),
            'active_bbox_max_height': max(by_frame[f]['gameplay_bbox_height'] for f in ACTIVE_FRAMES),
            'post_trigger_gameplay_equivalent': True,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)

    mk = sub.add_parser('make-script')
    mk.add_argument('script', type=Path)
    mk.add_argument('capture_dir', type=Path)

    cp = sub.add_parser('compare')
    cp.add_argument('baseline_dir', type=Path)
    cp.add_argument('candidate_dir', type=Path)
    cp.add_argument('--json', type=Path)

    args = ap.parse_args()
    if args.cmd == 'make-script':
        args.capture_dir.mkdir(parents=True, exist_ok=True)
        write_script(args.script, args.capture_dir)
        return

    report = compare(args.baseline_dir, args.candidate_dir)
    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
