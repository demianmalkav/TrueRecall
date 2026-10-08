# Sprite Renderer / Piece Resource Format

This document closes the presentation chain from animation mapping records to the fixed-size sprite chunks loaded into VRAM.

## Renderer consumer — CONFIRMED

The main actor-sprite renderer is in the `0x0111CC–0x0114D4` region. It walks the active entity list, resolves the current animation mapping record, clips it against the camera, iterates its `piece_count`, looks up/caches graphical chunks and writes Genesis SAT entries.

The piece loop begins from the record resolved through `object+0x2C` / `object+0x20` as documented in `ANIMATION_FORMAT.md`.

Reproducible probe: `tools/rom_probe/sprite_piece_probe.py`.

## Four-byte piece format — CONFIRMED

Each mapping-record piece is exactly four bytes:

```text
+0x00  byte  x_offset
+0x01  byte  y_offset
+0x02  word  graphics/flip word
```

The two position bytes are treated as relative 8-bit offsets and are combined with the entity/camera position. Renderer-side flip handling mirrors these offsets when the containing animation/entity is horizontally or vertically flipped.

The 16-bit graphics/flip word is:

```text
bit 15       vertical flip
bit 14       horizontal flip
bits 13..8   graphics resource group (0..63)
bits 7..0    chunk index within group (0..255)
```

For cache lookup the renderer masks the word with `0x3FFF`, excluding the two flip bits.

A compact implementation detail confirms the packing: the renderer reads the high byte, doubles it twice as an 8-bit value, and uses the result to index the descriptor's long-pointer group table. The two upper flip bits disappear naturally through 8-bit overflow while the six-bit group value becomes `group*4`.

## Piece geometry — CONFIRMED

Every piece is a fixed Genesis sprite of **2×2 tiles = 16×16 pixels**.

The SAT preparation path writes size bits `0x0500`, which encode a two-tile width and two-tile height. Every graphical chunk is correspondingly:

```text
4 tiles × 32 bytes/tile = 128 bytes
```

The four 8×8 Genesis tiles are consumed in the platform's multi-tile sprite ordering (column-major for the 2×2 block).

This fixed-size piece model explains how larger actors are built: the animation mapping record simply composes multiple 16×16 chunks at relative X/Y offsets.

## Graphics resource group table — CONFIRMED

For a piece group `g`, the renderer reads:

```text
long source = descriptor + 0x02 + g*4
```

The long supports two storage modes.

### Positive source pointer: contiguous raw chunks

When bit 31 is clear:

```text
chunk_source = source + index*128
```

The renderer transfers exactly 128 bytes.

### Bit-31 source pointer: indexed chunk table

When bit 31 is set, the remaining 31 bits are a word-offset table base:

```text
table = source & 0x7FFFFFFF
entry = word(table + index*2)
```

Then:

- `entry bit15 = 0`: `table + entry` contains a raw 128-byte chunk.
- `entry bit15 = 1`: `table + (entry & 0x7FFF)` contains a compact RLE stream that expands to one 128-byte chunk.

This bit-31 convention is analogous in spirit to other direct/resource flags in the engine, but the sprite-chunk table and its codec are distinct from LZBeam.

## 128-byte sprite micro-codec — CONFIRMED

The decoder begins at approximately `0x0114D6`.

Command byte semantics:

```text
0x00          end stream
0x01..0x7F    copy (128 - command) literal bytes
0x80..0xFF    repeat next byte (256 - command) times
```

Valid retail chunks tested by the probe terminate at exactly 128 decompressed bytes.

This is a small chunk-local RLE codec, not LZBeam.

## Dynamic VRAM cache — CONFIRMED

The renderer does not keep every actor chunk permanently resident in VRAM. It maintains a dynamic cache keyed by:

```text
piece_word & 0x3FFF
```

A cache slot represents one 128-byte / four-tile chunk. On a miss, the selected chunk is resolved/decompressed and sent through the VDP transfer routine near `0x0132DC` with a transfer length of `0x80` bytes.

The cache slot becomes the sprite's tile base:

```text
VRAM chunk slot  -> 4 consecutive tiles
SAT tile index   -> slot * 4
```

This is an important production constraint: actor animation cost is not just ROM size. A frame can create cache pressure proportional to the number of distinct 16×16 chunks needed concurrently.

## SAT attribute construction — CONFIRMED / PARTIAL

The two flip bits from the piece word are shifted into the Genesis sprite-attribute H/V flip positions and combined with the renderer's base attribute word.

The base attribute word also carries animation/entity/global render flags, including palette/priority state. The exact full provenance of palette selection is still being decoded; therefore debug exporters may reconstruct geometry and pixels correctly while using a synthetic palette unless scene/runtime palette state is explicitly supplied.

## End-to-end presentation chain

The recovered chain is now:

```text
placement type_id
    ↓ scripted/direct behavior
archetype ID (object+0x2A)
    ↓ 0x079906
animation descriptor (object+0x2C)
    ↓ animation selector / alias
mapping record (object+0x20)
    ↓ N pieces
4-byte piece
    ↓ group/index resolution
128-byte 16×16 graphical chunk
    ↓ dynamic cache / DMA
4 VRAM tiles
    ↓ SAT
16×16 sprite piece on screen
```

This is sufficient to build a structural actor/frame exporter and to reconstruct animation geometry directly from the canonical ROM.

## Production consequences for Total Recall

A future actor-authoring pipeline can operate in fixed 16×16 pieces rather than trying to infer arbitrary Genesis sprite shapes. New animation frames can potentially be compiled as:

```text
source image / sprite sheet
→ 16×16 piece decomposition
→ deduplicated 128-byte chunks
→ raw or RLE chunk groups
→ mapping records
→ animation descriptor
→ archetype
```

Before insertion work begins, the inverse encoder must reproduce known retail chunks/records without behavioral change, and VRAM-cache pressure must be included in regression/performance tests.

## Next targets

1. Promote the current debug frame renderer into a repository tool.
2. Decode palette/priority provenance in the base SAT attribute word.
3. Enumerate selectors actually reached by each placed archetype and export representative frames for classification.
4. Cross-correlate visual family, callbacks, stats, VM natives and scene distribution before assigning semantic actor names.
5. Implement inverse encoding only after exporter output is stable and round-trippable.
