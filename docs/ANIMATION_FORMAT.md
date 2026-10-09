# Animation Descriptor Format

The archetype table points to an animation descriptor, not directly to sprite pixels. That descriptor resolves animation selectors into mapping records consumed by the common actor renderer.

## Selector indirection — CONFIRMED

`object+0x2C` holds the descriptor base. Routine `0x00FDDC` receives an animation selector in `D0` and resolves it in two stages:

```text
encoded = word(descriptor + animation_selector)
object+0x24 = encoded
alias_offset = encoded & 0x0FFE
record_offset = word(descriptor + alias_offset)
object+0x20 = record_offset
```

The low bit and upper bits of `encoded` carry animation/link/render state. Their full semantic labeling is intentionally incomplete, but the indirection itself is confirmed.

## Mapping record — CONFIRMED

A resolved record begins at:

```text
descriptor + object+0x20
```

Layout:

```text
+0x00  word  control/sequencing field 0   [unresolved]
+0x02  word  control/sequencing field 1   [unresolved]
+0x04  word  control/sequencing field 2   [unresolved]
+0x06  word  origin_x
+0x08  word  origin_y
+0x0A  word  clip_width
+0x0C  word  clip_height
+0x0E  byte  record/render flags
+0x0F  byte  piece_count
+0x10  piece[0]   4 bytes
+0x14  piece[1]   4 bytes
...
```

Record size:

```text
0x10 + piece_count * 4
```

The first three words remain explicitly unresolved. They may be zero in valid retail player frames and the authoring compiler therefore exposes them as optional explicit fields rather than inventing semantics.

## Geometry fields — CONFIRMED

Renderer clipping around `0x0112DE–0x011368` establishes the four geometry fields.

For non-flipped X presentation, the renderer computes a left coordinate from:

```text
object_screen_x - origin_x
```

and uses `clip_width` for the opposite visibility bound. Flipped X uses the mirrored equivalent. Y repeats the same logic with `origin_y` and `clip_height`.

Independent helper `0x00194A` resolves the current mapping record and returns:

```text
D0 = (clip_width  >> 1) - origin_x
D1 = (clip_height >> 1) - origin_y
```

with sign correction when the object is flipped.

Thus `origin_x/origin_y` are anchor/hotspot coordinates inside the frame's clip box; width/height are clipping geometry and may intentionally include transparent margin.

## Four-byte piece format — CONFIRMED

Each piece is:

```text
+0  byte  stored_x
+1  byte  stored_y
+2  word  graphics/flip id
```

The coordinate bytes contain a +15 bias:

```text
local_x = stored_x - 15
local_y = stored_y - 15
```

The renderer later adds `0x71` before writing SAT coordinates, so the two constants combine to the Genesis sprite coordinate bias `0x80`.

The piece word is:

```text
bit 15       V flip
bit 14       H flip
bits 13..8   graphics resource group (0..63)
bits 7..0    chunk index (0..255)
```

The renderer masks `piece_word & 0x3FFF` for its dynamic VRAM cache key.

## Piece graphics — CONFIRMED

Every piece is one fixed **16×16** Genesis sprite:

```text
2×2 8×8 tiles
4 tiles × 32 bytes = 128 bytes
```

Tile order for the 2×2 sprite is column-major:

```text
top-left
bottom-left
top-right
bottom-right
```

Chunk resources can be contiguous raw 128-byte blocks or indexed blocks using the recovered chunk-local RLE codec. See `docs/SPRITE_RENDERER.md`.

## Independent boundary proof

Representative selector-2 records:

| Archetype | descriptor | record offset | pieces | computed size | next record |
|---:|---:|---:|---:|---:|---:|
| player 191 | `0x0E51FE` | `0x0168` | 2 | `0x18` | `0x0180` |
| 176 | `0x1008CE` | `0x015E` | 1 | `0x14` | `0x0172` |
| 166 | `0x12E720` | `0x0114` | 7 | `0x2C` | `0x0140` |
| 8 | `0x0DFD48` | `0x00EA` | 11 | `0x3C` | `0x0126` |

In each case the next record begins exactly at `record + 0x10 + 4*N`.

## Inverse authoring proof — CONFIRMED

`tools/build/sprite_asset_compiler.py` implements the inverse mapping/chunk path.

`tools/rom_probe/sprite_compiler_roundtrip_probe.py` reconstructs retail player archetype `191`, selector `2`, and recompiles:

- the complete mapping record byte-identically;
- both 128-byte chunks byte-identically.

That proof closes the structural inversion needed for the first Quaid frame compiler.

See `docs/SPRITE_AUTHORING.md` for the source-art pipeline and current constraints.
