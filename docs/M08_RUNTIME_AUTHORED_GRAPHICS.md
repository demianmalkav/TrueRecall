# M0.8 — Runtime-Validated Authored Avatar Graphics

M0.8 proves that independently modified sprite pixel data can be routed through the recovered True Lies renderer, dynamic VRAM cache and SAT path and appear on the player only during the new sprint state.

This closes the most important presentation-side uncertainty left by M0.7.

## ROM expansion

The laboratory build expands the canonical ROM from 2 MiB to **4 MiB** and updates the ROM-end header field accordingly.

The extended region holds:

- relocated direction/animation data at `0x200000`;
- sprint code at `0x207000` / `0x207080`;
- renderer/cache trampolines at `0x208000` / `0x208100`;
- authored raw sprite chunk bank at `0x210000`.

Expansion/no-op variants were runtime-tested before authored content was introduced.

## Retail renderer seam

Two retail renderer locations are used:

- cache-key path near `0x0113B4`;
- graphics-source lookup near `0x01143C`.

Immediately before the source lookup the retail code performs:

```text
MOVEA.L 0x2C(A6),A0
MOVE.L  0x02(A0,D1.W),D1
```

Therefore `A6` is the entity being rendered and `A0` is its active animation descriptor for that source resolution.

## Cache isolation

The actor renderer normally caches graphical chunks by `piece_word & 0x3FFF`. Simply changing the backing ROM source while retaining the same cache ID can return a previously cached retail chunk.

M0.8 avoids that ambiguity by assigning the sprint avatar an isolated cache namespace while Y is held:

```text
0x3F00 | chunk_index
```

Other sprites and the player outside the sprint state keep their retail cache IDs.

## Runtime avatar descriptor discovery

A differential sweep was performed over the small set of descriptors implicated by prior runtime initialization traces.

The tested scoped descriptors included:

- `0x0F0000`
- `0x0CA38C`
- `0x0F6FD4`

All builds used the same authored raw bank and the same deterministic `Left + Y` frame window.

Result:

- descriptor `0x0F0000` changes a compact ~32×32 region centered on the moving avatar throughout the Y-held interval;
- `0x0CA38C` produces no gameplay difference;
- `0x0F6FD4` modifies a separate small moving object elsewhere on screen;
- before Y (`frame 2098`) descriptor `0x0F0000` is pixel-identical to the reference gameplay frame;
- after Y is released (`frame 2144`) it again becomes pixel-identical.

This differential result identifies `0x0F0000` as the active avatar presentation descriptor for the tested gameplay path.

## Authored pixel payload

The proof build creates a 256-entry raw bank of 128-byte / 16×16 chunks. Valid donor chunks are copied structurally and a controlled pixel mutation is applied to the first bytes of each chunk.

This is deliberately diagnostic artwork, not final Total Recall art. Its purpose is to prove provenance:

```text
new ROM data
→ scoped renderer source override
→ isolated cache key
→ cache miss
→ DMA to VRAM
→ SAT sprite
→ visible changed avatar pixels
```

## Frame-level runtime proof — CONFIRMED

Against the correct M0.8 equivalence parent, the runtime-validated descriptor `0x0F0000` produced the following gameplay-region differences:

- frame 2098, before Y: **0 pixels**
- Y-active frames 2102–2140: **206–360 pixels** changed per sampled frame
- bounding boxes track the player and stay approximately within a 32×32 actor-sized region
- frame 2144, after Y release: **0 pixels**

The authored build therefore changes only the intended player presentation during the new state and cleanly falls back to retail presentation afterwards.

## Audited build

`tools/build/m08_runtime_authored_sprint_pixels.py`

```text
base SHA-1   d39174bed46ede85531b86df7ba49123ce2f8411
output SHA-1 a540621010aa529fc2371f6c7f433f6fa1cafbac
ROM size      4,194,304 bytes
checksum      0x934F
raw bank      0x210000
avatar desc   0x0F0000
```

The generated ROM and screenshots are not committed.

## What M0.8 proves

TrueRecall now has runtime proof for the complete player-extension presentation chain:

```text
new input/state
→ new code path
→ new animation selector/row
→ expanded ROM
→ independently addressable graphics bank
→ renderer/cache integration
→ authored sprite pixels visible on the player
→ exact fallback to retail when inactive
```

This is sufficient to begin replacing diagnostic content with actual Quaid animation assets while preserving the same regression methodology.

## Next production gate

The next step is no longer proving that new player pixels are possible. It is to build a proper source-asset compiler for Quaid frames, map them into dedicated chunk IDs/groups, measure VRAM-cache pressure, and validate a short coherent animation rather than diagnostic pixel mutations.
