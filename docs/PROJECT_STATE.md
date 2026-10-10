# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. The checkpoint below is the material proof checkpoint; later documentation-only commits may advance HEAD.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M0.9D — production Quaid source-frame authoring and budget validation
checkpoint: 4bb9d49d1dccb0ec4315465d3ce2050ec21c7ea2
```

**M0.9C is COMPLETE.**

**M0.9D is technically proven end-to-end and now has a validated v10 production candidate, but is not frozen as final production art.** All native-seam, mapping, palette, budget, deterministic-build and runtime-containment gates are green. The only remaining gate is micro-detail/art-quality refinement against the retail player-art quality baseline. Do not reopen the M09C native animation seam or expand mapping geometry merely to continue art iteration.

The first Total Recall production vertical slice has not begun.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed. ROM availability is session-local; verify size + SHA-1 before ROM-dependent work.

## Stable engine foundation

M0.1–M0.6 reconstruction/authoring, M0.7 deterministic held-Y sprint, M0.8 runtime-authored player-local graphics, M0.10 world-collision authoring and M0.11A–D canonical scene-source authoring remain stable foundation. Parallel M11E–H branches are preserved but are not the active track.

## M0.9C canonical runtime model — CLOSED / CONFIRMED

Retail loads `FFFFF9F8` and `FFFFFB6E` with `MOVEA.W`; each global stores a signed 16-bit RAM pointer.

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
native bridge = 0x009D5E
raw phase deltas = 0,2,4,6,8,10
```

The `0x0F0000 == F9F8 descriptor` model, adjacent-word 32-bit pointer reconstruction and “every +0x24 write is external reselection” model are FALSIFIED.

Primary evidence:

- `extracted_metadata/m09c_canonical_phase_bridge.json`
- `extracted_metadata/m09c_native_phase_trampoline_runtime.json`
- `extracted_metadata/m09c_native_visual_regression.json`

M09C proof build:

```text
size:     4,194,304 bytes
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
banks:    0x210000,0x218000,0x220000,0x228000,0x230000,0x238000
cache:    0x3A00..0x3F00
```

The final M09C runtime comparison against M07C proved exact pre/post fallback, zero control/RAM mismatches, canonical descriptor preservation, all six native phases and player-local active differences.

## M0.9D production sprite contract — CLOSED / CONFIRMED

Machine-readable contract: `extracted_metadata/m09d_quaid_sprint_contract.json`.

```text
descriptor:             0x000A0000
native phases:          6
runtime facings:        8
authored facings:       N, NE, E, SE, S
native H-flip reuse:    SW<-SE, W<-E, NW<-NE
unique mapping records: 10
resource group:         7
reserved chunk slots:   0x68..0x7F (24 slots)
reserved bytes/phase:   3,072
six-phase reservation:  18,432 bytes
max pieces/frame:       4
max retail clip:        48x64
transparent index:      0
palette indices:        0..15
```

The first production family preserves retail mapping geometry and the 24 proven group-7 slot identities. No mapping-geometry expansion is currently justified.

## Runtime player palette — CONFIRMED

`extracted_metadata/m09d_player_palette_runtime.json` confirms that the tested F9F8 sprint path uses player palette line 2 at priority 0 through all sampled native phases. The first Quaid family therefore authors directly to the proven 0..15 indexed palette; no palette reauthoring is required for this gate.

## M0.9D mapping-constrained compiler — CLOSED / CONFIRMED

`tools/build/m09d_mapping_constrained_sprite_compiler.py` reuses the recovered Genesis chunk encoder and supports the non-grid retail piece offsets required by the ten canonical records.

Current v10 contract use:

```text
source frames:              30
used chunk slots/phase:     17
reserved chunk slots/phase: 24
max pieces/frame:           4
palette range:              <= 15
```

All mapping-geometry, chunk-slot, transparency, palette, phase-budget and native-mirroring assertions remain green.

## Quaid source family v10 — ACTIVE PRODUCTION CANDIDATE / NOT YET FROZEN

Source of truth: `tools/build/m09d_quaid_sprint_source.py`.

Evidence: `extracted_metadata/m09d_quaid_v10_candidate.json`.

v10 replaces v9 as the active candidate. It preserves the facing-correct head treatment introduced in v9 and makes the following art-only changes inside the same contract:

- broader shoulder line with a tapered waist rather than a rectangular armor-panel read;
- cloth-fold shirt shading with restrained highlights;
- thicker upper arms with tapered forearms;
- heavier thighs/boots and a wider sprint stance;
- stronger overall Quaid physical weight while retaining all five authored/eight runtime facings.

Deterministic indexed-pixel source fingerprint:

`16df51a3063eaec999b88ad7d35dd8ba7d4fdb04`

Per-phase bank SHA-1:

```text
713264ed4ad4f14cc0bd0ea7bf7a498660bd77c7
5270f74e4550626ea36275d11da57cbf70512fc0
3fad55d7310d46347c10b1bcf6b62d48d4bbbcb0
a1f88979ba18ef4957ab8efedf253339b5de489b
e31bafa3d922343a8b29f0bf406d22d8c0f7b4da
ed27b3d7630ae71b8e9dc518a36f1647630edfdb
```

