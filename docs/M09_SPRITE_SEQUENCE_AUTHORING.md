# M0.9 — Sprite Sequence Authoring Pipeline

Status: **COMPILER + RUNTIME AUTHORING PROVEN / M09C NATIVE SIX-PHASE INTEGRATION ONE VISUAL GATE FROM COMPLETION**

For the exact live `NEXT`, defer to `docs/PROJECT_STATE.md`. This document describes the cumulative M0.9 pipeline and its current production boundary.

## Compiler — CONFIRMED

`tools/build/sprite_sequence_compiler.py` accepts indexed/RGBA source frames and emits:

- one shared raw 16×16 chunk bank;
- one mapping record per frame;
- global chunk deduplication across the sequence;
- manifest metadata for piece counts, chunk IDs, record sizes and per-frame working-set size.

Each chunk is the recovered retail unit:

```text
16×16 pixels
= 2×2 Genesis tiles
= 128 bytes
```

Palette index 0 remains transparent.

## Global deduplication — CONFIRMED

Chunk identity is shared across all frames rather than reset per frame. Production metrics include:

```text
global_unique_chunks
max_frame_working_set
```

The first measures ROM/resource cost; the second is a lower-bound indicator of dynamic VRAM-cache pressure.

## Retail round-trip probe — CONFIRMED

`tools/rom_probe/sprite_sequence_roundtrip_probe.py` reconstructs four real player frames from the retail archetype-191 descriptor path, recompiles them through the sequence compiler and requires pixel-exact reconstruction.

Observed proof:

```text
frames                    4
global unique chunks      6
chunk bytes               768
max per-frame working set 2
piece count per frame     2
```

Cross-frame reuse is real: two frames share the same chunk pair.

This compiler proof is independent from the later canonical F9F8 runtime-identity correction. Archetype-table descriptor identity and the live linked-player F9F8 descriptor are distinct facts.

## M09A native-sequence experiment — HISTORICAL / NOT PROMOTED

M09A replaced an active player descriptor wholesale with a synthetic four-frame descriptor. Although the resource sequence was structurally valid, runtime comparison developed gameplay/camera divergence.

Conclusion retained:

- descriptor substitution of the controlled player representation is not an acceptable integration architecture;
- linked F9F8/FB6E semantics must remain intact;
- a valid authored presentation path must preserve canonical runtime identity rather than merely feed structurally valid sprite data.

## M09B2 four-phase authored-pixel proof — CONFIRMED / DIAGNOSTIC

Builder:

```text
tools/build/m09b2_vblank_pixel_sequence.py
```

M09B2 keeps M07 sprint behavior and retail mapping geometry but swaps among four authored raw chunk banks while Y is held.

Diagnostic phase source:

```text
phase = (FFFFF712 >> 2) & 3
```

Banks:

```text
0x210000
0x218000
0x220000
0x228000
```

Cache namespaces:

```text
0x3C00 | chunk_index
0x3D00 | chunk_index
0x3E00 | chunk_index
0x3F00 | chunk_index
```

The corrected renderer trampoline preserves the retail sign branch around `0x01143C`:

```text
TST.L D1
BPL positive
JMP 0x011442
positive:
JMP 0x01145C
```

Deterministic regression against the correct M07C sprint parent shows:

- frame 2098 before Y: 0 gameplay-region pixel differences;
- sampled active frames 2102..2140: non-zero avatar-local differences;
- maximum active bounding box: 30×17 px;
- frame 2144 after Y release: 0 gameplay-region pixel differences.

Evidence:

```text
extracted_metadata/m09b2_runtime_regression.json
```

M09B2 proves multi-phase authored presentation and cache isolation, but **not** actor-native sequencing because `F712` supplies timing.

## M09C canonical runtime correction — CONFIRMED

M09C canonical tracing corrected two earlier assumptions.

### Player globals are word pointers

Retail loads F9F8 and FB6E via `MOVEA.W`. Observed values:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

They are not 32-bit pointers reconstructed from adjacent words.

### Canonical F9F8 identity

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

