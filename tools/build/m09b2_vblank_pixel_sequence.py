#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, argparse

BASE = 'd39174bed46ede85531b86df7ba49123ce2f8411'
OLD = 0x200000
NEW = 0x400000
CHECK = 0x18E
ROM_END = 0x1A4
DIR_SRC = 0x13F32
DIR_DST = 0x200000
DIR_SIZE = 0x2000
SPRINT_BASE = 0x1FF0
REFS = [0x19AE, 0x1A24, 0x1A80, 0x1AA4, 0x1B0E, 0x1B32]
AH = 0x83A6
MH = 0x9864
AT = 0x207000
MT = 0x207080
ORIG = bytes.fromhex('08380006FB7F')
PLAYER_DESC = 0x0F0000
KEY_HOOK = 0x113B4
KEY_ORIG = bytes.fromhex('302d001202403fff')
KT = 0x208100
RENDER_HOOK = 0x1143C
RENDER_ORIG = bytes.fromhex('223010026a1a')
RT = 0x208000
BANKS = [0x210000, 0x218000, 0x220000, 0x228000]


def jmp(a):
    return b'\x4e\xf9' + a.to_bytes(4, 'big')


def checksum(b):
    s = 0
    for i in range(0x200, len(b) - 1, 2):
        s = (s + int.from_bytes(b[i:i+2], 'big')) & 0xFFFF
    return s


class A:
    def __init__(self):
        self.b = bytearray()
        self.lab = {}
        self.fx = []

    def e(self, x):
        self.b += x

    def label(self, n):
        self.lab[n] = len(self.b)

    def br(self, op, n):
        p = len(self.b)
        self.b += bytes([op, 0])
        self.fx.append((p + 1, p + 2, n))

    def done(self):
        for at, base, n in self.fx:
            d = self.lab[n] - base
            if not -128 <= d <= 127:
                raise ValueError((n, d))
            self.b[at] = d & 0xFF
        return bytes(self.b)


def phase_dispatch(a, load_fn):
    # Use VBlank word F712 low-byte bits2/3 at F713: each phase lasts 4 frames.
    a.e(bytes.fromhex('08380003F713'))
    a.br(0x66, 'hi')
    a.e(bytes.fromhex('08380002F713'))
    a.br(0x66, 'p1')
    load_fn(a, 0)
    a.br(0x60, 'done')
    a.label('p1')
    load_fn(a, 1)
    a.br(0x60, 'done')
    a.label('hi')
    a.e(bytes.fromhex('08380002F713'))
    a.br(0x66, 'p3')
    load_fn(a, 2)
    a.br(0x60, 'done')
    a.label('p3')
    load_fn(a, 3)
    a.label('done')


def key_trampoline():
    a = A()
    a.e(bytes.fromhex('302D001202403FFF'))
    a.e(bytes.fromhex('08380005F6EC'))
    a.br(0x67, 'exit')
    a.e(bytes.fromhex('2F08206E002CB1FC') + PLAYER_DESC.to_bytes(4, 'big') + bytes.fromhex('205F'))
    a.br(0x66, 'exit')
    a.e(bytes.fromhex('024000FF'))

    def load(asm, i):
        asm.e(bytes.fromhex('0040') + (0x3C00 + i * 0x100).to_bytes(2, 'big'))

    phase_dispatch(a, load)
    a.label('exit')
    a.e(jmp(0x113BC))
    return a.done()


def render_trampoline():
    a = A()
    a.e(bytes.fromhex('22301002'))
    a.e(bytes.fromhex('08380005F6EC'))
    a.br(0x67, 'finish')
    a.e(bytes.fromhex('2F08206E002CB1FC') + PLAYER_DESC.to_bytes(4, 'big') + bytes.fromhex('205F'))
    a.br(0x66, 'finish')

    def load(asm, i):
        asm.e(bytes.fromhex('223C') + BANKS[i].to_bytes(4, 'big'))

    phase_dispatch(a, load)
    a.label('finish')
    # Preserve retail branch semantics at 0x1143C:
    # positive D1 -> 0x1145C, negative D1 -> 0x11442.
    a.e(bytes.fromhex('4A81'))
    a.br(0x6A, 'pos')
    a.e(jmp(0x11442))
    a.label('pos')
    a.e(jmp(0x1145C))
    return a.done()


def enc_tile(px, x0, y0):
    out = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            out.append((px[y0+y][x0+x] << 4) | px[y0+y][x0+x+1])
    return bytes(out)