## Deterministic M0.9D v10 integration build — CONFIRMED

Builder: `tools/build/m09d_quaid_sprint_build.py`.

Policy remains unchanged: rebuild canonical M09C, replace only the six 0x8000-byte phase banks, recompute the Genesis checksum, preserve descriptor/trampolines/mapping/control.

```text
size:     4,194,304 bytes
SHA-1:    a7ee31cb12e17965696fbd4591ddc6b5e96d5d87
checksum: 0xD3EF
parent:   3256f9dcbc6376624716e3508f41c0439e17cef6
```

## M0.9D v10 runtime regression — CONFIRMED

v10 was compared against the correct M07C sprint parent from the common native pre-Y state.

```text
M07C parent SHA-1: 55e02728cb0b7f3627f410202c889197c0e3d0d2
common state SHA-256: 72f3caa0f49d8d1548f897df67078994381efb5db37cd0a4ee4372ac76b35a8f
active samples: 42
first visible step: 3
state mismatches: 0
observed deltas: 0,2,4,6,8,10
max gameplay difference bbox: 65x64 host pixels
```

All ten runtime assertions pass: exact pre-trigger and post-release fallback, Y+Left normalized input throughout the active window, exact parent/candidate compared state, canonical descriptor preservation, all six native phases, bounded activation latency, continuous authored presentation after warmup, visible evidence for every phase and actor-local visual containment.

## Retail visual-quality comparison — NEW EVIDENCE

The canonical retail group-7 player frames were decoded from descriptor `0x000A0000` and used only as a visual-quality baseline. v10 now has comparable occupancy/silhouette density, but retail Tasker still uses finer micro-contrast to separate neck, sleeves/hands, torso folds, legs/boots and weapon/anatomical detail.

This is **not** evidence that the mapping contract is insufficient. It narrows the remaining work to pixel-level art refinement inside the existing contract.

## CI state

Actions run `38018819486` at commit `4bb9d49d1dccb0ec4315465d3ce2050ec21c7ea2`:

```text
58 tests / 0 failures / 0 errors
static: PASS
BlastEm harness: PASS
```

The first v10 source commit intentionally failed only the two v9 fingerprint pins; after updating those expected fingerprints, all functional/budget tests remained green. The final v10 build fingerprint commit is also fully green.

## CLOSED M0.9D engineering gates

- production sprite contract — CLOSED;
- mapping-constrained compiler — CLOSED;
- machine-checkable piece/chunk/palette budgets — CLOSED;
- reproducible 30-frame indexed source pipeline — CLOSED;
- deterministic ROM integration — CLOSED;
- player-local runtime integration + exact inactive fallback — CLOSED;
- v10 source/bank/build identity — CLOSED as current candidate.

## OPEN

### O1 — final micro-detail/art-quality refinement and production freeze

v10 is the active production candidate and is materially stronger than v9, but it is not yet frozen as final player art. Remaining work is deliberately narrow: raise micro-detail/readability to the retail-quality baseline without changing the closed engineering contract.

Completion requires:

- coherent Quaid identity across five authored/eight runtime facings;
- neck/face, sleeve/hand, cloth-fold and boot/leg separation at production-quality pixel-art density;
- broad/heavy Quaid silhouette and six-phase gait remain readable;
- source remains original and reproducible;
- compile/budget assertions remain green;
- runtime remains player-local with exact inactive fallback;
- final source/bank/ROM fingerprints are audited;
- explicit production freeze of the player-art pipeline.

## Parallel scene-authoring branches — PRESERVED, NOT ACTIVE NEXT

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

Do not switch tracks merely because the remaining work is artistic. A deliberate switch must first be recorded here.

## NEXT

1. Use v10 as the fixed technical/art baseline; do not return to v9.
2. Make one focused micro-detail pass inside the same source canvases/mapping masks: neckline/jaw, sleeves/hands, shirt folds, thigh/boot separation.
3. Review all five authored facings across all six phases against the retail visual-density baseline while preserving distinct Quaid identity.
4. Recompile; require 17/24-or-better slot use, <=4 pieces/frame, palette 0..15 and all closed assertions green.
5. Update fingerprints only for legitimate pixel changes and rebuild from the canonical ROM.
6. Re-run M09D runtime regression against M07C; require the same ten containment/fallback/control invariants.
7. If the quality gap is closed and all gates remain green, mark M0.9D COMPLETE, freeze the production player-art pipeline and establish the first M1.0 vertical-slice integration baseline.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed engineering gates reopen only on contradictory evidence.
- Do not rewrite the M09C native seam for art convenience.
- Do not expand mapping geometry until the fixed ten-record/24-slot contract is demonstrably insufficient.
- Generated PNGs/ROMs are outputs; source code + contract + verified ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D engineering closed; v10 Quaid candidate reproducible, budget-clean, CI-green and runtime-regression green.
EVIDENCE extracted_metadata/m09d_quaid_v10_candidate.json + Actions run 38018819486 + canonical retail group-7 visual baseline.
OPEN     final Quaid micro-detail/art-quality refinement and production player-art freeze.
NEXT     one focused v11 micro-detail pass inside the closed v10 contract, then compile/build/runtime gate and freeze if the visual bar is met.
```
