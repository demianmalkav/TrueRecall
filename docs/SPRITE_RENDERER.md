# Sprite Renderer / Piece Resource Format

This document records the durable presentation chain from animation mapping records to fixed-size sprite chunks loaded into VRAM. Current milestone priority is defined by `docs/PROJECT_STATE.md`.

## Renderer consumer — CONFIRMED

The main actor-sprite renderer is in `0x0111CC–0x0114D4`. It walks active entities, resolves the current mapping record, clips against the camera, iterates pieces, resolves/caches graphical chunks and writes Genesis SAT entries.

The piece loop begins from state resolved through `object+0x2C` / `object+0x20` as documented in `ANIMATION_FORMAT.md`.

Reproducible structural probe:

```text
tools/rom_probe/sprite_piece_probe.py
```

## Four-byte piece format — CONFIRMED

Each piece is exactly four bytes:

```text
+0x00  byte  x_offset
+0x01  byte  y_offset
+0x02  word  graphics/flip word
```

Graphics/flip word:

```text
bit 15       vertical flip
bit 14       horizontal flip
bits 13..8   graphics resource group (0..63)
bits 7..0    chunk index within group (0..255)
```

Cache identity is:

```text
piece_word & 0x3FFF
```

Renderer-side flip handling mirrors relative offsets as required.

## Piece geometry — CONFIRMED

Each piece is fixed at **2×2 Genesis tiles = 16×16 pixels**.

SAT preparation uses size bits `0x0500`. One graphical chunk is:

```text
4 tiles × 32 bytes = 128 bytes
```

Larger actors are composed from multiple 16×16 pieces in a mapping record.

## Graphics resource group table — CONFIRMED

For piece group `g`:

```text
long source = descriptor + 0x02 + g*4
```

### Positive source pointer — raw chunks

When bit 31 is clear:

```text
chunk_source = source + index*128
```

Exactly 128 bytes are transferred.

### Bit-31 source pointer — indexed chunk table

When bit 31 is set:

```text
table = source & 0x7FFFFFFF
entry = word(table + index*2)
```

- `entry bit15 = 0`: `table + entry` contains raw 128-byte data;
- `entry bit15 = 1`: `table + (entry & 0x7FFF)` contains chunk-local RLE expanding to 128 bytes.

This codec is distinct from LZBeam.

## 128-byte sprite micro-codec — CONFIRMED

Decoder begins near `0x0114D6`.

```text
0x00          end stream
0x01..0x7F    copy (128 - command) literal bytes
0x80..0xFF    repeat next byte (256 - command) times
```

Tested retail chunks terminate at exactly 128 decompressed bytes.

## Dynamic VRAM cache — CONFIRMED

Cache key:

```text
piece_word & 0x3FFF
```

A slot represents one 128-byte/four-tile chunk. On miss, the selected chunk is resolved/decompressed and sent through the VDP transfer path near `0x0132DC` with length `0x80`.

The cache slot becomes the sprite tile base:

```text
VRAM chunk slot -> 4 consecutive tiles
SAT tile index  -> slot * 4
```

This makes cache pressure a first-class production budget, not just ROM size.

## SAT attribute construction — CONFIRMED / PARTIAL

Piece flip bits are shifted into Genesis H/V flip attribute positions and combined with the renderer base attribute word.

The base word also carries palette/priority-related state. Full provenance remains partially unresolved; geometry/pixel exporters can therefore be correct while requiring supplied/synthetic palette context.

## Recovered end-to-end presentation chain

```text
placement / behavior
    ↓
archetype identity (object+0x2A)
    ↓ presentation initialization
animation/presentation descriptor (object+0x2C)
    ↓ native selector / phase state
mapping record (object+0x20)
    ↓ N pieces
4-byte piece
    ↓ group/index resolution
128-byte 16×16 chunk
    ↓ dynamic VRAM cache / DMA
4 VRAM tiles
    ↓ SAT
16×16 on-screen sprite piece
```

The generic chain is confirmed. The live linked-player identity is more specific and must not be inferred solely from archetype-table naming.

## M0.8 runtime authoring proof — CONFIRMED

M0.8 established that independently authored bytes can be routed through renderer/cache/VRAM/SAT and produce only a compact player-local active difference with exact inactive fallback.

Its scoped descriptor `0x0F0000` remains valid **player-local visual-component evidence**.

M0.9C later falsified the stronger statement that `0x0F0000` is the canonical F9F8 world/render-avatar descriptor.

## M0.9C linked-player refinement — CONFIRMED

Canonical runtime sprint path:

```text
FFFFF9F8 -> FFFFC632
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

Descriptor remains stable while native F9F8 phase cycles through raw deltas:

```text
0, 2, 4, 6, 8, 10
```

The native bridge at `0x009D5E` writes `+0x1E -> +0x24 -> +0x20` as one phase-advance transaction.

Current M09C builder scopes authored source/cache substitution to canonical descriptor `0x000A0000` and selects six banks from that native phase.

## Current authoring pipeline — IMPLEMENTED

The project no longer merely has a future design for an inverse encoder. It already has production-facing compiler foundations:

```text
source frame(s)
→ palette/index representation
→ 16×16 decomposition
→ transparent-cell pruning
→ global cross-frame chunk deduplication
→ mapping records
→ authored chunk banks
→ isolated cache namespaces
→ renderer/cache/VRAM/SAT
```

Primary tools include:

```text
tools/build/sprite_asset_compiler.py
tools/build/sprite_sequence_compiler.py
tools/build/m09c_native_phase_pixel_sequence.py
```

Four retail player frames have pixel-exact compiler round-trip proof. M09B2 has deterministic multi-phase runtime proof. M09C has canonical native six-phase dispatch and 12/12 exact trampoline executions.

## Current production boundary

The remaining M09C gate is not format uncertainty; it is full-game visual containment/fallback validation of the six-phase native build.

Do not begin final Quaid integration until that gate is green.

After M09C closes, production renderer work should focus on:

- coherent original source frames;
- palette/index reproducibility;
- global chunk/working-set budgets;
- cache churn and namespace safety;
- sprite-per-line pressure;
- multi-group spill if required;
- runtime containment/fallback regression for each promoted animation family.

Palette/priority provenance and production audio remain separate unresolved subsystems; neither invalidates the proven sprite piece/cache path.
