# M0.9 — Sprite Sequence Authoring Pipeline

M0.9 begins the production-facing player-art pipeline that follows the M0.8 runtime proof. It does **not** claim that final Quaid artwork exists yet. It proves that multiple source frames can be compiled into one deduplicated True Lies sprite resource set and reconstructed without pixel loss, and now includes a runtime-stable four-phase authored-pixel sequence proof.

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
frames                    4
global unique chunks      6
chunk bytes               768
max per-frame working set 2
piece count per frame     2
```

Two of the four frames reuse the same pair of chunks, proving that cross-frame deduplication is active rather than merely concatenating per-frame outputs.

The rendered output is pixel-identical for all four frames.

## M09A native-sequence experiment — NOT PROMOTED

An initial runtime experiment attempted to replace the active player-control descriptor with a fully synthetic four-frame descriptor and let the retail `FDDC` animation updater advance it.

The sequence itself was structurally valid, but runtime comparison showed gameplay/camera divergence after the sequence had been active for several frames. Because the player is represented by linked avatar/proxy objects and the control path depends on retail descriptor/geometry semantics, replacing the active control descriptor is not considered safe.

M09A therefore remains an investigative experiment and is **not** a milestone proof.

## M09B2 four-phase authored-pixel runtime proof — CONFIRMED

M09B2 deliberately isolates pixels from animation geometry/state. It keeps the M0.7 sprint behavior and retail mapping/geometry, but selects one of four original authored 16×16 chunk banks while Y is held.

Build tool:

`tools/build/m09b2_vblank_pixel_sequence.py`

The phase is selected from the VBlank counter:

```text
phase = (FFFFF712 >> 2) & 3
```

Each phase lasts four frames. Four separate cache-key namespaces are used:

```text
0x3C00 | chunk_index
0x3D00 | chunk_index
0x3E00 | chunk_index
0x3F00 | chunk_index
```

This prevents the dynamic VRAM cache from reusing a previous phase's bytes under the same key.

The build expands the ROM to 4 MiB and stores the four raw authored banks at:

```text
0x210000
0x218000
0x220000
0x228000
```

### Corrected renderer trampoline

The first M09B laboratory build reconstructed the branch at `0x01143C` backwards. The retail control flow is:

```text
MOVE.L source,D1
BPL     0x01145C
; negative source falls through to 0x011442
```

M09B2 restores those exact semantics after its scoped source override:

```text
TST.L D1
BPL positive
JMP 0x011442
positive:
JMP 0x01145C
```

This correction was required for a valid baseline comparison.

### Deterministic runtime regression

The candidate is compared against its correct logical parent, M07C sprint, under the same deterministic BlastEm framescript.

Regression tool:

`tools/runtime/m09b2_runtime_regression.py`

Persisted measurements:

`extracted_metadata/m09b2_runtime_regression.json`

Key results:

- frame `2098`, before Y: **0 gameplay-region pixels differ** from M07C;
- every sampled active frame `2102..2140`: non-zero authored-pixel difference confined to an avatar-sized box;
- maximum active difference bounding box: **30×17 px**;
- frame `2144`, after Y is released: **0 gameplay-region pixels differ** from M07C.

The sampled active boxes track the moving player rather than the map/camera. Therefore the four-phase authored resource path does not introduce scene/camera divergence in this test.

Small differences may appear in bottom non-gameplay/HUD raster rows; gameplay assertions deliberately compare the 224-line gameplay region.

### What M09B2 proves

M09B2 proves a stable runtime chain:

```text
new player mechanic (M07 sprint)
→ trigger-scoped authored pixel source
→ four distinct runtime phases
→ separate cache namespaces
→ renderer/cache/VRAM path
→ avatar-local visible change
→ exact gameplay convergence when trigger is released
```

It is stronger than M0.8's single authored-pixel source because the source changes across time while gameplay remains stable.

It is **not yet the final engine-native sequence authoring solution**: timing is driven by the VBlank counter and retail mapping geometry is retained. The next target is to let retail animation sequencing (`FDDC`/mapping records) advance authored frames while preserving the correct player descriptor/geometry and dual-object semantics.

## What the current M0.9 pipeline proves

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
→ multi-phase authored pixels visible in runtime
```

This is sufficient to begin production-quality Quaid frame generation while the final native sequence-integration seam is still being cleaned up.

## Remaining work before final Quaid animation

1. Build M09C: preserve the active retail player descriptor/geometry semantics while integrating authored records through the native `FDDC` sequence path.
2. Do not replace the player proxy/control descriptor wholesale; identify or extend the correct animation row/mapping seam.
3. Support controlled multi-group spill when an animation set exceeds 256 unique chunks.
4. Continue enforcing sprite-per-line and VRAM/cache-pressure budgets.
5. Replace diagnostic proof glyphs with original Total Recall Quaid source art and validate all eight directions.

M0.9 should now be considered **compiler + runtime multi-phase authored-pixel path demonstrated / native sequence integration in progress**.