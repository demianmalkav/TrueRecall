# Sprite Authoring Pipeline

M0.8 proved that authored sprite bytes can reach the player at runtime. This document defines the inverse source-asset format that turns artwork into the structures consumed by the recovered renderer.

## Mapping geometry — CONFIRMED

The four geometry words in a mapping record are now named:

```text
record+0x06  origin_x
record+0x08  origin_y
record+0x0A  clip_width
record+0x0C  clip_height
```

Renderer proof:

- non-flipped X clipping computes `object_screen_x - origin_x`, then tests `+ clip_width`;
- flipped X uses the mirrored equivalent;
- Y uses the same pattern with `origin_y / clip_height`;
- helper `0x00194A` returns:

```text
D0 = (clip_width  >> 1) - origin_x
D1 = (clip_height >> 1) - origin_y
```

with sign correction for flipped presentation.

The origin therefore describes the actor anchor/hotspot inside the clipping box; width/height describe the clipping extent, not necessarily the exact nontransparent pixel extent.

## Piece-coordinate bias — CONFIRMED

Stored piece coordinate bytes have a +15 bias:

```text
local_x = stored_x - 15
local_y = stored_y - 15
```

The renderer later adds `0x71` before writing SAT coordinates. Because `15 + 0x71 = 0x80`, the combination supplies the Genesis sprite-coordinate hardware bias while leaving source piece positions convenient in local frame coordinates.

Therefore the inverse compiler writes:

```text
stored_x = local_x + 15
stored_y = local_y + 15
```

## Chunk encoding — CONFIRMED

One mapping piece always refers to one 16×16 chunk:

```text
16×16 pixels
= 4 × 8×8 tiles
= 128 bytes at 4bpp
```

The four tiles are stored in Genesis multi-tile column-major order:

```text
top-left
bottom-left
top-right
bottom-right
```

Within each 8×8 tile, two 4-bit palette indexes are packed per byte, left pixel in the high nibble.

Palette index 0 is treated as transparent by the project source pipeline.

## Initial compiler — IMPLEMENTED

`tools/build/sprite_asset_compiler.py` currently supports:

- indexed PNG input using indexes 0..15;
- RGB/RGBA input with an explicit 16-color JSON palette;
- 16×16 aligned source-cell decomposition;
- transparent-cell omission;
- exact chunk deduplication;
- one graphics resource group per compile (`0..63`);
- piece-word generation;
- explicit origin / clip geometry;
- optional record control words and record flags;
- raw mapping-record output;
- raw contiguous chunk-bank output;
- machine-readable manifest output.

The compiler intentionally does not yet invent semantics for record words `+0x00/+0x02/+0x04`. They default to zero and may be supplied explicitly. These fields are not required to prove basic static-frame compilation because a known retail player frame uses zeros there.

## Byte-exact retail inversion — CONFIRMED

`tools/rom_probe/sprite_compiler_roundtrip_probe.py` uses retail player archetype `191`, animation selector `2`.

That frame is an ideal inversion fixture:

```text
origin_x    = 9
origin_y    = 5
clip_width  = 16
clip_height = 32
record flags = 0x40
pieces = 2
```

The probe reconstructs the source indexed image from the two retail chunks, runs it through the new compiler, and asserts:

1. the complete mapping record is byte-identical to retail;
2. compiled chunk 0 is byte-identical to retail chunk 0;
3. compiled chunk 1 is byte-identical to retail chunk 1.

This simultaneously validates the inverse 4bpp packing, tile ordering, +15 coordinate bias, geometry fields, piece order and mapping-record serialization.

## Current source-frame constraints

The first version uses a simple aligned authoring model: source art is divided on a 16-pixel grid from the source image origin. This is sufficient for new art and deterministic compilation, but it does not attempt to recreate every hand-offset retail mapping optimally.

A later optimizer may pack arbitrary piece positions or deduplicate flipped equivalents. That optimization is not required for the first Quaid animation and must not precede correctness/regression evidence.

## Quaid pipeline target

The next production path is:

```text
Quaid source frame / sheet
→ fixed 16-color palette
→ 4bpp indexed pixels
→ aligned 16×16 decomposition
→ deduplicated 128-byte chunks
→ resource group / chunk IDs
→ mapping records with explicit anchor geometry
→ animation descriptor / selector row
→ expanded-ROM resource placement
→ runtime cache/VRAM path
→ deterministic BlastEm regression
```

A coherent animation is production-ready only when it is reproducible from source art, visible only in its intended player state, returns cleanly to the retail/fallback path and stays inside measured VRAM/cache/sprite budgets.
