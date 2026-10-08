# M0.6E — VM Source Relocation Proof

M0.6E proves that a retail object script can be exported to source, edited, assembled at a new ROM address, redirected through the retail type table and statically revalidated in the generated ROM.

It is a stronger authoring proof than M0.6D, but it is still not runtime-validated M0.7.

## Experiment

Object type: `69` — confirmed shotgun weapon pickup.

Retail script:

```text
0x1761F0
```

Relocated script:

```text
0x1FB000
```

The relocation target lies inside a verified retail padding run:

```text
0x1FABC3..0x1FFFFF = 21,565 bytes of 0xFF
```

The 258-byte relocated script fits entirely inside this region.

## Source edit

The exported source contains the retail grant:

```text
MOVI_W_D1 0x0005
ADD_D1_TO_D2
STORE_ABS_W_D2 0xFFFFFB72
```

M0.6E changes only that source immediate to `0x0006` before assembly.

The original retail script at `0x1761F0` remains untouched.

## Pointer redirection

The type pointer entry is:

```text
0x07953E + type_id*4
```

For type 69:

```text
entry address: 0x079652
retail value:  0x001761F0
M0.6E value:   0x001FB000
```

The selector table remains scripted/VM mode.

## Static post-build proof — CONFIRMED

`tools/build/m06e_relocated_shotgun_patch.py` regenerates the build from the canonical ROM and proves:

- canonical input SHA-1;
- retail pointer is exactly the expected `0x1761F0`;
- relocation region is pristine `0xFF` padding;
- exported source assembles successfully at `0x1FB000`;
- type 69 pointer is redirected to the new script;
- original and relocated scripts each decode to 68 reachable instruction addresses;
- normalized instruction opcode/size shape is identical;
- the edited immediate value is present in the relocated script;
- Sega checksum is recomputed automatically.

Generated build:

```text
checksum   = 0x31D7
output SHA-1 = b96416b0c421c8ee9c42f260955d90f6299a9412
```

The generated ROM is not committed to GitHub.

## Significance

M0.6E proves this pipeline on a real ROM image:

```text
retail object script
→ symbolic source
→ source edit
→ VM assembly
→ safe-space relocation
→ type-pointer patch
→ checksum repair
→ static re-disassembly/regression check
```

This is the core technical mechanism needed for new Total Recall object scripts.

## Remaining gate

Runtime validation is still required in an emulator or on hardware. The current execution environment does not provide a Genesis emulator, so the project must not claim that the generated build has executed successfully yet.

After runtime validation, the next stronger authoring proof should allocate a genuinely new scripted behavior/type rather than merely relocating an edited retail class.
