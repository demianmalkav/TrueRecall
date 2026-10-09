#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from world_collision_codec import SCENE_TABLE, assert_retail_exact_scene, parse_index, p16, u16, u32, serialize_index

BASE_SHA1 = 'd39174bed46ede85531b86df7ba49123ce2f8411'
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
CHECKSUM_OFF = 0x18E
ROM_END_OFF = 0x1A4
SCENE_INDEX = 0
RELOC_BASE = 0x230000
NEW_RECORD_OFFSET = 0x2400
NEW_POOL_OFFSET = 0x2500
NEW_RECORD = [NEW_RECORD_OFFSET, 9, 800, 544, 816, 800]


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, 'big')


def genesis_checksum(buf: bytes | bytearray) -> int:
    value = 0
    for off in range(0x200, len(buf) - 1, 2):
        value = (value + u16(buf, off)) & 0xFFFF
    return value


def build(raw: bytes):
    assert len(raw) == OLD_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1
    layout = assert_retail_exact_scene(raw, SCENE_INDEX)
    scene = layout['scene_record']
    assert scene == 0x013B9A and layout['world_base'] == 0x07A42E

    scene1 = u32(raw, SCENE_TABLE + 4)
    retail_end = u32(raw, scene1 + 0x0E)
    retail_payload = raw[layout['world_base']:retail_end]
    assert len(retail_payload) == 0x23BE
    assert NEW_RECORD_OFFSET >= len(retail_payload)

    records = [list(row) for row in layout['records']] + [NEW_RECORD.copy()]
    grid, pool, memberships = serialize_index(records, layout['grid_w'], layout['grid_h'], pool_start=NEW_POOL_OFFSET)
    assert len(grid) == layout['grid_bytes'] == 0x09B4
    assert len(pool) == 1712
    sentinel = NEW_POOL_OFFSET + len(pool)
    assert NEW_RECORD_OFFSET + 10 < NEW_POOL_OFFSET
    assert sentinel + 2 < 0x8000

    changed = [i for i, (before, after) in enumerate(zip(layout['retail_memberships'], memberships)) if before != after]
    assert changed == [444, 498, 552, 606, 660]
    assert all(NEW_RECORD_OFFSET in memberships[i] for i in changed)

    out = bytearray(raw) + bytearray([0xFF]) * (NEW_SIZE - OLD_SIZE)
    out[ROM_END_OFF:ROM_END_OFF+4] = p32(NEW_SIZE - 1)
    out[RELOC_BASE:RELOC_BASE+len(retail_payload)] = retail_payload
    out[RELOC_BASE:RELOC_BASE+len(grid)] = grid

    for delta, value in zip((0, 2, 4, 6, 8), NEW_RECORD[1:]):
        out[RELOC_BASE+NEW_RECORD_OFFSET+delta:RELOC_BASE+NEW_RECORD_OFFSET+delta+2] = p16(value)
    out[RELOC_BASE+NEW_POOL_OFFSET:RELOC_BASE+NEW_POOL_OFFSET+len(pool)] = pool
    out[RELOC_BASE+sentinel:RELOC_BASE+sentinel+2] = b'\xFF\xFF'
    out[scene+0x0E:scene+0x12] = p32(RELOC_BASE)

    # Everything after the original dense grid remains byte-identical inside the retail payload.
    assert out[RELOC_BASE+layout['grid_bytes']:RELOC_BASE+len(retail_payload)] == retail_payload[layout['grid_bytes']:]

    # Validate authored grid/list pointers and record references.
    resource = out[RELOC_BASE:]
    new_grid, lists, decoded_memberships = parse_index(resource, layout['grid_bytes'], sentinel)
    assert bytes(resource[:layout['grid_bytes']]) == grid
    assert decoded_memberships == memberships
    valid_record_offsets = {row[0] for row in records}
    assert all(ref in valid_record_offsets for refs in lists.values() for ref in refs)
    assert all(ptr == 0 or NEW_POOL_OFFSET <= ptr < sentinel for ptr in new_grid)

    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = b'\0\0'
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = p16(checksum)

    report = {
        'schema': 'truerecall.m10d.new_world_record.v1',
        'base_sha1': BASE_SHA1,
        'scene': SCENE_INDEX,
        'relocated_resource': f'0x{RELOC_BASE:06X}',
        'new_record_offset': f'0x{NEW_RECORD_OFFSET:04X}',
        'new_record_address': f'0x{RELOC_BASE + NEW_RECORD_OFFSET:06X}',
        'new_record': {'world_type': 9, 'geometry': NEW_RECORD[2:]},
        'remote_pool_offset': f'0x{NEW_POOL_OFFSET:04X}',
        'remote_pool_bytes': len(pool),
        'remote_pool_end': f'0x{sentinel:04X}',
        'changed_cells': changed,
        'changed_cell_xy': [[i % layout['grid_w'], i // layout['grid_w']] for i in changed],
        'retail_payload_after_grid_unchanged': True,
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
