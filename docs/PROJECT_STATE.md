# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before interpreting milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` defines **where work resumes now**.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in a machine-readable form.
3. `docs/TECHNICAL_STATE.md` is the cumulative technical compendium; it does not override this file when choosing `NEXT`.
4. Milestone documents record subsystem knowledge. A document marked HISTORICAL/FALSIFIED must never be used as a promotion gate.
5. Drive controls project/design continuity, but Drive copies of dynamic state must defer to this file rather than independently redefining the active branch or next task.
6. Always refresh the live branch HEAD before writing. The checkpoint below identifies the technical proof state; later documentation-only commits may advance HEAD.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M0.9C — native player sequence integration seam
checkpoint: e77565bd0a56bc807806f9a91d2e87af70ed89e6
```

Current objective: finish the deterministic full-game visual regression for the six-phase native F9F8 authored-pixel build. Do not switch to the parallel M11 scene-authoring track merely because capture is operationally inconvenient.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed.

**Recovery rule:** ROM availability is session-local. Never infer that a fresh context already has raw bytes merely because an earlier session did. Before any ROM-dependent action, locate/provide the base ROM and verify size + SHA-1.

## Stable foundation

Completed and retained as technical foundation:

- M0.1 canonical ROM validation.
- M0.2 static landmarks / RAM / cheat-correlated seams.
- M0.3 entity architecture.
- M0.4 asset/cutscene extraction pipeline.
- M0.5 gameplay map format.
- M0.6A–M: player architecture, persistent object stream, VM, archetypes, maps, scene placement and scripted-type authoring.
- M0.7 deterministic BlastEm harness + held-Y sprint runtime proof.
- M0.8 4 MiB expansion + runtime-visible authored player-local graphics path.
- M0.10A/B runtime-confirmed world-resource relocation/material behavior.
- M0.10C–F exact broadphase/world-manifest authoring foundation.
- M0.11A–D unified canonical scene-source foundation on the stable scene track.

The first Total Recall production vertical slice has not begun.

## M0.9C canonical correction — CONFIRMED

Earlier M09C work made a useful but incorrect identity assumption:

```text
F9F8 world/render avatar descriptor == 0x0F0000
JLLBFR family 0x00F2 must resolve through 0x0F0000
```

Canonical runtime execution falsified that model.

### Linked player globals are word pointers

Retail code loads these globals with `MOVEA.W`; they contain signed 16-bit RAM pointers, not adjacent halves of 32-bit pointers.

Observed gameplay values:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

The old v1 tracer reconstructions such as `0xC6320000` / `0xC7FA000F` were tooling artifacts.

### Canonical F9F8 identity

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

`object+0x2C` remains stable through the observed native cycle.

M0.8's `0x0F0000` result remains valid only as **player-local visual-component evidence**. It is not the canonical F9F8 world/render-avatar descriptor.

Primary refinement document: `docs/M08_RUNTIME_AUTHORED_GRAPHICS.md`.

## Native phase bridge — CONFIRMED

The linked-object bridge at `0x009D5E` transfers animation **phase** from the proxy to the F9F8 avatar.

Effective behavior:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Canonical writer cluster:

```text
0x009D72  F9F8 +0x1E current phase
0x009D7E  F9F8 +0x24 encoded entry
0x009D88  F9F8 +0x20 resolved mapping record
0x011284  F9F8 +0x22 mirror of resolved record in observed trace
```

This ordered `+0x1E -> +0x24 -> +0x20` cluster is one native progression transaction. A `+0x24` write inside it is **not** automatically a new external selection event.

Primary evidence: `extracted_metadata/m09c_canonical_phase_bridge.json`.

## Observed six-position sprint cycle — CONFIRMED

F9F8 base phase:

```text
object+0x1C = 0x08B6
```

Current phase cycle:

```text
0x08B6 -> 0x08B8 -> 0x08BA -> 0x08BC -> 0x08BE -> 0x08C0 -> 0x08B6
```

Canonical raw deltas:

```text
0, 2, 4, 6, 8, 10
```

Mapping records:

```text
0x2C08 0x2C24 0x2C44 0x2C64 0x2C80 0x2CA0
```

Encoded entries:

```text
0x02AC 0x02AE 0x02B0 0x02B2 0x02B4 0x32B6
```

No `+0x2C` descriptor write occurred during the trace.

## Corrected M09C tooling

Authoritative current tools:

```text
tools/runtime/m09c_animation_state_trace_v2.py
tools/rom_probe/m09c_phase_bridge_analysis.py
tools/build/m09c_native_phase_pixel_sequence.py
```

Historical tools retained for provenance, not promotion:

```text
tools/runtime/m09c_animation_state_trace.py
tools/rom_probe/m09c_canonical_gate.py
tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py   # old JLLBFR@0x0F0000 interpretation
tools/rom_probe/m09c_animation_progression_analysis.py  # old +0x24/reselection rule
```

Do not modify historical tools merely to force their old hypothesis to pass.

## Native-phase six-bank proof build — IMPLEMENTED

`tools/build/m09c_native_phase_pixel_sequence.py` preserves the M07 sprint seam and M09B2 renderer/cache override architecture, but replaces the VBlank-driven source:

```text
(F712 >> 2) & 3
```

with native F9F8 phase:

```text
raw_delta = (object+0x1E) - (object+0x1C)
```

for deltas `0,2,4,6,8,10` and only while:

```text
object+0x2C == 0x000A0000
```

Phase resources:

```text
0 -> bank 0x210000 / cache namespace 0x3A00
1 -> bank 0x218000 / cache namespace 0x3B00
2 -> bank 0x220000 / cache namespace 0x3C00
3 -> bank 0x228000 / cache namespace 0x3D00
4 -> bank 0x230000 / cache namespace 0x3E00
5 -> bank 0x238000 / cache namespace 0x3F00
```

Audited proof-build fingerprint:

```text
ROM size: 4,194,304
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
key tramp: 146 bytes
render:    140 bytes
```

## 68000 trampoline runtime proof — CONFIRMED

The exact candidate trampolines executed under the project-pinned BlastEm 68000 core:

```text
6 render-source dispatches
6 cache-key dispatches
12/12 PASS
```

Render D1 results:

```text
0 -> 0x210000
2 -> 0x218000
4 -> 0x220000
6 -> 0x228000
8 -> 0x230000
10 -> 0x238000
```

Cache results for retail chunk index `0x17`:

```text
0 -> 0x3A17
2 -> 0x3B17
4 -> 0x3C17
6 -> 0x3D17
8 -> 0x3E17
10 -> 0x3F17
```

Evidence: `extracted_metadata/m09c_native_phase_trampoline_runtime.json`.

VERIFY also caught and fixed an invalid zero-displacement short `BRA`; the assembler now rejects that encoding and CI protects the case.

## CI state

Latest technical checkpoint recorded before this documentation reconciliation:

```text
workflow: m09c-static
run:      37997040444
head:     373b3d33636c12f6c30c206165ad171168694e6c
result:   success
unittest: 42 tests / 0 failures / 0 errors
BlastEm harness integration: success
```

Documentation-only commits after the technical checkpoint do not invalidate those proofs.

## OPEN

### O1 — full-game visual containment/fallback regression

This is the only material M09C completion gate.

Required proof:

- before Y: exact convergence to the correct M07 sprint parent;
- held Y: differences remain player-local;
- the six authored states correlate one-to-one with native F9F8 deltas `0,2,4,6,8,10`, not `F712`;
- cache namespaces do not contaminate unrelated actors;
- Y release: exact convergence to parent;
- M07 movement/control behavior remains intact;
- F9F8/FB6E link semantics and F9F8 descriptor `0x0A0000` remain intact.

Operational constraint: BlastEm `shot` hangs when combined with `-g` software rendering in the current environment. The debugger/control harness itself is healthy. Use the normal renderer or an external X capture path; do not classify the `-g` screenshot hang as a game failure.

### O2 — production Quaid source frames

Blocked on O1. Do not integrate final artwork before the native six-phase containment/fallback gate is green.

## Parallel scene-authoring branches — PRESERVED, NOT ACTIVE NEXT

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

These branches preserve real work. They do not override the active M09C continuation state.

## NEXT

1. Ensure the canonical ROM is available locally and verify size + SHA-1.
2. Build `m09c_native_phase_pixel_sequence.py`; require SHA-1 `3256f9dc...` and checksum `0x843C` for the current proof build.
3. Run the deterministic gameplay window against the correct M07 sprint parent using a capture path that avoids BlastEm `shot` + `-g`.
4. Prove pre/post exact convergence and player-local active differences.
5. Correlate the six visual states with raw F9F8 deltas `0,2,4,6,8,10`.
6. If cache contamination occurs, change only the namespace strategy; maximum two retries without new evidence.
7. If green, mark M09C COMPLETE and begin production Quaid-frame authoring.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Never reopen JLLBFR@`0x0F0000` as the F9F8 identity hypothesis; canonical runtime evidence falsified it.
- Never treat v1 combined-word pointer reconstruction as evidence.
- A closed gate reopens only if later evidence contradicts it.
- Runtime identity evidence outranks static naming assumptions.
- Do not promote M09C on static/disassembly proof alone.
- Prefer small semantic Git commits for material proof/correction.

## CONTINUATION FOOTER

```text
DONE     canonical F9F8 identity + native six-phase bridge recovered; six-bank builder implemented; 12/12 trampoline executions; 42/42 CI tests.
EVIDENCE extracted_metadata/m09c_canonical_phase_bridge.json + extracted_metadata/m09c_native_phase_trampoline_runtime.json + Actions run 37997040444.
OPEN     full-game visual containment/fallback regression only.
NEXT     deterministic M07-parent vs M09C-six-phase visual regression using a non--g screenshot path.
```
