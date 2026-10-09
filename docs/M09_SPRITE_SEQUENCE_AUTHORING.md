# M0.9 — Sprite Sequence Authoring Pipeline

M0.9 begins the production-facing player-art pipeline that follows the M0.8 runtime proof. It does **not** claim that final Quaid artwork exists yet. It proves that multiple source frames can be compiled into one deduplicated True Lies sprite resource set and reconstructed without pixel loss.

## Compiler

`tools/build/sprite_sequence_compiler.py` accepts a sequence of indexed/RGBA source frames and emits:

- one shared raw 16×16 chunk bank;
- one mapping record per frame;
- global chunk deduplication across the sequence;
- a manifest containing piece counts, chunk IDs, record sizes and per-frame working-set size.

Each chunk remains the recovered retail unit:

```text
16×16 pixels
= 2×2 Genesis tiles
= 128 bytes
```

The compiler currently targets one resource group per sequence and preserves palette index 0 as transparent.

## Global deduplication

Unlike the earlier single-frame compiler, chunk identity is shared across all frames in the sequence. Reused body/limb pieces therefore retain one chunk ID instead of being duplicated per animation frame.

This gives us an explicit production metric:

```text
global_unique_chunks
max_frame_working_set
```

The first is ROM/resource cost; the second is a lower-bound indicator of dynamic VRAM-cache pressure for the sequence.

## Retail round-trip probe — CONFIRMED

`tools/rom_probe/sprite_sequence_roundtrip_probe.py` reconstructs four real player frames from archetype 191, selectors:

```text
2, 258, 260, 262
```

It recompiles them through the sequence compiler with newly assigned shared chunk indices, renders those generated mapping records/chunks back to indexed pixels and requires exact equality against the reconstructed retail frames.

Observed proof result:

```text
frames                   4
global unique chunks     6
chunk bytes              768
max per-frame working set 2
piece count per frame    2
```

Two of the four frames reuse the same pair of chunks, proving that cross-frame deduplication is active rather than merely concatenating per-frame outputs.

The rendered output is pixel-identical for all four frames.

## What this proves

The player-art path now supports:

```text
source animation frames
→ 16×16 decomposition
→ transparent-cell pruning
→ global chunk deduplication
→ stable chunk IDs
→ mapping records per frame
→ resource/cost manifest
→ pixel-exact reconstruction
```

This is the correct foundation for actual Quaid animation production.

## Remaining work before final Quaid animation

1. Add explicit sequence timing / frame-order metadata and compile animation-selector rows, not only mapping records.
2. Support controlled multi-group spill when an animation set exceeds 256 unique chunks.
3. Add sprite-per-line and VRAM/cache-pressure analysis, not only total chunk counts.
4. Integrate compiled sequence output into the M0.8 expanded-ROM renderer path and runtime-test a coherent multi-frame authored animation.
5. Replace diagnostic or retail-derived proof frames with original Total Recall source art.

M0.9 should be considered **pipeline demonstrated / integration in progress**, not a completed art milestone.
