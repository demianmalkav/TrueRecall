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
milestone:  M1.1C — canonical scene-source-v3 graphics transaction
checkpoint: 79c1e485441f92b536baa00d5401caa5c24076f8
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE and FROZEN.**

**M1.0A/B is COMPLETE.** Frozen Quaid, persistent object authoring and world collision coexist in one reproducible scene0 gameplay baseline and are runtime-confirmed.

**M1.1A is COMPLETE.** Palette authoring is canonical, source-level, transactional and runtime-confirmed at actual VDP CRAM.

**M1.1B is COMPLETE.** Scene0 primary environment graphics can be exported, exactly round-tripped, relocated, authored at tile granularity, integrated with M110A and runtime-confirmed at actual VDP VRAM/presentation without reopening player, gameplay or palette gates.

The active task is M1.1C: migrate the now-confirmed primary-graphics model into a new versioned canonical scene source/transaction so map + objects + world collision + palette + primary environment graphics are authored through one source-level transaction instead of a post-build composition step.

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
- M1.1A palette + scene-source-v2 transaction/runtime proof;
- M1.1B primary gameplay graphics authoring + actual VRAM/presentation proof.

## M0.9D production player — CLOSED / FROZEN

```text
source fingerprint: da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA-1:       49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum:          0x266C
F9F8 descriptor:   0x000A0000
native phases:     0,2,4,6,8,10
```

Do not edit v11 player pixels or mapping geometry during M1.1C.

## M1.0 scene0 gameplay baseline — CLOSED / CONFIRMED

Source manifest: `tools/build/examples/m100a_scene0_baseline.json`.

Authored resources:

```text
shotgun pickup: type 69, stride 6, x=690, y=558
world wall:     type 9, rect=[668,540,676,580]
```

Integrated candidate:

```text
SHA-1:    84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027
checksum: 0x6E6A
direct parent: 49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
```

M1.0B proves the pickup grants shotgun + five shells only in the candidate, the type-9 wall blocks the candidate while the direct parent crosses the zone, canonical player/proxy semantics remain stable and all 14 behavioral/control assertions pass.

Evidence:

- `extracted_metadata/m100a_vertical_slice_baseline.json`
- `extracted_metadata/m100b_vertical_slice_runtime.json`

## M1.1A canonical palette/source-v2 — COMPLETE / CONFIRMED

Canonical source/tooling:

```text
tools/build/scene_palette.py
tools/build/scene_source_v2.py
tools/build/scene_compiler_v2.py
tools/build/m110a_palette_vertical_slice.py
tools/runtime/m110b_palette_runtime.py
```

`scene_source.v1` remains unchanged as a regression anchor. `scene_source.v2` exposes explicit `colors[64]`; `scene_compiler_v2` places palette data after the scene allocation ledger and repairs final checksum once.

Canonical matrix:

- 19/19 gameplay scenes export valid 64-word Genesis CRAM palettes;
- 19/19 palette no-op compiles are byte-exact;
- invalid CRAM words are rejected;
- source-v2 exact no-op is confirmed across all 19 scenes.

Scene0 palette proof:

```text
palette index:      8
retail word:        0x0464
authored word:      0x0648
player line:        indices 32..47, untouched
palette allocation: 0x303080
M110A SHA-1:        270e1d633db7883c9170bb1e4eb367abdf97a2bd
checksum:           0x6B9E
```

Actual VDP CRAM proof confirms exactly one changed CRAM word at index 8; player line 32..47 remains exact; M100B remains 14/14 PASS.

Evidence:

- `extracted_metadata/m11f_scene_palette_canonical.json`
- `extracted_metadata/m11h_scene_source_v2_transaction_canonical.json`
- `extracted_metadata/m110a_palette_vertical_slice.json`
- `extracted_metadata/m110b_palette_runtime.json`

CI checkpoint:

```text
commit:          9db2910e30007ad49ab58b27785055e7753c3f8a
Actions run:     38068084778
artifact id:     11675387267
artifact SHA256: 2cc4c0c2394f03745e5d362c95e9ce56e475d0fbabc72ee99a765e16c36c6ba6
static:          PASS
BlastEm harness: PASS
```

## M1.1B gameplay graphics — COMPLETE / CONFIRMED

Durable subsystem document: `docs/M111_GAMEPLAY_GRAPHICS_AUTHORING.md`.

### Scene0 primary resource

The non-zero primary gameplay graphics descriptor is authorable as a three-long structure while unresolved secondary/auxiliary identity is preserved:

```text
retail descriptor:    0x00FFAA
primary LZBeam:       0x014898
secondary pointer:    0x800178DA
auxiliary pointer:    0x01BF7A
secondary-plane desc: 0x00000000
```

Decoded primary resource:

```text
24,960 bytes
780 tiles × 32 bytes
SHA256 0f73aff41d28f9cae5b17368f78979f720474ce342c85e53f9a46174e3bbb171
```

Exact raw no-op is confirmed. Forced relocation to `0x304000/0x304010` reparses to identical decoded bytes.

Evidence: `extracted_metadata/m111b_scene_graphics_primary.json`.