def make_chunk(phase):
    # Original diagnostic 16x16 glyph. 0 transparent, phase colors 9..12.
    c = 9 + phase
    px = [[0] * 16 for _ in range(16)]
    for y in range(3, 13):
        for x in range(6, 10):
            px[y][x] = c
    if phase == 0:
        for x in range(3, 13):
            px[5][x] = c
        for y in range(11, 16):
            px[y][5] = c
            px[y][10] = c
    elif phase == 1:
        for k in range(5):
            px[5+k][5-k//2] = c
            px[5+k][10+k//2] = c
        for k in range(5):
            px[11+k][6-k//2] = c
            px[11+k][9+k//2] = c
    elif phase == 2:
        for x in range(2, 14):
            px[8][x] = c
        for y in range(11, 16):
            px[y][7] = c
            px[y][8] = c
    else:
        for k in range(6):
            px[4+k][3+k] = c
            px[4+k][12-k] = c
        for k in range(5):
            px[11+k][5+k//2] = c
            px[11+k][10-k//2] = c
    return b''.join(enc_tile(px, tx*8, ty*8) for tx in range(2) for ty in range(2))


def build(raw):
    assert len(raw) == OLD and hashlib.sha1(raw).hexdigest() == BASE
    assert raw[KEY_HOOK:KEY_HOOK+8] == KEY_ORIG
    assert raw[RENDER_HOOK:RENDER_HOOK+6] == RENDER_ORIG

    b = bytearray(raw) + bytearray([0xFF]) * (NEW - OLD)
    b[ROM_END:ROM_END+4] = (NEW - 1).to_bytes(4, 'big')

    # Retain M0.7 sprint behavior and safe direction row.
    b[DIR_DST:DIR_DST+DIR_SIZE] = raw[DIR_SRC:DIR_SRC+DIR_SIZE]
    for p in REFS:
        b[p:p+4] = DIR_DST.to_bytes(4, 'big')
    b[DIR_DST+SPRINT_BASE:DIR_DST+SPRINT_BASE+16] = raw[DIR_SRC+0xF2:DIR_SRC+0xF2+16]
    anim = bytes.fromhex('08380005F6EC670A303C1FF0') + jmp(0x83C2) + ORIG + jmp(0x83AC)
    move = bytes.fromhex('08380005F6EC6714303C0300323C02804EB900009D8A') + jmp(0x97FA) + ORIG + jmp(0x986A)
    b[AT:AT+len(anim)] = anim
    b[MT:MT+len(move)] = move
    b[AH:AH+6] = jmp(AT)
    b[MH:MH+6] = jmp(MT)

    # Four complete raw banks. Repeating the authored chunk over all indices
    # makes the proof independent of the retail chunk IDs selected by geometry.
    phase_hashes = []
    for phase, base in enumerate(BANKS):
        ch = make_chunk(phase)
        phase_hashes.append(hashlib.sha1(ch).hexdigest())
        b[base:base+0x8000] = ch * 256

    kt = key_trampoline()
    rt = render_trampoline()
    assert len(kt) < 0x100 and len(rt) < 0x100
    b[KT:KT+len(kt)] = kt
    b[KEY_HOOK:KEY_HOOK+8] = jmp(KT) + bytes.fromhex('4E71')
    b[RT:RT+len(rt)] = rt
    b[RENDER_HOOK:RENDER_HOOK+6] = jmp(RT)

    b[CHECK:CHECK+2] = b'\0\0'
    cs = checksum(b)
    b[CHECK:CHECK+2] = cs.to_bytes(2, 'big')
    rep = {
        'schema': 'truerecall.m09b2.vblank_pixel_sequence.v1',
        'base_sha1': BASE,
        'output_sha1': hashlib.sha1(b).hexdigest(),
        'rom_size': NEW,
        'vblank_counter': 'FFFFF712',
        'phase_formula': '(F712 >> 2) & 3',
        'cache_namespaces': ['0x3C00|index', '0x3D00|index', '0x3E00|index', '0x3F00|index'],
        'banks': [hex(x) for x in BANKS],
        'phase_chunk_sha1': phase_hashes,
        'player_desc_scope': hex(PLAYER_DESC),
        'key_trampoline_bytes': len(kt),
        'render_trampoline_bytes': len(rt),
        'checksum': f'0x{cs:04X}',
        'runtime_validation': 'external deterministic BlastEm regression required',
    }
    return bytes(b), rep


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--report', type=Path)
    args = ap.parse_args()
    out, report = build(args.rom.read_bytes())
    args.out.write_bytes(out)
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.write_text(text + '\n', encoding='utf-8')
