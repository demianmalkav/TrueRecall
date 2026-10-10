# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. Closed gates reopen only on contradictory evidence.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M1.1B — gameplay tile-graphics authoring and runtime proof
checkpoint: 9db2910e30007ad49ab58b27785055e7753c3f8a
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE and FROZEN.**

**M1.0A/B is COMPLETE.** Frozen Quaid, persistent object authoring and world collision coexist in one reproducible scene0 gameplay baseline and are runtime-confirmed.

**M1.1A is COMPLETE.** Palette authoring is now canonical, source-level, transactional and runtime-confirmed at actual VDP CRAM while preserving every closed M1.0 behavior invariant.

The active task is M1.1B: recover and author gameplay tile graphics for scene0 without reopening the frozen player, object, collision or palette gates.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed. Generated builds remain reproducible from source/manifests plus this verified base.

## Closed engine/integration foundation

Stable unless contradictory runtime evidence appears:

- M0.1–M0.6 ROM/entity/VM/map/authoring reconstruction;
- M0.7 deterministic held-Y sprint;
- M0.8 runtime-authored player-local graphics;
- M0.9C native six-phase player presentation;
- M0.9D frozen production Quaid sprint family;
- M0.10 world-collision authoring;
- M0.11A–D canonical scene-source authoring;
- M1.0A/B player + object + collision scene0 integration;
- M1.1A palette + scene-source-v2 transaction/runtime proof.

## M0.9D production player — CLOSED / FROZEN

```text
source fingerprint: da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA-1:       49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum:          0x266C
F9F8 descriptor:   0x000A0000
native phases:     0,2,4,6,8,10
```

Do not edit v11 player pixels or mapping geometry during M1.1B.

## M1.0 scene0 gameplay baseline — CLOSED / CONFIRMED

Source manifest:

`tools/build/examples/m100a_scene0_baseline.json`

Authored resources:

```text
shotgun pickup: type 69, stride 6, x=690, y=558
world wall:     type 9, rect=[668,540,676,580]
```

Integrated M1.0A candidate:

```text
SHA-1:    84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027
checksum: 0x6E6A
direct parent: 49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
```

M1.0B runtime proves the pickup grants shotgun + five shells only in the candidate, the type-9 wall blocks the candidate while the direct parent crosses the zone, F9F8 remains `FFC632` with descriptor `0x000A0000`, and all 14 behavioral/control assertions pass.

Evidence:

- `extracted_metadata/m100a_vertical_slice_baseline.json`
- `extracted_metadata/m100b_vertical_slice_runtime.json`

## M1.1A canonical palette/source-v2 — COMPLETE / CONFIRMED

Minimal preserved M11F/G/H functionality was deliberately ported instead of merging historical branches:

```text
tools/build/scene_palette.py
tools/build/scene_source_v2.py
tools/build/scene_compiler_v2.py
```

`scene_source.v1` remains unchanged as a regression anchor. `scene_source.v2` moves palette identity out of immutable metadata and exposes explicit `colors[64]`. `scene_compiler_v2` runs the existing scene transaction first, allocates palette data after the highest allocation, checks non-overlap and repairs the final checksum once.

### Canonical palette matrix

Against canonical SHA-1 `d39174...f8411`:

- 19/19 gameplay scenes export valid 64-word Genesis CRAM palettes;
- 19/19 palette no-op compiles return byte-exact canonical ROM bytes;
- invalid CRAM words are rejected;
- source-v2 exact no-op is confirmed across all 19 scenes.

Evidence: `extracted_metadata/m11f_scene_palette_canonical.json`.

### Canonical v2 transaction

The canonical transaction probe combines a map-word edit and palette relocation through one allocation ledger with no overlap and exact reparse/checksum validation.

Evidence: `extracted_metadata/m11h_scene_source_v2_transaction_canonical.json`.

### Scene0 integrated palette baseline

Builder: `tools/build/m110a_palette_vertical_slice.py`.

The closed scene0 pickup/wall baseline is rebuilt through `scene_source.v2` and receives one environment-palette proof edit outside the frozen player line:

```text
palette index:     8
retail word:       0x0464
authored word:     0x0648
player line:       indices 32..47, untouched
palette allocation:0x303080
scene-v2 parent:   427b842188b29e4fa040802c94b7d60fe44976cc / 0xA30C
integrated SHA-1:  270e1d633db7883c9170bb1e4eb367abdf97a2bd
checksum:          0x6B9E
```

