#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

BASE_SHA1 = 'd39174bed46ede85531b86df7ba49123ce2f8411'
OLD_SIZE = 0x200000
NEW_SIZE = 0x400000
CHECKSUM_OFF = 0x18E
ROM_END_OFF = 0x1A4
SCENE_TABLE = 0x013B4A
SCENE_INDEX = 0
RELOC_BASE = 0x230000

PROFILES = {
    'player': {
        'record_offset': 0x1C46,
        'before': 9,
        'after': 11,
        'geometry': (736, 544, 752, 800),
        'semantic_change': 'player: standard collision -> no-op; projectile path is not the validation target',
    },
    'projectile': {
        'record_offset': 0x1C6E,
        'before': 9,
        'after': 10,
        'geometry': (464, 496, 784, 544),
        'semantic_change': 'projectile: standard collision -> no-op; player remains on the standard collision handler',
    },
}


def u16(b: bytes, off: int) -> int:
    return int.from_bytes(b[off:off+2], 'big')


def u32(b: bytes, off: int) -> int:
    return int.from_bytes(b[off:off+4], 'big')


def genesis_checksum(b: bytes) -> int:
    value = 0
    for off in range(0x200, len(b) - 1, 2):
        value = (value + int.from_bytes(b[off:off+2], 'big')) & 0xFFFF
    return value


def build(raw: bytes, profile_name: str):
    profile = PROFILES[profile_name]
    assert len(raw) == OLD_SIZE
    assert hashlib.sha1(raw).hexdigest() == BASE_SHA1

    scene = u32(raw, SCENE_TABLE + SCENE_INDEX * 4)
    src = u32(raw, scene + 0x0E)
    all_bases = sorted({u32(raw, u32(raw, SCENE_TABLE + i * 4) + 0x0E) for i in range(19)})
    nxt = min(x for x in all_bases if x > src)
    payload = raw[src:nxt]
    assert (scene, src, nxt, len(payload)) == (0x013B9A, 0x07A42E, 0x07C7EC, 0x23BE)

    ro = profile['record_offset']
    assert u16(raw, src + ro) == profile['before']
    geometry = tuple(u16(raw, src + ro + delta) for delta in (2, 4, 6, 8))
    assert geometry == profile['geometry']

    out = bytearray(raw) + bytearray([0xFF]) * (NEW_SIZE - OLD_SIZE)
    out[ROM_END_OFF:ROM_END_OFF+4] = (NEW_SIZE - 1).to_bytes(4, 'big')
    out[RELOC_BASE:RELOC_BASE+len(payload)] = payload
    out[scene+0x0E:scene+0x12] = RELOC_BASE.to_bytes(4, 'big')
    out[RELOC_BASE+ro:RELOC_BASE+ro+2] = profile['after'].to_bytes(2, 'big')

    # M10B must differ from the M10A relocation payload only at the selected type word.
    assert out[RELOC_BASE:RELOC_BASE+ro] == raw[src:src+ro]
    assert out[RELOC_BASE+ro+2:RELOC_BASE+len(payload)] == raw[src+ro+2:nxt]
    assert tuple(u16(out, RELOC_BASE + ro + delta) for delta in (2, 4, 6, 8)) == profile['geometry']
    assert u16(out, RELOC_BASE + ro) == profile['after']

    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = b'\0\0'
    checksum = genesis_checksum(out)
    out[CHECKSUM_OFF:CHECKSUM_OFF+2] = checksum.to_bytes(2, 'big')

    report = {
        'schema': 'truerecall.m10b.targeted_collision.v1',
        'profile': profile_name,
        'base_sha1': BASE_SHA1,
        'scene': SCENE_INDEX,
        'scene_record': f'0x{scene:06X}',
        'retail_resource': f'0x{src:06X}',
        'relocated_resource': f'0x{RELOC_BASE:06X}',
        'record_offset': f'0x{ro:04X}',
        'record_address': f'0x{RELOC_BASE + ro:06X}',
        'geometry_xyxy': list(profile['geometry']),
        'world_type_before': profile['before'],
        'world_type_after': profile['after'],
        'checksum': f'0x{checksum:04X}',
        'output_sha1': hashlib.sha1(out).hexdigest(),
        'semantic_change': profile['semantic_change'],
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('profile', choices=sorted(PROFILES))
    ap.add_argument('rom', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()

    out, report = build(args.rom.read_bytes(), args.profile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