### One authored environment tile

M111C changes only tile index `2`, replacing its retail 32-byte payload with an 8×8 X diagnostic pattern using palette index `0xE`.

```text
retail tile2 SHA256: e0e77a507412b120f6ede61f62295b1a7b2ff19d3dcc8f7253e51663470c888e
graphics-only SHA-1: a26f74937233e155e025bcd45a220660c75e110f
integrated SHA-1:    b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0
checksum:             0xFAD7
```

Combined allocation ledger:

```text
0x300000 object_desc                    132
0x300090 object_lz                     1217
0x300600 world_resource               10880
0x303080 scene_palette                  128
0x304000 primary_graphics_descriptor     12
0x304010 primary_graphics_lz          12105
```

No overlaps occur; all six frozen Quaid phase banks and M110A palette bytes remain exact.

Evidence: `extracted_metadata/m111c_graphics_vertical_slice.json`.

### Actual VDP VRAM + presentation proof

Correct logical comparison: M110A vs M1.1B candidate under the same deterministic scene0 sequence.

```text
VRAM changed range: [0x0040,0x0060)
changed bytes:      32
candidate VRAM tile: exact authored tile2 bytes
CRAM M110A→M1.1B:  exact / no differences
```

BlastEm internal screenshot comparison:

```text
size:            256×240
changed pixels:  1440
bbox:            [15,9,199,45]
```

The visual delta is confined to the upper environment region containing the repeated E000 tile.

Evidence: `extracted_metadata/m111d_graphics_runtime.json`.

### Closed-gate regression

Against frozen M09D:

- M100B behavioral/control assertions: **14/14 PASS**;
- M110B CRAM contract remains exact: only index 8 differs `0x0464 → 0x0648`;
- player palette line 32..47 remains exact.

Evidence: `extracted_metadata/m111e_graphics_regression.json`.

### M1.1B CI/reproduction checkpoint

```text
source commit:    79c1e485441f92b536baa00d5401caa5c24076f8
Actions run:      38073075203
artifact id:      11677736118
artifact SHA256:  be0b0a2cdc1016f33cb9828b7c970fc50f9898d7dea3e79d77564b38ff862c58
static:           PASS
BlastEm harness:  PASS
```

The exact CI artifact rebuilt the pinned M111C candidate byte-for-byte and its artifact-published M111D/M111E runners reproduced all runtime evidence above.

## OPEN — M1.1C

### O1 — source schema v3

Add the confirmed primary gameplay graphics identity/payload to a new versioned scene source. Keep `scene_source.v1` and v2 unchanged as regression anchors. Preserve secondary and auxiliary graphics pointers as immutable identity; do not guess their semantics.

### O2 — unified transaction allocator

Extend the scene transaction so map/object/world/palette/primary-graphics allocations are owned by one ledger and one final checksum repair, rather than composing an independently generated graphics ROM after M110A.

### O3 — exact no-op migration gate

Prove v2→v3 upgrade/downgrade losslessness where applicable and exact/no-op behavior for scenes with primary graphics resources. Pin decoded graphics/resource fingerprints mechanically.

### O4 — reproduce the closed scene0 graphics proof through v3

Rebuild the same tile-2 environment edit through the unified v3 source. The output should either reproduce the pinned M111C bytes exactly or be mechanically equivalent with exact decoded resources and the same runtime behavior.

### O5 — runtime regression

Run the v3-generated candidate through M111D and M111E. Promotion requires exact VRAM/presentation semantics plus M110B and M100B gates remaining green.

## NEXT

1. Define `scene_source.v3` by extending v2 with the confirmed primary-graphics source; leave v1/v2 untouched.
2. Implement v2↔v3 migration helpers and strict graphics identity validation.
3. Extend the transactional compiler so primary graphics allocate after existing scene/palette allocations in the same ledger.
4. Establish exact no-op/migration probes before any new graphics edit.
5. Rebuild the already-confirmed scene0 tile-2 proof through v3.
6. Runtime-verify the v3 candidate with M111D + M111E; only then freeze M1.1C.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1A/M1.1B gates reopen only on contradictory evidence.
- Do not modify v11 player pixels or mapping geometry during M1.1C.
- Keep `scene_source.v1` and v2 immutable; v3 is additive/versioned.
- Primary graphics semantics confirmed by M1.1B may be used; secondary/auxiliary semantics may not be guessed.
- Generated ROMs/PNGs are outputs; source code + manifests + verified canonical ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D frozen; M1.0A/B complete; M1.1A palette/source-v2 complete; M1.1B primary gameplay graphics authoring + actual VRAM/presentation proof complete.
EVIDENCE m111b_scene_graphics_primary.json + m111c_graphics_vertical_slice.json + m111d_graphics_runtime.json + m111e_graphics_regression.json + Actions run 38073075203.
OPEN     M1.1C canonical scene-source-v3 graphics transaction.
NEXT     migrate confirmed primary graphics into an additive v3 scene source/transaction, prove no-op, reproduce the tile-2 proof, then rerun M111D/M111E.
```
