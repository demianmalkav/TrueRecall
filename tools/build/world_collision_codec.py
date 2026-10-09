#!/usr/bin/env python3
from __future__ import annotations
import math

SCENE_TABLE = 0x013B4A
SCENE_COUNT = 19
CELL_PX = 64

# Scene-0 compatibility constants retained for older proof builders.
GRID_W = 54
GRID_H = 23
GRID_BYTES = 0x09B4
POOL_START = 0x09B4
POOL_END = 0x105A
SENTINEL = 0x105A
RECORD_START = 0x105C
RECORD_END = 0x1F02


def u16(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+2], 'big')


def s16(buf: bytes | bytearray, off: int) -> int:
    value = u16(buf, off)
    return value - 0x10000 if value & 0x8000 else value


def u32(buf: bytes | bytearray, off: int) -> int:
    return int.from_bytes(buf[off:off+4], 'big')


def p16(value: int) -> bytes:
    return int(value & 0xFFFF).to_bytes(2, 'big')


def _first_ffff(resource: bytes | bytearray, limit: int = 0x10000) -> int:
    for off in range(0, min(len(resource), limit), 2):
        if u16(resource, off) == 0xFFFF:
            return off
    raise ValueError('world-resource sentinel not found')


def _pool_start(resource: bytes | bytearray, sentinel: int) -> int:
    for off in range(0, sentinel, 2):
        if u16(resource, off) & 0x8000:
            return off
    return sentinel


def _factor_grid(cell_count: int, records) -> tuple[int, int]:
    if cell_count <= 0:
        raise ValueError('invalid cell count')
    max_x = max((r[4] for r in records), default=0)
    max_y = max((r[5] for r in records), default=0)
    target_w = max(1, math.ceil(max(0, max_x) / CELL_PX))
    target_h = max(1, math.ceil(max(0, max_y) / CELL_PX))
    candidates = []
    for gw in range(1, int(math.sqrt(cell_count)) + 1):
        if cell_count % gw:
            continue
        gh = cell_count // gw
        for w, h in ((gw, gh), (gh, gw)):
            score = abs(w - target_w) + abs(h - target_h)
            candidates.append((score, abs((w / h) - (target_w / target_h)), w, h))
    if not candidates:
        raise ValueError('no grid factorization')
    _, _, gw, gh = min(candidates)
    return gw, gh


def parse_index(resource: bytes | bytearray, grid_bytes: int, sentinel: int):
    grid = [u16(resource, off) for off in range(0, grid_bytes, 2)]
    starts = sorted({ptr for ptr in grid if ptr})
    for ptr in starts:
        if not (grid_bytes <= ptr < sentinel):
            raise ValueError(f'grid pointer out of list pool: 0x{ptr:04X}')
    lists = {}
    for i, start in enumerate(starts):
        stop = starts[i + 1] if i + 1 < len(starts) else sentinel
        refs = tuple(u16(resource, off) & 0x7FFF for off in range(start, stop, 2))
        lists[start] = refs
    memberships = [tuple() if ptr == 0 else lists[ptr] for ptr in grid]
    return grid, lists, memberships


def parse_records(resource: bytes | bytearray, record_start: int, record_count: int):
    rows = []
    for i in range(record_count):
        off = record_start + i * 10
        rows.append([
            off,
            u16(resource, off + 0),
            s16(resource, off + 2),
            s16(resource, off + 4),
            s16(resource, off + 6),
            s16(resource, off + 8),
        ])
    return rows


def raster_memberships(records, grid_w: int, grid_h: int):
    """Reproduce Beam's retail rasterizer, including linear-row wrap quirks."""
    cells = [[] for _ in range(grid_w * grid_h)]
    for off, _typ, x0, y0, x1, y1 in records:
        if x1 <= x0 or y1 <= y0:
            continue
        c0 = math.floor(x0 / CELL_PX)
        c1 = math.floor((x1 - 1) / CELL_PX)
        r0 = math.floor(y0 / CELL_PX)
        r1 = math.floor((y1 - 1) / CELL_PX)
        for row in range(r0, r1 + 1):
            base = row * grid_w
            for col in range(c0, c1 + 1):
                index = base + col
                if 0 <= index < len(cells):
                    cells[index].append(off)
    return [tuple(sorted(refs, reverse=True)) for refs in cells]


