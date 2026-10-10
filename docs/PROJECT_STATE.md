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
checkpoint: 385e634b00901071af882ffc8d7c79bfddd40a6e
```

**M0.9C is COMPLETE.**

**M0.9D is technically proven end-to-end but is not frozen as final production art.** The contract, compiler, original 30-frame source prototype, deterministic ROM integration and runtime containment/fallback proof are green. The remaining gate is art-quality refinement/freeze of the Quaid family; do not redo the native animation seam or the mapping compiler unless new evidence requires it.

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

## M0.9D production sprite contract — CONFIRMED

Machine-readable contract:

`extracted_metadata/m09d_quaid_sprint_contract.json`

Recovered production constraints:

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

The first production family deliberately preserves retail mapping geometry and the 24 proven group-7 slot identities. No mapping-geometry expansion is required for the first Quaid family.

## M0.9D mapping-constrained compiler — CONFIRMED

`tools/build/m09d_mapping_constrained_sprite_compiler.py` extends the existing sprite encoder without creating a second Genesis codec. It reuses `sprite_asset_compiler.encode_chunk` and supports the non-grid retail piece offsets required by the ten canonical records.

It accepts five authored directions × six indexed source frames and emits six raw 32 KiB banks. For the current contract:

```text
source frames:              30
used chunk slots/phase:     17
reserved chunk slots/phase: 24
max pieces/frame:           4
palette range:              <= 15
```

Assertions enforce mapping-geometry preservation, chunk-slot identity, transparency, palette range, per-phase slot budget and native mirrored facings.

## First original Quaid source family — PRODUCTION PROTOTYPE / NOT FINAL ART

Source of truth:

`tools/build/m09d_quaid_sprint_source.py`

The generator produces **30 original indexed frames** (five authored directions × six native phases) plus a source manifest and palette. PNGs are generated outputs, not opaque source truth.

The current prototype uses a heavier, broad-shouldered silhouette, arm/leg counter-swing and Total Recall-specific rust/industrial accents. It is intentionally a technical production prototype, not an assertion that the final Quaid look is approved.

Stable indexed-pixel source fingerprint:

`d7affbf3fd6474ae3aead55fecb098e29ef03528`

All thirty phases are distinct, remain within Genesis indices `0..15`, reserve index `0` for transparency and compile through the closed mapping contract.

## Deterministic M0.9D integration build — CONFIRMED

Builder:

`tools/build/m09d_quaid_sprint_build.py`

Policy:

1. rebuild the canonical M09C parent;
2. compile the generated Quaid family;
3. replace **only** the six 0x8000-byte authored phase banks;
4. recompute the Genesis checksum;
5. leave descriptor, trampolines, mapping geometry and player control untouched.

Current audited prototype build:

```text
size:     4,194,304 bytes
SHA-1:    b279469147ff4b7d76290d2da2738a5d4bb58919
checksum: 0x968B
```

Per-phase bank SHA-1 values are statically pinned by `tests/test_m09d_quaid_sprint_build_static.py`.

## M0.9D runtime regression — CONFIRMED

Evidence:

`extracted_metadata/m09d_quaid_runtime_regression.json`

Runner:

`tools/runtime/m09d_quaid_runtime_regression.py`

Parent M07C:

`55e02728cb0b7f3627f410202c889197c0e3d0d2`

Candidate M09D prototype:

`b279469147ff4b7d76290d2da2738a5d4bb58919`

Pinned BlastEm SHA-256:

`b511890bd1cd6616050e8b009aa9bf1d5d791a326682d3da76d9524467dfb0d2`

Confirmed results:

- pre-trigger scene exact;
- post-release scene exact;
- active normalized input contains Y+Left on all 42 active samples (`F6EC=0x2044`);
- parent/candidate runtime state is identical in all compared control/object fields;
- F9F8 descriptor stays `0x000A0000`;
- all six native deltas `0,2,4,6,8,10` occur;
- two-frame presentation/cache warm-up, then visible authored output on every remaining active frame;
- every native phase has visible authored output;
- maximum active difference bbox is `68x64` in 2x host capture, within the established scaled retail envelope.

Therefore source -> mapping-constrained compile -> six phase banks -> native M09C phase selection -> renderer/cache/VRAM/SAT is proven end-to-end for original Quaid prototype pixels without control/link/scene regression.

## CI state

Actions run `38013011483` passed at commit `d6de2347995167904c600783b9ee57c05f5d5dc6`:

```text
58 tests / 0 failures / 0 errors
BlastEm harness: PASS
recovery_doctor: PASS
```

Later commits add the parameterized M09D runtime runner/evidence and documentation. Re-run CI after each material source/pipeline change.

## CLOSED M0.9D engineering gates

- production sprite contract — CLOSED;
- mapping-constrained compiler — CLOSED;
- machine-checkable piece/chunk/palette budgets — CLOSED;
- first reproducible original 30-frame source family — CLOSED as technical prototype;
- deterministic ROM integration — CLOSED;
- player-local runtime integration + exact inactive fallback — CLOSED.

## OPEN

### O1 — Quaid art-quality refinement and production freeze

The procedural source family proves the pipeline but is **not final art**. Refine the source family until it meets the project visual bar while preserving the closed M09D contract unless measured evidence shows that geometry must change.

Completion requires:

- coherent Quaid identity across five authored/eight runtime facings;
- production-quality silhouette and animation character, not diagnostic/procedural placeholder quality;
- six native phases remain readable as a sprint/locomotion cycle;
- source remains original and reproducible;
- compile/budget assertions remain green;
- runtime regression remains player-local with exact inactive fallback;
- final source and ROM fingerprints are audited and the player-art pipeline is then frozen.

## Parallel scene-authoring branches — PRESERVED, NOT ACTIVE NEXT

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

Do not switch tracks merely because player-art refinement is creative work. A deliberate switch must first be recorded here.

## NEXT

1. Refine the reproducible Quaid sprint source family from prototype quality to production-quality pixel art while preserving the current contract.
2. Visually review all five authored facings and six native phases for silhouette, gait readability and Total Recall identity.
3. Recompile with `m09d_mapping_constrained_sprite_compiler.py`; require all budgets/assertions green.
4. Update the audited source/bank/build fingerprints only if art pixels legitimately change.
5. Re-run `m09d_quaid_runtime_regression.py` against M07C and require the same containment/fallback/control invariants.
6. If green, mark M0.9D COMPLETE, freeze the production player-art pipeline and establish the first M1.0 Total Recall vertical-slice integration baseline.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed engineering gates reopen only on contradictory evidence.
- Do not rewrite the M09C native seam merely to make art authoring easier unless a measured production constraint requires it.
- Do not expand mapping geometry until the fixed ten-record/24-slot contract is demonstrably insufficient.
- Generated PNGs/ROMs are outputs; source code + contract + verified ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D contract + mapping compiler + 30-frame original prototype + deterministic build + runtime regression proven.
EVIDENCE extracted_metadata/m09d_quaid_sprint_contract.json + extracted_metadata/m09d_quaid_runtime_regression.json + Actions run 38013011483.
OPEN     Quaid art-quality refinement and production player-art freeze.
NEXT     refine source art within the closed contract, then recompile/re-regress and freeze M09D if green.
```
