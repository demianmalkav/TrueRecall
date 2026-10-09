# M0.9C — Native Animation Progression Trace

Status: **HISTORICAL / SUPERSEDED BY CANONICAL RUNTIME EVIDENCE**

This document preserves the provenance of the first M09C progression-tracing approach. It is **not** a current promotion gate and its former classification rules must not be used to design or validate the active M09C build.

Current authoritative M09C model:

- `docs/PROJECT_STATE.md`
- `docs/M09C_NATIVE_SEQUENCE_SEAM.md`
- `extracted_metadata/m09c_canonical_phase_bridge.json`
- `tools/runtime/m09c_animation_state_trace_v2.py`
- `tools/rom_probe/m09c_phase_bridge_analysis.py`

## What this historical gate tried to answer

The original question was valid: after `0x00FDDC` resolves animation state, what actually advances the player mapping record over time?

The first tracer watched the player-linked state cluster around:

```text
object+0x1C
object+0x1E
object+0x20
object+0x22
object+0x24
object+0x2C
```

It combined deterministic BlastEm absolute-frame input, PTY debugger control and write watchpoints.

That harness concept remains useful. Two interpretations inside the v1 implementation did not survive canonical runtime verification.

## Falsified v1 assumption 1 — pointer reconstruction

The v1 tracer reconstructed F9F8/FB6E as if adjacent 16-bit words were halves of 32-bit pointers.

That produced values such as:

```text
0xC6320000
0xC7FA000F
```

Canonical retail code and runtime evidence show instead that the globals are loaded with `MOVEA.W` and each contains a signed 16-bit RAM pointer:

```text
FFFFF9F8 -> FFFFC632
FFFFFB6E -> FFFFC7FA
```

Therefore v1 reconstructed 32-bit values are tooling artifacts and must never be cited as engine identity evidence.

## Falsified v1 assumption 2 — every +0x24 write means reselection

The old analyzer used a rule equivalent to:

```text
+0x24 write = external selection/reselection
```

Canonical runtime evidence recovered the linked-object bridge at `0x009D5E` and disproved that rule.

Observed native transaction:

```text
0x009D72  avatar +0x1E
0x009D7E  avatar +0x24
0x009D88  avatar +0x20
```

The `+0x24` write here is part of one native phase-advance transaction, not a separate external selector event.

The corrected analyzer therefore classifies the ordered writer cluster as one bridge operation.

## Canonical result that closed the ambiguity

During held-Y sprint, canonical F9F8 state is:

```text
object+0x2A = 139
object+0x2C = 0x000A0000
object+0x1C = 0x08B6
```

`+0x1E` cycles:

```text
0x08B6 -> 0x08B8 -> 0x08BA -> 0x08BC -> 0x08BE -> 0x08C0 -> wrap
```

Raw deltas are:

```text
0, 2, 4, 6, 8, 10
```

No `+0x2C` descriptor write occurred in the observed cycle.

Primary evidence: `extracted_metadata/m09c_canonical_phase_bridge.json`.

## What remains valid from the historical work

The following engineering ideas remain part of the current harness design:

- deterministic absolute-frame KIT input;
- debugger/control-socket coexistence;
- dynamic actor-address resolution rather than hard-coding runtime RAM addresses;
- write-watchpoint evidence;
- frame-anchored runtime state capture;
- refusal to assign timer/state semantics merely from adjacency.

The corrected v2 tracer preserves the useful harness while fixing the pointer and classification models.

## Historical tooling

```text
tools/runtime/m09c_animation_state_trace.py
tools/rom_probe/m09c_animation_progression_analysis.py
```

These files are retained for provenance and regression understanding. They are not current promotion gates.

## Do not reopen without new evidence

The following are closed/falsified:

- F9F8/FB6E adjacent-word 32-bit pointer reconstruction;
- canonical F9F8 descriptor `0x0F0000`;
- unconditional `+0x24 write == reselection` classification.

A later test may reopen a closed conclusion only if it produces contradictory canonical evidence.