The descriptor remains stable during the observed native cycle.

M0.8 `0x0F0000` remains a valid player-local visual-component renderer/cache proof, but the claim that it is the canonical F9F8 world/render-avatar descriptor is **FALSIFIED**.

## Native phase bridge — CONFIRMED

The linked-object bridge at `0x009D5E` transfers phase from proxy to F9F8 avatar:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Writer transaction:

```text
0x009D72  +0x1E
0x009D7E  +0x24
0x009D88  +0x20
```

The `+0x24` write inside this cluster is native progression, not automatically external reselection.

Evidence:

```text
extracted_metadata/m09c_canonical_phase_bridge.json
```

## Native six-position sprint cycle — CONFIRMED

Base phase:

```text
F9F8 +0x1C = 0x08B6
```

Current phase cycle:

```text
0x08B6 -> 0x08B8 -> 0x08BA -> 0x08BC -> 0x08BE -> 0x08C0 -> wrap
```

Raw deltas:

```text
0, 2, 4, 6, 8, 10
```

Mapping records:

```text
0x2C08 0x2C24 0x2C44 0x2C64 0x2C80 0x2CA0
```

No descriptor write occurs in the observed cycle.

## M09C six-bank native-phase build — IMPLEMENTED

Authoritative builder:

```text
tools/build/m09c_native_phase_pixel_sequence.py
```

It replaces M09B2's VBlank phase source with:

```text
raw_delta = (object+0x1E) - (object+0x1C)
```

and scopes the authored substitution to:

```text
object+0x2C == 0x000A0000
```

Resource mapping:

```text
phase 0 -> bank 0x210000 / cache namespace 0x3A00
phase 1 -> bank 0x218000 / cache namespace 0x3B00
phase 2 -> bank 0x220000 / cache namespace 0x3C00
phase 3 -> bank 0x228000 / cache namespace 0x3D00
phase 4 -> bank 0x230000 / cache namespace 0x3E00
phase 5 -> bank 0x238000 / cache namespace 0x3F00
```

Audited proof build:

```text
size:     4,194,304
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
```

Twelve exact trampoline executions pass under the pinned BlastEm 68000 core: six render-source dispatches and six cache-key dispatches.

Evidence:

```text
extracted_metadata/m09c_native_phase_trampoline_runtime.json
```

VERIFY also caught an invalid zero-displacement short `BRA`; the assembler now rejects that case and CI protects the fix.

## Current production boundary

The structural compiler and native six-phase runtime dispatch are strong enough to define the production architecture, but **final Quaid artwork must not be integrated yet**.

The remaining M09C gate is full-game visual containment/fallback regression against the correct M07 sprint parent:

1. exact pre-Y convergence;
2. player-local held-Y differences;
3. one-to-one visual correlation with F9F8 deltas `0,2,4,6,8,10` rather than `F712`;
4. no cache contamination of unrelated actors;
5. exact post-Y convergence;
6. unchanged M07 movement/control behavior;
7. preserved F9F8/FB6E link semantics;
8. F9F8 descriptor remains `0x000A0000`.

Only after this gate is green should diagnostic chunks be replaced with compiler-produced production Quaid frames.

## Production work after M09C closes

- author a coherent original Quaid cycle rather than proof glyphs/pixel mutations;
- retain source-art -> palette/index conversion -> 16×16 decomposition -> deduplicated chunks -> mapping/resource build reproducibility;
- track global unique chunks, frame working set, incoming churn, cache pressure, sprite-per-line overlap and ROM bytes;
- support controlled multi-group spill if a production sequence exceeds the current group budget;
- validate all required directions/weapon families incrementally against the same containment/fallback invariants.

## Status summary

```text
compiler / retail round-trip        CONFIRMED
M09B2 authored multi-phase runtime  CONFIRMED diagnostic path
canonical F9F8 identity             CONFIRMED
native six-phase bridge             CONFIRMED
six-bank dispatch trampolines       CONFIRMED 12/12
full-game six-phase visual gate     OPEN
production Quaid frames             BLOCKED ON VISUAL GATE
```
