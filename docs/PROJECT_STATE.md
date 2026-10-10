# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. The checkpoint below is the last material proof checkpoint; later documentation-only commits may advance HEAD.

## Active continuation

```text
branch:     m1.0a-integration-baseline
milestone:  M1.0A — Total Recall integration baseline
checkpoint: 03eca058804efe54cef675de5e736ed0b80cf143
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE as the first production player-art baseline.** The v9 Quaid family closes the milestone's pre-existing completion criteria: coherent authored facings, readable six-phase locomotion, original/reproducible indexed source, unchanged 10-record/24-slot mapping contract, green budgets, exact inactive fallback, zero control/link divergence, audited source/bank/ROM fingerprints and green CI. The player-art **pipeline and contract are now frozen**. Later pixel-art polish is content revision and does not reopen M0.9D unless it contradicts an engineering invariant.

M1.0 production has therefore begun at the integration-baseline stage. M1.0A is not yet the finished vertical slice; it exists to prove that the frozen M09D player layer and the M11D/M10 scene-authoring stack compose deterministically in one build before content-scale work.

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

M0.1–M0.6 reconstruction/authoring, M0.7 deterministic held-Y sprint, M0.8 runtime-authored graphics, M0.9 native player presentation + first Quaid production baseline, M0.10 world-collision authoring and M0.11A–D canonical scene-source authoring are retained as stable foundation. Parallel M11E–H branches remain preserved experiments and do not override this track.

## M0.9C canonical runtime model — CLOSED / CONFIRMED

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
native bridge = 0x009D5E
raw phase deltas = 0,2,4,6,8,10
```

The `0x0F0000 == F9F8 descriptor`, adjacent-word 32-bit pointer reconstruction and “every +0x24 write is external reselection” models remain FALSIFIED.

M09C proof build:

```text
size:     4,194,304 bytes
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
```

Primary evidence:

- `extracted_metadata/m09c_canonical_phase_bridge.json`
- `extracted_metadata/m09c_native_phase_trampoline_runtime.json`
- `extracted_metadata/m09c_native_full_visual_regression.json`

## M0.9D production player-art baseline — CLOSED / CONFIRMED

Frozen contract:

```text
descriptor:             0x000A0000
native phases:          6
runtime facings:        8
authored facings:       N, NE, E, SE, S
native mirrors:         SW<-SE, W<-E, NW<-NE
unique mapping records: 10
resource group:         7
reserved chunk slots:   0x68..0x7F (24)
used slots/phase:       17
max pieces/frame:       4
palette indices:        0..15
```

Production source of truth: `tools/build/m09d_quaid_sprint_source.py`.

The accepted v9 baseline corrects directional anatomy (`N` rear, `NE` rear three-quarter, `E` profile, `SE` front three-quarter, `S` front), uses a grey work-shirt/olive-trouser palette strategy and avoids the earlier broad white torso mass. Thirty indexed frames remain generated reproducibly from source code.

Audited v9 fingerprints:

```text
source art SHA-1: 94db7b28dca13720fd2656c37de4e57dc74d6dd4
ROM size:          4,194,304
ROM SHA-1:         eccbd54596c932ba3d7d2361af2437e59087b853
Genesis checksum:  0x7DCB
```

Phase-bank SHA-1 values:

```text
dd64c9fd36639fb81e83aaa734d0c2e09cd32c26
bbe43db7b7639157d19b5b4267c4e5f26dea8444
018c59af23e42825fabb50937dc6263be4840c05
7386aa54924b24c54e5c69b7aa7b079a84f36bb2
8209c9c428fcd8d45169f79caa51225b74d7ad38
241f1d4a95474b8b64f7f1b57727d31e2de1936b
```

Runtime regression against M07C (`55e02728cb0b7f3627f410202c889197c0e3d0d2`) passed:

- pre-trigger exact;
- post-release exact;
- active input Y+Left on all 42 samples;
- zero compared runtime-state mismatches;
- F9F8 descriptor `0x000A0000` preserved;
- all six native phases observed and visibly authored;
- 40/42 active frames visible after two-frame cache/presentation warm-up;
- maximum active diff bbox `63x64` at 2x host capture;
- no mapping-geometry or player-control change.

Evidence: `extracted_metadata/m09d_quaid_v9_candidate.json`.

CI gate at source/bank fingerprint commit `0bb9e8dc1fed55107969a1cdc2a12ffe74bf82cd`:

```text
Actions run:      38015926111
static tests:     58 / 58 PASS
BlastEm harness:  PASS
recovery_doctor:  PASS
```

## M1.0A integration-baseline objective

Prove one reproducible build in which the frozen M09D player presentation coexists with the canonical M11D scene source and M10 world-collision/object-placement derivations without hidden ROM-range conflicts or regression.

This is a composition gate, not a new reverse-engineering excursion. Reuse closed tools rather than inventing parallel formats.

### Required proof

- start from the verified canonical ROM;
- reproduce the frozen M09D v9 player build exactly;
- compile a canonical M11D scene source with a controlled authored scene edit;
- compose scene edit + M09D banks/trampolines/checksum deterministically;
- prove allocation/patch ranges do not overlap unexpectedly;
- reparse the authored scene and require expected tile/object/world-collision semantics;
- run a deterministic BlastEm regression against the correct parent;
- require player control/F9F8/FB6E invariants and M09D presentation fallback to remain intact;
- persist one machine-readable integration manifest containing input/output hashes and all component evidence.

## OPEN

### O1 — M1.0A scene/player composition proof

Blocking. The milestone closes only after one authored scene mutation and the frozen Quaid player layer coexist in a reproducible, reparsed and runtime-regressed build.

### O2 — choose/freeze the production vertical-slice sequence

Blocked by O1. The Level Bible remains design authority for the provisional film-to-game progression. Do not encode a full production level before the composition baseline is green.

## NEXT

1. Verify the canonical ROM locally and reproduce the M09D v9 fingerprint `eccbd545... / 0x7DCB`.
2. Inspect the M11D canonical scene-source compiler and choose the smallest controlled scene mutation suitable for the composition proof.
3. Build the authored scene component from the canonical base and record every relocated/patched ROM range.
4. Compose it with the frozen M09D layer using one deterministic build tool; reject any unplanned overlap.
5. Reparse scene/object/world-collision output and run deterministic BlastEm regression against the correct logical parent.
6. If green, persist the M1.0A integration manifest, close M1.0A and freeze the first production vertical-slice sequence/design target.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- M09C and M09D engineering gates reopen only on contradictory evidence.
- Do not rewrite the native player seam, sprite mapping contract or world/scene formats merely for convenience.
- Prefer composition through existing canonical tools and explicit allocation ledgers.
- Any ROM-range collision must be resolved in the composer, not hidden by hand edits.
- Generated PNGs/ROMs are outputs; source code + manifests + verified canonical ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D v9 production baseline frozen with 58/58 CI and runtime regression green.
EVIDENCE extracted_metadata/m09d_quaid_v9_candidate.json + Actions run 38015926111.
OPEN     M1.0A scene/player composition proof.
NEXT     reproduce v9, compose one controlled M11D scene mutation with the frozen player layer, reparse and runtime-regress.
```
