# TrueRecall — Authoritative Project State

This file is the single authoritative continuation state for the reverse-engineering / reconstruction workflow. When work resumes with `continua`, execute `NEXT` from this file unless new evidence requires a state revision.

## Active branch

```text
m09c-native-sequence-seam
```

## Active milestone

```text
M0.9C — native player sequence integration seam
```

Current objective: replace the M09B2 diagnostic VBlank-driven pixel phase with authored resources driven by the **native F9F8 animation phase**, while preserving the M07 sprint behavior, linked F9F8/FB6E player semantics and retail fallback.

## CANONICAL ROM — AVAILABLE / VERIFIED

The canonical ROM is now available as raw bytes in the current work session.

```text
size:  2,097,152 bytes
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The previous Library-materialization blocker is CLOSED.

## MAJOR CANONICAL CORRECTION

The earlier M09C hypothesis was wrong in a useful way.

The old gate assumed:

```text
F9F8 visual avatar descriptor == 0x0F0000
JLLBFR family 0x00F2 must resolve through 0x0F0000
```

Canonical ROM execution disproved that model.

### Linked player globals are word pointers

Retail code loads the player globals with `MOVEA.W`; they contain signed 16-bit RAM pointers, not adjacent halves of 32-bit pointers.

Canonical runtime values in the tested gameplay path:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

The v1 tracer's reconstructed values such as `0xC6320000` / `0xC7FA000F` were tooling errors caused by combining adjacent words.

### Canonical F9F8 identity

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

The descriptor remains stable during the observed animation cycle.

M08's `0x0F0000` result remains valid as **player-local visual-component evidence**, but it is no longer identified as the F9F8 world/render-avatar descriptor. `docs/M08_RUNTIME_AUTHORED_GRAPHICS.md` records this refinement.

## NATIVE PHASE BRIDGE — CANONICAL RUNTIME PROOF

The key routine is the linked-object bridge at `0x009D5E`.

Its effective behavior is:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Canonical writer PCs inside that transaction:

```text
0x009D72  F9F8 +0x1E current phase
0x009D7E  F9F8 +0x24 encoded entry
0x009D88  F9F8 +0x20 resolved mapping record
0x011284  F9F8 +0x22 mirror of resolved record in observed trace
```

This proves that the proxy transfers **phase**, not JLLBFR selector identity, into the linked world/render avatar.

### Observed six-position sprint cycle

After the sprint family is selected, F9F8 uses:

```text
base +0x1C = 0x08B6
```

and current `+0x1E` cycles:

```text
0x08B6
0x08B8
0x08BA
0x08BC
0x08BE
0x08C0
→ wrap to 0x08B6
```

Therefore the native raw phase deltas are exactly:

```text
0, 2, 4, 6, 8, 10
```

Observed mapping-record cycle:

```text
0x2C08 0x2C24 0x2C44 0x2C64 0x2C80 0x2CA0
```

Observed encoded-entry cycle:

```text
0x02AC 0x02AE 0x02B0 0x02B2 0x02B4 0x32B6
```

No `+0x2C` descriptor write occurred during the trace.

Primary evidence:

```text
extracted_metadata/m09c_canonical_phase_bridge.json
```

## FALSIFIED / HISTORICAL GATES

The following tools remain in-tree as historical evidence but are no longer authoritative promotion gates:

```text
tools/rom_probe/m09c_canonical_gate.py
tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py   # when interpreted as JLLBFR@0x0F0000
tools/rom_probe/m09c_animation_progression_analysis.py  # old +0x24/reselection rule
```

Why:

- JLLBFR `0x00F2` does not resolve coherently through `0x0F0000`;
- `0x0F0000` is not F9F8 identity in the canonical tested path;
- native bridge `0x009D5E` legitimately writes `+0x1E → +0x24 → +0x20`, so a `+0x24` write inside that cluster is part of progression, not external reselection.

Do not repair these historical gates by forcing their old hypothesis to pass.

## CORRECTED TOOLING

Authoritative corrected tools:

```text
tools/runtime/m09c_animation_state_trace_v2.py
tools/rom_probe/m09c_phase_bridge_analysis.py
tools/build/m09c_native_phase_pixel_sequence.py
```

The v2 tracer:

- sign-extends the 16-bit F9F8/FB6E globals;
- expects canonical F9F8 descriptor `0x0A0000`;
- preserves the proven PTY/control/watchpoint harness from v1.

The new analyzer recognizes the ordered writer cluster:

```text
9D72 -> 9D7E -> 9D88
```

as one native phase-advance transaction.

## M09C NATIVE-PHASE PIXEL BUILD — IMPLEMENTED

`tools/build/m09c_native_phase_pixel_sequence.py` keeps the M07 sprint seam and the M09B2 renderer/cache override architecture, but changes the presentation phase source from:

```text
(F712 >> 2) & 3
```

to:

```text
raw_delta = (object+0x1E) - (object+0x1C)
```

for canonical deltas:

```text
0, 2, 4, 6, 8, 10
```

The build scopes the authored source/cache substitution to:

```text
object+0x2C == 0x000A0000
```

and maps the six phases one-to-one to:

```text
phase 0 -> bank 0x210000 / cache namespace 0x3A00
phase 1 -> bank 0x218000 / cache namespace 0x3B00
phase 2 -> bank 0x220000 / cache namespace 0x3C00
phase 3 -> bank 0x228000 / cache namespace 0x3D00
phase 4 -> bank 0x230000 / cache namespace 0x3E00
phase 5 -> bank 0x238000 / cache namespace 0x3F00
```

Canonical-base build fingerprint from the current proof build:

```text
ROM size:   4,194,304
SHA-1:      3256f9dcbc6376624716e3508f41c0439e17cef6
checksum:   0x843C
key tramp:  146 bytes
render:     140 bytes
```

The six diagnostic chunks have distinct persisted SHA-1 fingerprints in the runtime evidence file.

## 68000 TRAMPOLINE RUNTIME PROOF — CONFIRMED

The exact candidate trampolines were executed by the project-pinned BlastEm 68000 core using reset-vector entry and debugger-injected actor state.

Twelve executions were performed:

```text
6 render-source dispatches
6 cache-key dispatches
```

All passed.

Render D1 results:

```text
0 -> 0x210000
2 -> 0x218000
4 -> 0x220000
6 -> 0x228000
8 -> 0x230000
10 -> 0x238000
```

Cache results with retail chunk index `0x17`:

```text
0 -> 0x3A17
2 -> 0x3B17
4 -> 0x3C17
6 -> 0x3D17
8 -> 0x3E17
10 -> 0x3F17
```

Evidence:

```text
extracted_metadata/m09c_native_phase_trampoline_runtime.json
```

### Assembler correction caught during VERIFY

The first prototype encoded a short `BRA` with displacement zero after phase 5. On 68000, opcode `0x6000` means BRA with a word extension; BlastEm correctly disassembled the resulting jump into the wrong address.

Fix:

- phase 5 now falls directly into restore;
- the assembler rejects any zero-displacement short branch;
- CI has a dedicated regression test for this case.

## CI — GREEN

Latest corrected M09C CI checkpoint:

```text
workflow: m09c-static
run:      37997040444
head:     373b3d33636c12f6c30c206165ad171168694e6c
static:   success
BlastEm harness: success
unittest: 42 tests, 0 failures, 0 errors
```

The suite covers the legacy evidence, corrected word-pointer semantics, phase-bridge classification, six-phase builder contract, zero-BRA regression and debugger/control-socket integration.

## OPEN

### O1 — full-game visual regression of the six-phase build

This is now the only material M09C completion gate.

Required proof:

- before Y: candidate converges exactly to the correct sprint parent;
- held Y: differences remain player-local;
- six authored visual states are driven by the native F9F8 phase sequence, not `F712`;
- cache namespaces `0x3A00` and `0x3B00` do not contaminate unrelated actors;
- Y release: exact convergence to parent;
- M07 movement/control behavior remains intact;
- F9F8/FB6E link semantics and F9F8 descriptor `0x0A0000` remain intact.

Operational note: BlastEm `shot` hangs in this environment when `-g` software rendering is used. The debugger/watchpoint harness itself is healthy. Visual capture must use the normal renderer or an external X capture path; do not interpret the `-g` screenshot hang as a game/build failure.

### O2 — production Quaid source frames

Do not begin final artwork integration until O1 is green.

Once O1 closes, replace diagnostic chunks with six compiler-produced authored Quaid frames and retain the same native-phase/cache regression gates.

## PARALLEL SCENE-AUTHORING TRACK

M11 scene-source/palette work remains on separate branches. It is not the active `NEXT` while M09C has only one visual completion gate remaining.

Do not switch tracks merely because visual capture is operationally inconvenient; solve the capture/regression gate first or explicitly record a deliberate track switch here.

## NEXT

1. Build the canonical M09C six-phase candidate with `m09c_native_phase_pixel_sequence.py` and verify fingerprint `3256f9dc...` / checksum `0x843C`.
2. Run the deterministic gameplay window against the correct M07 sprint parent using a capture path that does not combine `shot` with BlastEm `-g`.
3. Prove pre/post exact convergence and player-local active differences.
4. Correlate the six observed authored visual states with native F9F8 raw deltas `0,2,4,6,8,10`.
5. If cache namespaces `0x3A00/0x3B00` cause unrelated diffs, change only the namespace strategy and rerun; maximum two retries without new evidence.
6. If green, mark M09C COMPLETE and begin production Quaid-frame authoring.

## RETRY / ANTI-LOOP RULES

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Do not reopen the old JLLBFR@0x0F0000 hypothesis; canonical runtime evidence falsified it.
- Do not treat the old v1 pointer reconstruction as evidence.
- A closed gate is not reopened unless a later test contradicts it.
- Runtime identity evidence outranks static naming assumptions.
- Do not promote M09C on static/disassembly proof alone: O1 still requires full gameplay visual containment/fallback evidence.
- Prefer one small semantic commit per material proof or correction.

## CONTINUATION FOOTER

```text
DONE     canonical F9F8 identity + six-phase bridge recovered; six-phase builder implemented; 12/12 BlastEm trampoline executions; 42/42 CI tests.
EVIDENCE m09c_canonical_phase_bridge.json + m09c_native_phase_trampoline_runtime.json + Actions run 37997040444.
OPEN     full-game visual containment/fallback regression only.
NEXT     run deterministic M07-parent vs M09C-six-phase visual regression without BlastEm -g screenshot path.
```
