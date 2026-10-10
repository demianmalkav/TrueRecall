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
milestone:  M1.0 — first Total Recall vertical-slice integration baseline
checkpoint: 00d9a0e9db501e7f8763515ce34fbe7476dd6c67
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE and FROZEN.** The first production Quaid sprint/locomotion family and its source-to-ROM pipeline are closed. Do not resume v9/v10 art iteration, rewrite the M09C native phase seam, or expand the mapping contract without new contradictory evidence.

The active task is now the first **Total Recall** vertical-slice integration baseline: prove that the already recovered player, scene/object, world-collision and gameplay systems can coexist in one reproducible authored scene without reopening closed subsystems.

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

The following are stable foundation and are not active reverse-engineering gates:

- M0.1–M0.6 ROM, entity, VM, map and authoring reconstruction;
- M0.7 deterministic held-Y sprint;
- M0.8 runtime-authored player-local graphics;
- M0.9C native six-phase player presentation integration;
- M0.9D production Quaid sprint family and source-to-ROM pipeline;
- M0.10 world-collision authoring;
- M0.11A–D unified canonical scene-source authoring.

Parallel scene-authoring branches remain preserved but are **not** automatically promoted:

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

Any switch to one of them must be deliberate and recorded here first.

## M0.9C canonical runtime model — CLOSED / CONFIRMED

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
native bridge = 0x009D5E
raw phase deltas = 0,2,4,6,8,10
```

The `0x0F0000 == F9F8 descriptor` model, adjacent-word 32-bit pointer reconstruction and “every +0x24 write is external reselection” model are FALSIFIED.

M09C proof build:

```text
size:     4,194,304 bytes
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
banks:    0x210000,0x218000,0x220000,0x228000,0x230000,0x238000
cache:    0x3A00..0x3F00
```

Primary evidence:

- `extracted_metadata/m09c_canonical_phase_bridge.json`
- `extracted_metadata/m09c_native_phase_trampoline_runtime.json`
- `extracted_metadata/m09c_native_visual_regression.json`

## M0.9D production Quaid family — COMPLETE / FROZEN

Freeze evidence:

`extracted_metadata/m09d_quaid_v11_production_freeze.json`

Source of truth:

`tools/build/m09d_quaid_sprint_source.py`

Production contract:

```text
descriptor:             0x000A0000
native phases:          6
runtime facings:        8
authored facings:       N, NE, E, SE, S
native H-flip reuse:    SW<-SE, W<-E, NW<-NE
unique mapping records: 10
resource group:         7
reserved chunk slots:   0x68..0x7F (24 slots)
used chunk slots/phase: 17
max pieces/frame:       4
transparent index:      0
palette indices:        0..15
```

v11 source fingerprint:

`da0a060e77f9da835b388ffe94a8090d75cd51ea`

v11 phase-bank SHA-1:

```text
97a9f024374b75810dd060ff8c03b4b703cd7ab6
fce14e16bc2325ea603f7ad973a0033c56f68098
38c2f905c4f05cc01938f440f2e7cd8a9fa28d74
12fd0abb168d4983fc3b6d2d46a4589317c8f6c2
0cd1b90c15c55504e2e55e992197022a5856204f
416007b12132f06ff30fa009649e4b1c6379d5c1
```

Frozen v11 integration build:

```text
size:     4,194,304 bytes
SHA-1:    49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum: 0x266C
parent:   3256f9dcbc6376624716e3508f41c0439e17cef6
```

Runtime regression against exact M07C parent `55e02728cb0b7f3627f410202c889197c0e3d0d2` passed all ten containment/fallback/control assertions with zero compared-state mismatches, all six native phases, first visible step 3 and maximum gameplay-difference bbox 65x64 host pixels.

CI checkpoint `4e933f104292a88d6301d0c39855176253a077d1`, Actions run `38019250327`: 58 static tests PASS and BlastEm harness PASS.

## M1.0 objective — first integration baseline

M1.0 is not “build the whole first level”. It is the smallest reproducible scene proving that the Total Recall production player can coexist with authored level content through the recovered engine.

The initial baseline should use **scene 18 as the sandbox unless new evidence shows a better target**, because M11D already proved exact no-op reconstruction and controlled plane/object/world-collision edits there while its world-collision scene is empty enough to isolate authored changes.

The first baseline must demonstrate, in one derived ROM built from the canonical base:

1. frozen v11 Quaid production player path remains intact;
2. one declaratively authored scene edit through the canonical scene-source pipeline;
3. at least one authored object/pickup chosen from an already-semanticized safe type;
4. at least one authored world-collision record with expected player interaction;
5. deterministic build identity and containment audit;
6. runtime entry into the scene with no player/control regression.

This is an **integration scaffold**, not yet the final Mars art pass. New tile graphics, palette reauthoring and broader scene-presentation work remain separate gates and must not be smuggled into the baseline unless the baseline proves they are required.

## OPEN

### O1 — M1.0A integration manifest and static build

Define one machine-readable vertical-slice manifest that composes the frozen v11 player build with a canonical M11D scene-18 authored edit. Select object types from confirmed semantic evidence, not guesses. Compile it from the canonical ROM and prove all modified byte ranges are intended.

### O2 — M1.0B runtime smoke

Boot the M1.0A candidate deterministically, enter the authored scene, verify player/control identity and show runtime evidence for the authored scene object/collision behavior. Parent/child comparison must use the correct direct parent.

### O3 — visual-world authoring gate after baseline

Only after M1.0A/B are green, decide whether the active branch needs palette/tile authoring from the preserved M11E–H work. Any promotion must be explicit and based on a measured limitation of M11D.

## NEXT

1. Inspect the current M11D scene-source compiler and the semantic object/pickup evidence for scene-safe types.
2. Freeze a minimal `M1.0A` scene-18 manifest: one authored object/pickup plus one authored world-collision record, preserving all immutable scene boundaries.
3. Add a compositor/build tool that starts from the canonical ROM, applies the frozen v11 player integration, then applies the M11D scene transaction deterministically.
4. Run static containment/no-op invariants and record the candidate ROM fingerprint.
5. Run a deterministic BlastEm runtime smoke against the correct parent and verify player/control identity plus authored scene behavior.
6. If green, mark M1.0A/B complete and decide the next deliberate presentation gate.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D gates reopen only on contradictory evidence.
- Do not modify v11 player pixels during M1.0 integration.
- Do not expand player mapping geometry for scene-authoring convenience.
- Do not switch to M11E–H merely because their features are attractive; require an evidenced M11D limitation.
- Generated ROMs/PNGs are outputs; source code + manifests + verified canonical ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D v11 production Quaid family and player-art pipeline frozen.
EVIDENCE extracted_metadata/m09d_quaid_v11_production_freeze.json + Actions run 38019250327.
OPEN     M1.0 first Total Recall vertical-slice integration baseline.
NEXT     inspect M11D + semantic object evidence, then build the minimal scene-18 v11+scene integration manifest and static candidate.
```
