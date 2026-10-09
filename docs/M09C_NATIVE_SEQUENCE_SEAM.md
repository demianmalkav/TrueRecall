# M0.9C — Native Player Sequence Integration Seam

Status: **CANONICAL NATIVE PHASE RECOVERED / SIX-BANK BUILD IMPLEMENTED / FULL-GAME VISUAL GATE OPEN**

This document describes the current M09C subsystem model. Earlier JLLBFR@`0x0F0000` gate assumptions have been superseded by canonical runtime evidence.

For continuation priority and exact `NEXT`, always defer to `docs/PROJECT_STATE.md`.

## Goal

Replace the diagnostic M09B2 VBlank-driven authored-pixel phase with authored player presentation driven by the retail-linked F9F8 animation phase while preserving:

- M07 held-Y sprint behavior;
- F9F8/FB6E linked-object semantics;
- canonical F9F8 descriptor identity;
- retail inactive fallback;
- renderer/cache isolation.

## Canonical linked-player identity — CONFIRMED

Retail code loads the player globals with `MOVEA.W`; each global is a signed 16-bit RAM pointer.

Observed runtime values:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

The descriptor remains stable through the observed animation cycle.

### Superseded identity model

M0.8 proved that scoping renderer/cache substitution to `0x0F0000` produces a compact player-local visual difference with clean fallback. That remains valid presentation-path evidence.

Canonical M09C runtime disproves the stronger claim that `0x0F0000` is the F9F8 world/render-avatar descriptor. The tested F9F8 descriptor is `0x000A0000`.

## Native phase bridge — CONFIRMED

The key routine is the linked-object bridge at `0x009D5E`.

Equivalent behavior:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Observed writer transaction:

```text
0x009D72  F9F8 +0x1E
0x009D7E  F9F8 +0x24
0x009D88  F9F8 +0x20
0x011284  F9F8 +0x22 mirror in the observed path
```

Therefore the proxy transfers **phase**, not JLLBFR selector identity, to F9F8.

The old analytical rule that every `+0x24` write indicates a new external selection is false for this bridge. The ordered `0x009D72 -> 0x009D7E -> 0x009D88` writes are one phase-advance transaction.

Evidence: `extracted_metadata/m09c_canonical_phase_bridge.json`.

## Native six-position sprint sequence — CONFIRMED

After the sprint family is active:

```text
F9F8 +0x1C base = 0x08B6
```

`+0x1E` cycles:

```text
0x08B6
0x08B8
0x08BA
0x08BC
0x08BE
0x08C0
-> 0x08B6
```

Raw phase deltas:

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

No `+0x2C` descriptor write occurred during the observed cycle.

## Authoritative tooling

```text
tools/runtime/m09c_animation_state_trace_v2.py
tools/rom_probe/m09c_phase_bridge_analysis.py
tools/build/m09c_native_phase_pixel_sequence.py
```

The v2 tracer corrects the pointer model by sign-extending the 16-bit F9F8/FB6E globals and expects canonical F9F8 descriptor `0x0A0000`.

The phase analyzer recognizes the native writer cluster as a single transaction rather than misclassifying the `+0x24` write.

## Historical tooling — NOT PROMOTION GATES

```text
tools/runtime/m09c_animation_state_trace.py
tools/rom_probe/m09c_canonical_gate.py
tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py
tools/rom_probe/m09c_animation_progression_analysis.py
```

These remain useful provenance for how the ambiguity was resolved. Do not force them to satisfy the old hypothesis.

## Six-bank native-phase build — IMPLEMENTED

`tools/build/m09c_native_phase_pixel_sequence.py` retains the proven M07 sprint seam and M09B2 renderer/cache override concept while replacing the phase source.

Old diagnostic source:

```text
(F712 >> 2) & 3
```

Current native source:

```text
raw_delta = (object+0x1E) - (object+0x1C)
```

Accepted canonical deltas:

```text
0, 2, 4, 6, 8, 10
```

Scope invariant:

```text
object+0x2C == 0x000A0000
```

Resource map:

```text
phase 0 -> bank 0x210000 / cache 0x3A00
phase 1 -> bank 0x218000 / cache 0x3B00
phase 2 -> bank 0x220000 / cache 0x3C00
phase 3 -> bank 0x228000 / cache 0x3D00
phase 4 -> bank 0x230000 / cache 0x3E00
phase 5 -> bank 0x238000 / cache 0x3F00
```

Audited proof build:

```text
size:     4,194,304 bytes
SHA-1:    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum: 0x843C
key trampoline: 146 bytes
render trampoline: 140 bytes
```

## Trampoline runtime proof — CONFIRMED

The exact candidate 68000 trampolines were executed under the project-pinned BlastEm core using reset-vector entry plus debugger-injected actor state.

Twelve executions passed:

```text
6 render-source dispatches
6 cache-key dispatches
```

Render source results:

```text
0  -> 0x210000
2  -> 0x218000
4  -> 0x220000
6  -> 0x228000
8  -> 0x230000
10 -> 0x238000
```

Cache-key results with retail chunk `0x17`:

```text
0  -> 0x3A17
2  -> 0x3B17
4  -> 0x3C17
6  -> 0x3D17
8  -> 0x3E17
10 -> 0x3F17
```

Evidence: `extracted_metadata/m09c_native_phase_trampoline_runtime.json`.

## VERIFY correction: zero-displacement BRA

The first prototype accidentally emitted a short `BRA` whose displacement was zero. On 68000, opcode `0x6000` denotes a word-extension branch rather than a valid zero-distance short branch. BlastEm exposed the wrong target.

Correction:

- phase 5 falls directly into restore;
- assembler rejects zero-displacement short branches;
- CI protects the regression.

This is a closed correction unless new evidence contradicts it.

## CI

Latest technical checkpoint before documentation cleanup:

```text
workflow: m09c-static
run:      37997040444
head:     373b3d33636c12f6c30c206165ad171168694e6c
result:   success
unittest: 42 / 42 pass
BlastEm debugger/control integration: pass
```

Coverage includes historical guardrails, corrected word-pointer semantics, phase-bridge classification, six-phase builder contract, zero-BRA rejection and emulator debugger/control integration.

## Remaining runtime gate

M09C is not complete until the six-phase build passes a full gameplay containment/fallback comparison against the correct M07 sprint parent.

Required:

1. pre-Y gameplay convergence is exact;
2. held-Y visual differences remain player-local;
3. six authored states correlate one-to-one with F9F8 deltas `0,2,4,6,8,10`;
4. no unrelated actor is contaminated by cache namespaces;
5. post-Y convergence is exact;
6. M07 movement/control behavior remains intact;
7. F9F8/FB6E link semantics remain intact;
8. F9F8 descriptor remains `0x000A0000`.

Operational note: BlastEm `shot` hangs when used with `-g` software rendering in the current environment. Use the normal renderer or external X capture; the screenshot hang is not evidence of a ROM failure.

## Completion criteria

M09C completes only when:

- canonical word-pointer model is preserved;
- canonical F9F8 descriptor identity is preserved;
- authored resources are selected from native F9F8 phase, not `F712`;
- six-phase dispatch is runtime-correct;
- active visual effects remain player-local;
- inactive fallback is exact;
- evidence and audited fingerprints are persisted.

Only after that should diagnostic chunks be replaced with production Quaid source frames.