The single scene ledger contains object descriptor/LZ, world resource and palette allocations with no overlap. All six frozen v11 phase banks remain byte-exact. Player and scene deltas have no incompatible overlap.

Evidence: `extracted_metadata/m110a_palette_vertical_slice.json`.

### Actual VDP CRAM runtime proof

Runner: `tools/runtime/m110b_palette_runtime.py`.

The pinned BlastEm native savestate format was parsed structurally. In the pinned core, VDP section id `3`, state version `5`, serializes 64 KiB VRAM followed by the 64-word `context->cram` array. Parent and M1.1A candidate were run through the same scene0 sequence and quicksaved at the same deterministic stage.

Result:

```text
CRAM words compared: 64
difference count:    1
CRAM[8], parent:     0x0464
CRAM[8], candidate:  0x0648
CRAM[32..47]:        byte/word exact parent == candidate
M1.0B assertions:    14/14 PASS
```

This is actual VDP CRAM evidence, not merely ROM or RAM-shadow inspection.

Evidence: `extracted_metadata/m110b_palette_runtime.json`.

### M1.1A CI checkpoint

```text
commit:          9db2910e30007ad49ab58b27785055e7753c3f8a
Actions run:     38068084778
artifact id:     11675387267
artifact SHA256: 2cc4c0c2394f03745e5d362c95e9ce56e475d0fbabc72ee99a765e16c36c6ba6
static:          PASS
BlastEm harness: PASS
```

The exact artifact-published `m110b` runner was then executed locally against the verified canonical-derived parent/candidate and produced the persisted CRAM/runtime evidence above.

## OPEN

### O1 — recover gameplay plane graphics-resource format at authoring fidelity

M11D currently carries each plane's `graphics_descriptor` as immutable identity while tile words are authorable. M1.1B must determine the exact graphics-resource ownership/encoding used by scene0 C000/E000 and establish a deterministic extract/rebuild boundary. Existing asset knowledge may be reused, but no graphics descriptor semantics may be guessed.

### O2 — exact no-op graphics round-trip

For the selected scene0 graphics resource, decode/export/recompile must reproduce the original resource exactly or produce a mechanically equivalent relocated representation with exact decoded bytes. The allocator must coexist with the M1.1A object/world/palette ledger.

### O3 — one authored environment tile/chunk

Replace or add one deliberately obvious environment graphics unit while preserving tile-map indices, palette contract and frozen player graphics. The build must remain deterministic and collision-free.

### O4 — runtime graphics proof

Boot the integrated candidate under pinned BlastEm and prove the authored environment pixels reach VRAM/presentation while all M110B CRAM assertions and all 14 M100B gameplay assertions remain green.

## NEXT

1. Audit scene0 C000/E000 `graphics_descriptor` structures and trace their load/decompression path from ROM to VRAM.
2. Cross-check existing asset/graphics-format documentation and probes before introducing a new decoder.
3. Identify the smallest scene0 environment graphics resource that can be independently extracted and rebuilt.
4. Implement an exact no-op graphics probe/round-trip with machine-checkable fingerprints.
5. Only after the no-op gate is green, add one authored environment tile/chunk through the transaction allocator.
6. Integrate with M110A, then runtime-confirm VRAM/presentation and rerun M110B + M100B invariants.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1A gates reopen only on contradictory evidence.
- Do not modify v11 player pixels during M1.1B.
- Keep `scene_source.v1` unchanged; evolve source schemas only when the graphics model is actually recovered.
- Do not infer graphics descriptor semantics from visual appearance alone.
- Generated ROMs/PNGs are outputs; source code + manifests + verified canonical ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D frozen; M1.0A/B complete; M1.1A palette/source-v2 canonical + actual VDP CRAM runtime proof complete.
EVIDENCE m11f_scene_palette_canonical.json + m11h_scene_source_v2_transaction_canonical.json + m110a_palette_vertical_slice.json + m110b_palette_runtime.json + Actions run 38068084778.
OPEN     M1.1B gameplay tile-graphics authoring and runtime proof.
NEXT     recover scene0 gameplay graphics descriptors/load path, establish exact no-op graphics round-trip, then author one environment tile/chunk and runtime-regress against M110B/M100B.
```
