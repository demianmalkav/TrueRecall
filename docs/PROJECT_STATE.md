# TrueRecall — Authoritative Project State

This file is the single authoritative continuation state for the reverse-engineering / reconstruction workflow. When work resumes with `continua`, execute `NEXT` from this file unless new evidence requires a state revision.

## Active branch

```text
m09c-native-sequence-seam
```

Authoritative checkpoint:

```text
d5ecf079b3d773cb7852f5b8fce71b93b047ea6b
Promote M09C static gate to v3
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
- `tools/rom_probe/m09c_canonical_gate.py` is implemented as the one-shot canonical gate runner.
- Historical `sprite_sequence_roundtrip_probe.py` has a shell-clean import path on the M09C branch.
- Static CI workflow `.github/workflows/m09c-static.yml` is operational.
- GitHub Actions run `37993521291` completed successfully on commit `fe5c6edc2958012ac9a46eac3626eec3bc3c601f`.
- CI compiled all four M09/M09C probes/gates and executed **16/16** static/synthetic tests successfully.
- Synthetic descriptor coverage proves the packed descriptor model where `descriptor+0x02` participates simultaneously in selector decoding and the group-0 graphics source pointer.
- Synthetic visual-frame round-trip proves `descriptor -> record -> pixels -> sequence compiler -> record/pixels` is lossless under the current compiler grid contract.
- Canonical promotion guardrails reject wrong descriptor identity, incomplete JLLBFR resolution, non-pixel-exact output, selector/frame count disagreement and base-ROM SHA mismatch.
- BlastEm toolchain has been restored from GitHub Actions artifact `11643919770`.
- `extracted_metadata/m09c_static_gate.json` schema v3 is the current static evidence record.
- The Library entry `/Total Recall Sega/True Lies (World).md` has been located and reports the exact canonical size `2,097,152` bytes.
- Raw materialization of that Library entry remains denied by the current Project authorization path.

## EVIDENCE

Primary static evidence:

```text
extracted_metadata/m09c_static_gate.json
schema: truerecall.m09c.static_gate.v3
```

Latest CI:

```text
workflow: m09c-static
run:      37993521291
job:      114033538700
result:   success
python:   3.12
compile:  PASS
unittest: 16 tests, 0 failures, 0 errors
```

Canonical gate runner:

```text
tools/rom_probe/m09c_canonical_gate.py
```

It verifies the ROM identity, runs Gate 1 and Gate 2 in order, validates both report schemas/identities/invariants and emits:

```text
extracted_metadata/m09c_native_sequence_seam.json
extracted_metadata/m09c_visual_avatar_roundtrip.json
extracted_metadata/m09c_canonical_gate.json
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

Library locator:

```text
/Total Recall Sega/True Lies (World).md
registered size: 2,097,152 bytes
raw materialization: blocked by current Project authorization
```

## OPEN

### O1 — one-shot canonical M09C gate

Pending execution of:

```text
python tools/rom_probe/m09c_canonical_gate.py <canonical_rom>
```

The runner serializes:

1. descriptor/family reconciliation through `m09c_native_sequence_seam_probe.py`;
2. canonical visual-avatar compiler round-trip through `m09c_visual_avatar_roundtrip_probe.py`;
3. report-level promotion checks;
4. emission of a single canonical PASS checkpoint only if every required invariant holds.

### O2 — authored native selector/record path

Do not implement until O1 is green.

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

### O3 — deterministic runtime regression

After O2 builds successfully:

- compare against the correct sprint parent, not blindly against retail;
- before activation: exact visual convergence to parent;
- Y held: avatar-local authored differences only;
- animation progression: native actor state, not `F712` phase bits;
- Y release: exact convergence to parent;
- control/movement: preserve M07 sprint behavior;
- linked `F9F8` / `FB6E` semantics unchanged;
- cache/VRAM/SAT budgets remain within established limits.

## BLOCKER

The only material blocker for O1 is raw access to the canonical `True Lies (World)` ROM bytes.

The Library entry has been positively located and has the exact canonical size, but `files.materialize` currently returns:

```text
This Project file does not have an authorized raw-byte materialization path.
```

The generated `true_lies_re_v0.3.zip` is blocked by the same authorization rule. BlastEm is no longer a blocker.

Do not reopen static helper work, descriptor synthetic tests, CI setup, canonical-gate orchestration or BlastEm acquisition unless new evidence shows a regression.

## PARALLEL SCENE-AUTHORING TRACK

M11 scene-source work exists on separate branches and is not the active `NEXT` while M09C remains blocked at canonical player-presentation integration.

Known prepared work includes M11E scene-source matrix and later palette/v2 transaction experiments. These must not be promoted to canonical confirmation without running their SHA-1-locked probes against the canonical ROM.

Do not jump back to M11 merely because M09C is waiting on ROM bytes; doing so creates project-state drift. Only switch tracks deliberately and record that switch in this file.

## NEXT

1. Obtain an authorized raw-byte copy of the exact canonical 2 MiB ROM (`SHA-1 d39174...`) in the current conversation/container.
2. Execute exactly one command path: `m09c_canonical_gate.py`.
3. If the gate fails, fix only the evidenced failing invariant and rerun the one-shot gate. Do not broaden the investigation.
4. If the gate passes, inspect its canonical native report and select the safest non-overlapping authored selector/record seam while preserving `object+0x2C == 0x0F0000`.
5. Implement one minimal native-sequence proof build.
6. Run deterministic BlastEm regression.
7. Persist output fingerprints/evidence and update this file.

## RETRY / ANTI-LOOP RULES

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- A closed gate is not reopened unless a later test contradicts it.
- `0xFF` bytes are storage candidates, never proof of free space.
- Runtime identity evidence outranks naming assumptions from static archetype classification.
- No milestone is promoted on source inspection alone when its completion criteria require canonical ROM or runtime execution.
- Prefer a small semantic commit for each material proof or correction.

## CONTINUATION FOOTER

```text
DONE     M09C static/synthetic/orchestration gate confirmed; 16/16 CI; BlastEm restored.
EVIDENCE extracted_metadata/m09c_static_gate.json v3 + Actions run 37993521291.
OPEN     one-shot canonical M09C gate, then native authored selector/record proof.
NEXT     materialize canonical ROM bytes and run m09c_canonical_gate.py exactly once.
```
