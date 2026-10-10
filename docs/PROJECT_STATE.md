# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED milestone material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. The checkpoint below is the material technical proof checkpoint, not a promise that live HEAD never advances.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M0.9D — production Quaid source-frame authoring and budget validation
checkpoint: 6b0556aac44b960b43fcf7e19e0abe94f64e4305
```

**M0.9C is COMPLETE.** The native six-phase player-presentation seam is now runtime-proven end-to-end. The active task is no longer reverse-engineering the F9F8 animation identity; it is to replace diagnostic proof glyphs with reproducible original Quaid source frames while preserving the proven native phase/cache path.

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

Retained foundation includes M0.1–M0.6 reconstruction/authoring, M0.7 deterministic held-Y sprint, M0.8 runtime-authored player-local graphics, M0.10 world-collision authoring and M0.11A–D canonical scene-source authoring. Parallel M11E–H branches remain preserved but are not the active track.

## M0.9C canonical runtime model — CONFIRMED

Retail loads `FFFFF9F8` and `FFFFFB6E` with `MOVEA.W`; each global stores a signed 16-bit RAM pointer.

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

The descriptor remains stable through the observed native cycle. The older `0x0F0000 == F9F8 descriptor` interpretation is FALSIFIED; `0x0F0000` remains only M0.8 player-local visual-component evidence.

The linked-object bridge at `0x009D5E` advances the avatar phase through the canonical writer transaction:

```text
0x009D72  F9F8 +0x1E
0x009D7E  F9F8 +0x24
0x009D88  F9F8 +0x20
```

Native raw phase deltas are:

```text
0, 2, 4, 6, 8, 10
```

Primary structural evidence: `extracted_metadata/m09c_canonical_phase_bridge.json`.

## Native six-bank proof build — CONFIRMED

`tools/build/m09c_native_phase_pixel_sequence.py` derives authored resource selection from:

```text
(object+0x1E) - (object+0x1C)
```

while Y is held and only when `object+0x2C == 0x000A0000`.

```text
phase 0 -> bank 0x210000 / cache 0x3A00
phase 1 -> bank 0x218000 / cache 0x3B00
phase 2 -> bank 0x220000 / cache 0x3C00
phase 3 -> bank 0x228000 / cache 0x3D00
phase 4 -> bank 0x230000 / cache 0x3E00
phase 5 -> bank 0x238000 / cache 0x3F00
```

Audited build fingerprint:

```text
size:     4,194,304 bytes
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
```

The exact 68000 trampolines already passed 12/12 native-core dispatch tests. Evidence: `extracted_metadata/m09c_native_phase_trampoline_runtime.json`.

## M0.9C final visual containment/fallback — CONFIRMED

Final runtime evidence: `extracted_metadata/m09c_native_visual_regression.json`.

The comparison starts parent M07C and candidate M09C from the same native pre-Y gameplay state after fresh six-button peripheral initialization. It uses physical `W=Y` + Left input, BlastEm software rendering and external X11 capture; the problematic internal `shot + -g` combination is not used.

Confirmed results:

- parent M07C SHA-1 `55e02728cb0b7f3627f410202c889197c0e3d0d2`;
- candidate M09C SHA-1 `3256f9dcbc6376624716e3508f41c0439e17cef6`;
- normalized active input `F6EC = 0x2044` on all 42 active samples;
- 44 parent/candidate state samples compared with **zero RAM/control mismatches**;
- F9F8 descriptor remains `0x000A0000`;
- all six native phase deltas appear and every phase has visible authored-pixel evidence;
- two-frame presentation/cache activation latency, followed by continuous visible authored effect through the remaining active window;
- retail active records `0x5AC8/0x5AE4` have `clip_width=48`, `clip_height=39`, yielding a 2x visual envelope of `96×78`;
- observed maximum active gameplay-difference bbox is `78×64`, entirely inside that retail avatar envelope;
- pre-trigger gameplay region is pixel-exact to M07C;
- post-release gameplay region is pixel-exact to M07C;
- small host/raster differences were confined below the established 224-source-line gameplay comparison region and are not game-state divergence.

Therefore the M09C completion gate is closed: native phase -> authored bank/cache namespace -> renderer/cache/VRAM/SAT -> player-local visible output is runtime-proven without movement/control/link regression.

## Closed/falsified M09C models

Do not reopen without contradictory runtime evidence:

- F9F8 descriptor is `0x0F0000` — FALSIFIED.
- F9F8/FB6E are adjacent-word reconstructed 32-bit pointers — FALSIFIED.
- every `+0x24` write is an external reselection — FALSIFIED.
- M09C still needs a native visual containment gate — CLOSED by `m09c_native_visual_regression.json`.

## Active milestone: M0.9D

Goal: turn the proven presentation seam into a production player-art pipeline for Quaid.

Completion criteria:

1. Define the production Quaid sprite contract: canvas/anchor/clip geometry, palette policy, allowed piece count, cache/VRAM budget and directional coverage.
2. Produce an original source-art sequence for at least one coherent locomotion/sprint family; diagnostic proof glyphs are not production art.
3. Compile the source sequence through the existing 16×16 decomposition/global-dedup pipeline with deterministic metadata.
4. Prove the compiled sequence fits the established cache/VRAM/sprite pressure budget.
5. Integrate it through the already-proven native M09C phase path without changing F9F8/FB6E control semantics.
6. Run deterministic runtime comparison showing player-local authored output and exact inactive fallback.
7. Only after those gates are green freeze the production player-art pipeline and advance toward the first Total Recall vertical slice.

## OPEN

### O1 — production Quaid source-frame contract

Define the exact art/technical constraints from the now-confirmed runtime mapping geometry and compiler limits.

### O2 — first production Quaid locomotion/sprint family

Blocked on O1. Source art must be original/reproducible and designed for Genesis constraints rather than downscaled after the fact.

## Parallel scene-authoring branches — PRESERVED, NOT ACTIVE NEXT

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

Do not switch tracks merely because player-art production requires creative iteration. A deliberate track switch must first be recorded here.

## NEXT

1. Derive the production Quaid sprite specification from the confirmed F9F8 mapping geometry and current sprite compiler.
2. Audit current sequence compiler limits against that specification: piece count, chunk count, global dedup, palette index 0, cache working set and eight-direction requirements.
3. Add machine-readable production budgets/assertions before final art is introduced.
4. Build a reproducible original Quaid source-frame template/first locomotion-sprint sequence against those budgets.
5. Compile it and run static round-trip/budget checks.
6. Integrate the first production frames through the closed M09C native phase seam and runtime-regress against M07 semantics.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed gates reopen only on contradictory evidence.
- Runtime identity evidence outranks static naming assumptions.
- Preserve M09C diagnostic proof assets as tests; do not mistake them for production art.
- Do not rewrite the native seam merely to make art authoring easier unless a measured production constraint requires it.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M0.9C COMPLETE: canonical F9F8 identity, native six-phase bridge, 12/12 trampoline dispatch and full visual containment/fallback runtime proof.
EVIDENCE extracted_metadata/m09c_canonical_phase_bridge.json + extracted_metadata/m09c_native_phase_trampoline_runtime.json + extracted_metadata/m09c_native_visual_regression.json.
OPEN     M0.9D production Quaid sprite contract, then first original locomotion/sprint family.
NEXT     derive and codify production sprite budgets from confirmed runtime geometry + compiler constraints.
```
