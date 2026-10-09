#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BASE = 'd39174bed46ede85531b86df7ba49123ce2f8411'
OLD = 0x200000
NEW = 0x400000
CHECK = 0x18E
ROM_END = 0x1A4
SCENE_TABLE = 0x013B4A
SCENE = 0
NEW_BASE = 0x230000


def u32(b, o):
    return int.from_bytes(b[o:o+4], 'big')


def checksum(b):
    s = 0
    for i in range(0x200, len(b) - 1, 2):
        s = (s + int.from_bytes(b[i:i+2], 'big')) & 0xFFFF
    return s


def build(raw: bytes):
    assert len(raw) == OLD and hashlib.sha1(raw).hexdigest() == BASE
    scene = u32(raw, SCENE_TABLE + SCENE * 4)
    src = u32(raw, scene + 0x0E)
    all_bases = sorted({u32(raw, u32(raw, SCENE_TABLE + i * 4) + 0x0E) for i in range(19)})
    nxt = min(x for x in all_bases if x > src)
    payload = raw[src:nxt]

    assert scene == 0x013B9A
    assert src == 0x07A42E
    assert nxt == 0x07C7EC
    assert len(payload) == 0x23BE

    out = bytearray(raw) + bytearray([0xFF]) * (NEW - OLD)
    out[ROM_END:ROM_END+4] = (NEW - 1).to_bytes(4, 'big')
    assert all(x == 0xFF for x in out[NEW_BASE:NEW_BASE+len(payload)])
    out[NEW_BASE:NEW_BASE+len(payload)] = payload
    out[scene+0x0E:scene+0x12] = NEW_BASE.to_bytes(4, 'big')

    assert out[NEW_BASE:NEW_BASE+len(payload)] == raw[src:nxt]
    assert int.from_bytes(out[scene+0x0E:scene+0x12], 'big') == NEW_BASE

    out[CHECK:CHECK+2] = b'\0\0'
    cs = checksum(out)
    out[CHECK:CHECK+2] = cs.to_bytes(2, 'big')

    report = {
        'schema': 'truerecall.m10a.world_collision_relocation.v1',
        'base_sha1': BASE,
        'scene': SCENE,
        'scene_record': f'0x{scene:06X}',
        'retail_resource': f'0x{src:06X}',
        'retail_copy_end': f'0x{nxt:06X}',
        'copied_bytes': len(payload),
        'relocated_resource': f'0x{NEW_BASE:06X}',
        'rom_size': NEW,
        'checksum': f'0x{cs:04X}',
        'output_sha1': hashlib.sha1(out).hexdigest(),
        'semantic_change': 'none; byte-identical resource relocation only',
    }
    return bytes(out), report


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    out, report = build(args.rom.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.write_text(text + '\n', encoding='utf-8')