def serialize_memberships(memberships, grid_bytes: int, pool_start: int | None = None):
    pointers = []
    pool = bytearray()
    seen = {}
    cursor = grid_bytes if pool_start is None else pool_start
    for refs in memberships:
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
    return grid, bytes(pool)


def serialize_index(records, grid_w: int, grid_h: int, pool_start: int | None = None):
    memberships = raster_memberships(records, grid_w, grid_h)
    grid_bytes = 2 * grid_w * grid_h
    grid, pool = serialize_memberships(memberships, grid_bytes, pool_start)
    return grid, pool, memberships


def discover_scene_layout(rom: bytes | bytearray, scene_index: int):
    if not (0 <= scene_index < SCENE_COUNT):
        raise ValueError('scene out of range')
    scene = u32(rom, SCENE_TABLE + scene_index * 4)
    world_base = u32(rom, scene + 0x0E)
    resource = rom[world_base:]

    sentinel = _first_ffff(resource)
    grid_bytes = _pool_start(resource, sentinel)
    grid, lists, retail_memberships = parse_index(resource, grid_bytes, sentinel)
    record_start = sentinel + 2

    refs = sorted({ref for members in retail_memberships for ref in members})
    if refs:
        if refs[0] != record_start:
            raise ValueError('record table does not begin immediately after sentinel')
        expected = list(range(record_start, refs[-1] + 10, 10))
        if refs != expected:
            raise ValueError('record references are not one contiguous 10-byte table')
        record_count = len(refs)
    else:
        record_count = 0
    records = parse_records(resource, record_start, record_count)

    cell_count = grid_bytes // 2
    map_desc = u32(rom, scene + 0x16)
    map_w = u16(rom, map_desc + 0x10)
    map_h = u16(rom, map_desc + 0x12)
    candidate = (math.ceil(map_w / 2), math.ceil(map_h / 2))
    if candidate[0] * candidate[1] == cell_count:
        grid_w, grid_h = candidate
        dimension_source = 'scene_map_dimensions'
    else:
        grid_w, grid_h = _factor_grid(cell_count, records)
        dimension_source = 'record_extent_factorization'

    return {
        'scene_index': scene_index,
        'scene_record': scene,
        'world_base': world_base,
        'grid_w': grid_w,
        'grid_h': grid_h,
        'grid_bytes': grid_bytes,
        'pool_start': grid_bytes,
        'pool_end': sentinel,
        'pool_bytes': sentinel - grid_bytes,
        'sentinel': sentinel,
        'record_start': record_start,
        'record_count': record_count,
        'record_end': record_start + record_count * 10,
        'grid': grid,
        'lists': lists,
        'retail_memberships': retail_memberships,
        'records': records,
        'map_width': map_w,
        'map_height': map_h,
        'dimension_source': dimension_source,
    }


def assert_retail_exact_scene(rom: bytes | bytearray, scene_index: int):
    layout = discover_scene_layout(rom, scene_index)
    resource = rom[layout['world_base']:]
    grid, pool, memberships = serialize_index(layout['records'], layout['grid_w'], layout['grid_h'])
    assert grid == bytes(resource[:layout['grid_bytes']])
    assert pool == bytes(resource[layout['pool_start']:layout['pool_end']])
    assert memberships == layout['retail_memberships']
    return layout


def assert_retail_exact(resource: bytes | bytearray):
    """Backward-compatible scene-0 resource assertion used by M10C."""
    records = parse_records(resource, RECORD_START, 375)
    grid, lists, memberships = parse_index(resource, GRID_BYTES, SENTINEL)
    built_grid, pool, built_memberships = serialize_index(records, GRID_W, GRID_H)
    assert built_grid == bytes(resource[:GRID_BYTES])
    assert pool == bytes(resource[POOL_START:POOL_END])
    assert memberships == built_memberships
    assert len(grid) == GRID_W * GRID_H
    assert len(lists) == 373
    return records
