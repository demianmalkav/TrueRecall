#!/usr/bin/env python3
from __future__ import annotations

GRID_W = 54
GRID_H = 23
CELL_PX = 64
GRID_BYTES = 0x09B4
POOL_START = 0x09B4
POOL_END = 0x105A
SENTINEL = 0x105A
RECORD_START = 0x105C
RECORD_END = 0x1F02


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+2], 'big')


def p16(value: int) -> bytes:
    return int(value).to_bytes(2, 'big')


def parse_records(resource: bytes | bytearray):
    rows = []
    for off in range(RECORD_START, RECORD_END, 10):
        rows.append([
            off,
            u16(resource, off + 0),
            u16(resource, off + 2),
            u16(resource, off + 4),
            u16(resource, off + 6),
            u16(resource, off + 8),
        ])
    return rows


def parse_index(resource: bytes | bytearray):
    grid = [u16(resource, off) for off in range(0, GRID_BYTES, 2)]
    starts = sorted({ptr for ptr in grid if ptr})
    lists = {}
    for i, start in enumerate(starts):
        stop = starts[i + 1] if i + 1 < len(starts) else POOL_END
        lists[start] = tuple(u16(resource, off) & 0x7FFF for off in range(start, stop, 2))
    memberships = [tuple() if ptr == 0 else lists[ptr] for ptr in grid]
    return grid, lists, memberships


def cell_members(records, cx: int, cy: int):
    x0, y0 = cx * CELL_PX, cy * CELL_PX
    x1, y1 = x0 + CELL_PX, y0 + CELL_PX
    return tuple(sorted((
        off for off, _typ, rx0, ry0, rx1, ry1 in records
        if rx0 < x1 and rx1 > x0 and ry0 < y1 and ry1 > y0
    ), reverse=True))


def serialize_index(records):
    pointers = []
    pool = bytearray()
    seen = {}
    cursor = POOL_START
    memberships = []

    for cy in range(GRID_H):
        for cx in range(GRID_W):
            refs = cell_members(records, cx, cy)
            memberships.append(refs)
            if not refs:
                pointers.append(0)
                continue
            if refs not in seen:
                seen[refs] = cursor
                for i, ref in enumerate(refs):
                    pool += p16(ref | (0x8000 if i == 0 else 0))
                    cursor += 2
            pointers.append(seen[refs])

    grid = b''.join(p16(ptr) for ptr in pointers)
    return grid, bytes(pool), memberships


def assert_retail_exact(resource: bytes | bytearray):
    records = parse_records(resource)
    retail_grid, _lists, retail_memberships = parse_index(resource)
    grid, pool, memberships = serialize_index(records)
    assert grid == bytes(resource[:GRID_BYTES])
    assert pool == bytes(resource[POOL_START:POOL_END])
    assert memberships == retail_memberships
    assert len(grid) == GRID_BYTES
    assert len(pool) == POOL_END - POOL_START == 1702
    assert len(records) == 375
    assert len({ptr for ptr in retail_grid if ptr}) == 373
    return records
