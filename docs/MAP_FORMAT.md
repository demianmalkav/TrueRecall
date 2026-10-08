# Gameplay Map Format

The gameplay scene/map system is now enumerated from its master table rather than inferred from isolated packages.

## Master scene table — CONFIRMED

A pointer table at `0x013B4A` contains **19 non-null scene records** followed by a null pointer. The records begin at `0x013B9A` and are spaced exactly `0x2E` bytes (46 bytes) apart.

Each record is:

```text
word header                 ; currently 0x0003 in all 19 records
long L0_palette_0
long L1_palette_1
long L2_aux                 ; unresolved
long L3_aux                 ; unresolved
long L4_aux                 ; unresolved/shared in many scenes
long L5_graphics_descriptor
long L6_plane_C_descriptor
long L7_plane_C_vram        ; 0x0000C000
long L8                     ; 0 in all 19 current records
long L9_plane_E_descriptor
long L10_plane_E_vram       ; 0x0000E000
```

Reproducible probe: `tools/rom_probe/level_master_probe.py`.

## Palette fields — CONFIRMED

`L0` and `L1` are identical in every current scene record and point to 128-byte Genesis CRAM images:

`4 palettes × 16 colors × 2 bytes = 128 bytes`

The first scene uses `0x09AC20`, the next `0x09ACA0`, then `0x09AD20`, etc. Every sampled word obeys the Genesis CRAM bit mask `0x0EEE`. These palettes have been used successfully to reconstruct all 19 scene maps in their native colors.

## Graphics descriptor — CONFIRMED structure, secondary semantics partial

`L5` points to a three-long descriptor:

```text
long graphics_lzbeam_ptr
long graphics_secondary_ptr
long graphics_aux_ptr
```

The first pointer is confirmed LZBeam-compressed Genesis tile data. Every one of the 19 scene records decodes to a size divisible by 32 bytes, i.e. complete 8×8 4bpp tiles.

The second pointer frequently has bit 31 set (for example `0x800178DA`, `0x800239FA`, `0x80050000`). The earlier shorthand “raw/non-LZ flag” remains plausible but is **not yet promoted to CONFIRMED semantics** until its consumer is recovered.

The third pointer is optional and zero in several scenes; its exact role is also unresolved.

## Plane descriptors — CONFIRMED

`L6` and `L9` each point to an 8-byte plane/map descriptor:

```text
long map_lzbeam_ptr
word width_tiles
word height_tiles
```

The decoded map size always satisfies:

`width × height × 2 bytes`

The record then supplies the destination VRAM bases explicitly:

- `L6` descriptor → `L7 = 0xC000`
- `L9` descriptor → `L10 = 0xE000`

This is stronger than the old “layer A/layer B” interpretation: these are independently described Genesis name-table planes with explicit VRAM destinations.

### Independent plane dimensions

The two planes do **not** always share dimensions. Examples:

- scene 5: C000 plane `104×48`, E000 plane `80×48`
- scene 6: C000 plane `71×110`, E000 plane `52×110`

Therefore editors and rebuild tools must preserve per-plane dimensions independently rather than assuming one scene rectangle applies to both.

## Scene dimension inventory — CONFIRMED

| Scene | C000 plane | E000 plane |
|---:|---:|---:|
| 0 | 107×45 | 107×45 |
| 1 | 20×253 | 20×253 |
| 2 | 50×39 | 50×39 |
| 3 | 9×13 | 9×13 |
| 4 | 50×78 | 50×78 |
| 5 | 104×48 | 80×48 |
| 6 | 71×110 | 52×110 |
| 7 | 74×60 | 74×60 |
| 8 | 45×16 | 45×16 |
| 9 | 70×69 | 70×69 |
| 10 | 95×54 | 95×54 |
| 11 | 60×58 | 60×58 |
| 12 | 45×80 | 45×80 |
| 13 | 78×66 | 78×66 |
| 14 | 13×400 | 13×400 |
| 15 | 32×43 | 32×43 |
| 16 | 36×44 | 36×44 |
| 17 | 46×31 | 46×31 |
| 18 | 18×40 | 18×40 |

The unusual `20×253` and `13×400` records are real descriptor values and their LZBeam streams decode to exactly those dimensions; they are not parser overrun artifacts.

## Previously isolated packages, now placed in the master table

### Scene 0

- palette: `0x09AC20`
- graphics descriptor: `0x00FFAA`
- graphics LZBeam: `0x014898` → `24,960` bytes = 780 tiles
- C000 plane descriptor: `0x00FFBE` → map `0x01D4EE`, `107×45`
- E000 plane descriptor: `0x00FFB6` → map `0x01C8FC`, `107×45`
- graphics secondary: `0x800178DA`
- graphics aux: `0x01BF7A`

### Scene 2

- palette: `0x09AD20`
- graphics descriptor: `0x00FFE2`
- graphics LZBeam: `0x02667A` → `21,504` bytes = 672 tiles
- C000 plane descriptor: `0x00FFF6` → map `0x01F0B8`, `50×39`
- E000 plane descriptor: `0x00FFEE` → map `0x01EACA`, `50×39`
- graphics secondary: `0x80029418`
- graphics aux: `0x01E7D0`

These are the two packages that originally proved the map representation. The master-table recovery now generalizes that result to all 19 records.

## Tilemap entries

Gameplay planes use standard 16-bit Genesis name-table entries: tile index plus palette/flip/priority attributes. Using each record's own CRAM data produces coherent true-color full-map renders.

## Auxiliary record fields still unresolved

The remaining high-value fields are now sharply isolated:

- `L2`: often itself LZBeam-decodable and small (`3–296` bytes in tested scenes); exact consumer/semantics unresolved
- `L3`: raw scene-specific resource; often arrays of small words; exact consumer/semantics unresolved
- `L4`: usually shared pointer `0x01FA62`, with at least one alternate value; exact semantics unresolved
- `graphics_secondary`: often high-bit flagged pointer; consumer/flag semantics unresolved
- `graphics_aux`: optional third graphics-resource pointer

These are now the prime candidates for collision/material data, animation/tile support data, spawns/objects, or mission scripting, but **none of those labels should be assigned without consumer-level evidence**.

## Required proof before level editor work

1. Recover the consumer(s) of `L2/L3/L4` and the two secondary graphics pointers.
2. Identify collision/material and object/spawn/script data explicitly.
3. Implement deterministic export/import for the master record, graphics descriptor and both plane descriptors.
4. Implement LZBeam encoding.
5. Prove a byte-stable no-op extract→rebuild cycle before authoring new maps.
