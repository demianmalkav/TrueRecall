#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from world_collision_codec import (
    GRID_W, GRID_H, CELL_PX, GRID_BYTES, POOL_START, POOL_END, SENTINEL,
    RECORD_START, parse_records, parse_index, serialize_index, assert_retail_exact, p16,
)

BASE_SHA1 = 'd39174bed46ede85531b86df7ba49123ce2f8411'
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
CHECKSUM_OFF = 0x18E
ROM_END_OFF = 0x1A4
SCENE_TABLE = 0x013B4A
SCENE_INDEX = 0
WORLD_SRC = 0x07A42E
WORLD_END = 0x07C7EC
RELOC_BASE = 0x230000
TARGET_RECORD = 0x1C46
DX = 64


def u16(buf, off): return int.from_bytes(buf[off:off+2], 'big')
def u32(buf, off): return int.from_bytes(buf[off:off+4], 'big')
def p32(value): return int(value).to_bytes(4, 'big')


def genesis_checksum(buf: bytes | bytearray) -> int:
    value = 0
    for off in range(0x200, len(buf) - 1, 2):
        value = (value + u16(buf, off)) & 0xFFFF
    return value


def build(raw: bytes):
    assert len(raw) == OLD_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1
    scene = u32(raw, SCENE_TABLE + SCENE_INDEX * 4)
    assert scene == 0x013B9A
    assert u32(raw, scene + 0x0E) == WORLD_SRC

    resource = bytearray(raw[WORLD_SRC:WORLD_END])
    records = assert_retail_exact(resource)
    _g, _lists, retail_memberships = parse_index(resource)

    idx = (TARGET_RECORD - RECORD_START) // 10
    rec = records[idx]
    assert rec[0] == TARGET_RECORD
    assert tuple(rec[1:]) == (9, 736, 544, 752, 800)

    rec[2] += DX
    rec[4] += DX
    assert tuple(rec[1:]) == (9, 800, 544, 816, 800)

    grid, pool, memberships = serialize_index(records)
    changed_cells = [i for i, (a, b) in enumerate(zip(retail_memberships, memberships)) if a != b]
    assert changed_cells == [443, 444, 497, 498, 551, 552, 605, 606, 659, 660]
    assert len(pool) == 1698
    assert len(pool) <= POOL_END - POOL_START

    resource[:GRID_BYTES] = grid
    resource[POOL_START:POOL_END] = b'\xFF' * (POOL_END - POOL_START)
    resource[POOL_START:POOL_START + len(pool)] = pool
    resource[SENTINEL:SENTINEL+2] = b'\xFF\xFF'
    for delta, value in zip((0, 2, 4, 6, 8), rec[1:]):
        resource[TARGET_RECORD + delta:TARGET_RECORD + delta + 2] = p16(value)

    reparsed = parse_records(resource)
    grid2, pool2, memberships2 = serialize_index(reparsed)
    assert grid2 == bytes(resource[:GRID_BYTES])
    assert pool2 == bytes(resource[POOL_START:POOL_START + len(pool2)])
    assert memberships2 == memberships
    assert tuple(reparsed[idx][1:]) == (9, 800, 544, 816, 800)

    out = bytearray(raw) + bytearray([0xFF]) * (NEW_SIZE - OLD_SIZE)
    out[ROM_END_OFF:ROM_END_OFF+4] = p32(NEW_SIZE - 1)
    out[RELOC_BASE:RELOC_BASE + len(resource)] = resource
    out[scene+0x0E:scene+0x12] = p32(RELOC_BASE)
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = b'\0\0'
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = p16(checksum)

    report = {
        'schema': 'truerecall.m10c.broadphase_geometry.v1',
        'base_sha1': BASE_SHA1,
        'scene': SCENE_INDEX,
        'grid': {'width': GRID_W, 'height': GRID_H, 'cell_px': CELL_PX, 'bytes': GRID_BYTES},
        'retail_exact_regeneration': True,
        'retail_list_pool_bytes': 1702,
        'authored_list_pool_bytes': len(pool),
        'record_offset': f'0x{TARGET_RECORD:04X}',
        'geometry_before': [736, 544, 752, 800],
        'geometry_after': [800, 544, 816, 800],
        'semantic_changed_cells': changed_cells,
        'semantic_changed_cell_xy': [[i % GRID_W, i // GRID_W] for i in changed_cells],
        'relocated_resource': f'0x{RELOC_BASE:06X}',
        'checksum': f'0x{checksum:04X}',
        'output_sha1': hashlib.sha1(out).hexdigest(),
        'runtime_validation': 'pending',
    }
    return bytes(out), report


def main():
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
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
