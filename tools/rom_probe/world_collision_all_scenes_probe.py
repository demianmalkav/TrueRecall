#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build'))
from world_collision_codec import SCENE_COUNT, CELL_PX, assert_retail_exact_scene

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = 'd39174bed46ede85531b86df7ba49123ce2f8411'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--json', type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    assert len(rom) == EXPECTED_SIZE
    digest = hashlib.sha1(rom).hexdigest()
    assert digest == EXPECTED_SHA1

    scenes = []
    for i in range(SCENE_COUNT):
        layout = assert_retail_exact_scene(rom, i)
        records = layout['records']
        out_of_bounds = sum(
            1 for _off, _typ, x0, y0, x1, y1 in records
            if x0 < 0 or y0 < 0 or x1 > layout['grid_w'] * CELL_PX or y1 > layout['grid_h'] * CELL_PX
        )
        scenes.append({
            'scene': i,
            'scene_record': f"0x{layout['scene_record']:06X}",
            'world_base': f"0x{layout['world_base']:06X}",
            'grid_w': layout['grid_w'],
            'grid_h': layout['grid_h'],
            'cell_px': CELL_PX,
            'grid_bytes': layout['grid_bytes'],
            'pool_bytes': layout['pool_bytes'],
            'unique_lists': len(layout['lists']),
            'nonempty_cells': sum(bool(x) for x in layout['grid']),
            'record_start': f"0x{layout['record_start']:04X}",
            'record_count': layout['record_count'],
            'max_list_len': max((len(x) for x in layout['retail_memberships']), default=0),
            'out_of_bounds_records': out_of_bounds,
            'dimension_source': layout['dimension_source'],
            'exact_grid_pool_roundtrip': True,
        })

    assert scenes[6]['grid_w'] == 26 and scenes[6]['grid_h'] == 55
    assert scenes[18]['record_count'] == 0 and scenes[18]['pool_bytes'] == 0
    report = {
        'schema': 'truerecall.world_collision_all_scenes.v1',
        'base_sha1': digest,
        'scene_count': SCENE_COUNT,
        'all_exact_grid_pool_roundtrip': True,
        'cell_size_px': CELL_PX,
        'coordinate_encoding': 'signed 16-bit',
        'raster_policy': 'row/column raster over linear cell array; preserve duplicate refs; discard only linear indices outside grid',
        'scenes': scenes,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
