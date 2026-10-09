# TrueRecall — Authoritative Project State

This file is the single authoritative continuation state for the reverse-engineering / reconstruction workflow. When work resumes with `continua`, execute `NEXT` from this file unless new evidence requires a state revision.

## Active branch

```text
m09c-native-sequence-seam
```

Authoritative checkpoint at creation:

```text
0a164e55ecdb168fced6041afceac2527dc7a68d
Promote M09C static gate after CI roundtrip
```

Stable parent for the current player-presentation track:

```text
be6c632335ab451392859cf099c8c4bf353a104c
```

## Active milestone

```text
M0.9C — native player sequence integration seam
```

Goal: replace the M09B2 VBlank-driven diagnostic frame phase with authored player frames selected/progressed through the retail animation machinery while preserving the runtime visual-avatar descriptor identity and the linked player proxy/avatar model.

## DONE

- M08 proved authored sprite bytes can be scoped to the runtime visual avatar while Y is active and fall back cleanly when inactive.
- M09B2 proved a four-phase authored pixel sequence, cache namespace isolation, VRAM transfer and SAT rendering, but its frame progression is diagnostic and driven by `F712`, not actor animation state.
- The player-control / direction-family seam used by M07C is established and can select a dedicated alternate direction-table row.
- FDDC selector resolution is structurally confirmed to write the encoded animation entry to `object+0x24` and the current mapping-record offset to `object+0x20` using `object+0x2C` as descriptor identity.
- M09C distinguishes two facts that must not be conflated:
  - archetype 191 descriptor from the archetype table: `0x0E51FE`;
  - runtime-proven visual-avatar descriptor from M08/M09B2 renderer sweep: `0x0F0000`.
- `tools/rom_probe/m09c_native_sequence_seam_probe.py` is implemented.
- `tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py` is implemented.
- Historical `sprite_sequence_roundtrip_probe.py` has a shell-clean import path on the M09C branch.
- Static CI workflow `.github/workflows/m09c-static.yml` is operational.
- GitHub Actions run `37992816170` completed successfully on commit `cb60fdc5cf56ae9e39da5425b484a86f044a4d9d`.
- CI compiled all three M09/M09C probes and executed **10/10** static/synthetic tests successfully.
- Synthetic descriptor coverage proves the packed descriptor model where `descriptor+0x02` participates simultaneously in selector decoding and the group-0 graphics source pointer.
- Synthetic visual-frame round-trip proves `descriptor -> record -> pixels -> sequence compiler -> record/pixels` is lossless under the current compiler grid contract.
- BlastEm toolchain has been restored from GitHub Actions artifact `11643919770`; the artifact is recorded in `extracted_metadata/m09c_static_gate.json`.
- `extracted_metadata/m09c_static_gate.json` schema v2 is the static evidence record.

## EVIDENCE

Primary static evidence:

```text
extracted_metadata/m09c_static_gate.json
schema: truerecall.m09c.static_gate.v2
```

CI:

```text
workflow: m09c-static
run:      37992816170
result:   success
python:   3.12
probes:   py_compile PASS
unittest: 10 tests, 0 failures, 0 errors
```

BlastEm restoration:

```text
workflow run: 37989794952
artifact id:  11643919770
artifact:     blastem-linux-x86_64-6e5677969b59
artifact sha256: cfb240d0fef27b05865f21bb53b25125f29d081c8e2336d496b96f4c8586fe5f
```

Canonical ROM identity required by every canonical probe/build:

```text
size:  2,097,152 bytes
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

## OPEN

### O1 — canonical descriptor/family reconciliation

Pending execution of:

```text
tools/rom_probe/m09c_native_sequence_seam_probe.py
```

This must establish, from the canonical ROM, which player-facing selector families resolve validly against `0x0F0000` versus `0x0E51FE`, locate actual FDDC callers, enumerate reachable mapping records and identify storage candidates without assuming that `0xFF` filler is safe.

### O2 — canonical visual-avatar compiler round-trip

Pending execution of:

```text
tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py
```

Target: the JLLBFR family selected from direction-table base `0x00F2`, resolved through descriptor `0x0F0000`.

Required outcome: pixel-exact reconstruction plus exact mapping-record header preservation for every unique selector in that facing family.

### O3 — authored native selector/record path

Do not implement until O1 and O2 are green.

Preferred architecture:

```text
player Y/sprint state
→ retail direction-family selection
→ dedicated authored selector path
→ FDDC-compatible state resolution
→ object+0x24 / object+0x20
→ retail renderer
→ authored chunk source/cache namespace
```

Hard invariant:

```text
Do not replace object+0x2C for the controlled visual avatar.
```

If no safe mapping-record slot exists inside the descriptor-relative 16-bit record window, introduce the smallest possible resolver/renderer indirection rather than descriptor substitution.

### O4 — deterministic runtime regression

After O3 builds successfully:

- compare against the correct sprint parent, not blindly against retail;
- before activation: exact visual convergence to parent;
- Y held: avatar-local authored differences only;
- animation progression: native actor state, not `F712` phase bits;
- Y release: exact convergence to parent;
- control/movement: preserve M07 sprint behavior;
- linked `F9F8` / `FB6E` semantics unchanged;
- cache/VRAM/SAT budgets remain within established limits.

## BLOCKER

The only material blocker for O1/O2 is raw access to the canonical `True Lies (World)` ROM bytes. The ROM has existed in Library in prior sessions, but the current conversation surface does not expose a raw 2 MiB ROM file. BlastEm is no longer a blocker.

Do not reopen static helper work, descriptor synthetic tests, CI setup or BlastEm acquisition unless new evidence shows a regression.

## PARALLEL SCENE-AUTHORING TRACK

M11 scene-source work exists on separate branches and is not the active `NEXT` while M09C remains blocked at canonical player-presentation integration.

Known prepared work includes M11E scene-source matrix and later palette/v2 transaction experiments. These must not be promoted to canonical confirmation without running their SHA-1-locked probes against the canonical ROM.

Do not jump back to M11 merely because M09C is waiting on ROM bytes; doing so creates project-state drift. Only switch tracks deliberately and record that switch in this file.

## NEXT

1. Acquire raw access to the exact canonical 2 MiB ROM (`SHA-1 d39174...`).
2. Run `m09c_native_sequence_seam_probe.py`; persist its JSON under `extracted_metadata/`.
3. Run `m09c_visual_avatar_roundtrip_probe.py`; persist its JSON under `extracted_metadata/`.
4. If either fails, fix only the evidenced failure and rerun that gate. Do not broaden the investigation.
5. If both pass, select the safest authored selector/record integration seam while preserving `object+0x2C == 0x0F0000` for the visual avatar.
6. Implement one minimal native-sequence proof build.
7. Run deterministic BlastEm regression.
8. Persist output fingerprints/evidence and update this file.

## RETRY / ANTI-LOOP RULES

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- A closed gate is not reopened unless a later test contradicts it.
- `0xFF` bytes are storage candidates, never proof of free space.
- Runtime identity evidence outranks naming assumptions from static archetype classification.
- No milestone is promoted on source inspection alone when its completion criteria require canonical ROM or runtime execution.
- Prefer a small semantic commit for each material proof or correction.

## CONTINUATION FOOTER

```text
DONE     M09C static/synthetic gate confirmed; 10/10 CI; BlastEm restored.
EVIDENCE extracted_metadata/m09c_static_gate.json + Actions run 37992816170.
OPEN     canonical descriptor reconciliation + canonical 0x0F0000 round-trip.
NEXT     obtain raw canonical ROM bytes, run the two M09C canonical probes, then implement exactly one native selector/record proof.
```
