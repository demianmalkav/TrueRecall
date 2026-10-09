# TrueRecall — Recovery Procedure

Use this after context loss, model change, long interruption or a handoff to another agent.

The objective is not to reconstruct project state from chat memory. The repository must be sufficient to identify the active branch, technical checkpoint, open gate and exact `NEXT`.

## Authority

- Human continuation state: `docs/PROJECT_STATE.md`.
- Machine continuation state: `docs/RECOVERY_MANIFEST.json`.
- Cumulative technical background: `docs/TECHNICAL_STATE.md`.
- Operating rules: `AGENTS.md`.

If another document conflicts with `PROJECT_STATE.md` about current branch/milestone/`NEXT`, that other document is stale or historical.

## Fresh-context read order

1. Obtain repository access.
2. Read `docs/RECOVERY_MANIFEST.json` to identify the active branch and checkpoint basis.
3. Refresh the live active branch HEAD; do not assume `main` is current.
4. Read `docs/PROJECT_STATE.md` from that branch.
5. Read `AGENTS.md`.
6. Read `docs/TECHNICAL_STATE.md` for cumulative engine knowledge.
7. Read only the current subsystem documents referenced by `PROJECT_STATE.md`.
8. Consult Drive `START_HERE`, `PROJECT_STATE_MASTER`, `RECOVERY_HANDOFF` and design bibles for project/design continuity; their dynamic technical state must defer to GitHub `PROJECT_STATE.md`.

## Canonical ROM gate

Before any ROM-dependent work, locate/provide the base ROM and verify:

```text
title: True Lies (World)
size:  2,097,152 bytes
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

Never infer ROM availability from an earlier session. The original ROM is not repository state and is never committed.

## Recovery validation checklist

A fresh context is recovered only when it can answer all of the following from repository/Drive artifacts without old chat history:

- What is the active branch?
- What technical checkpoint underlies the current state?
- What milestone is active?
- Which claims are confirmed vs historical/falsified?
- Which exact evidence files support the current gate?
- Which tools are authoritative now?
- Which tools are historical only?
- What is the logical parent build for the next runtime comparison?
- What remains OPEN?
- What exact sequence is `NEXT`?

If any answer requires guessing, recovery is incomplete; repair documentation before extending code.

## Current checkpoint pointer

Do not duplicate current technical details here. Resolve them from:

```text
docs/RECOVERY_MANIFEST.json
docs/PROJECT_STATE.md
```

At the documentation reconciliation that introduced this procedure, the active continuation is M0.9C on `m09c-native-sequence-seam`, based on technical checkpoint `e77565bd0a56bc807806f9a91d2e87af70ed89e6`. This sentence is only a recovery pointer; `PROJECT_STATE.md` remains authoritative if the project has advanced.

## Historical-state handling

Old probes/docs are not deleted merely because their interpretation was superseded. They preserve provenance and may explain why a design changed.

However:

- files marked `HISTORICAL` are not promotion gates;
- claims marked `FALSIFIED` cannot be revived without new contradictory evidence;
- old chat instructions never outrank persisted runtime evidence;
- v1 tooling output known to contain a reconstruction error is evidence of the tooling failure, not evidence of engine behavior.

## Handoff update rule

After a material advance that changes continuation state:

1. commit evidence/tooling;
2. update `docs/PROJECT_STATE.md`;
3. update `docs/RECOVERY_MANIFEST.json`;
4. update the affected subsystem document or mark the superseded one historical;
5. update `docs/TECHNICAL_STATE.md` when cumulative engine knowledge changed;
6. synchronize Drive recovery pointers;
7. record the technical checkpoint commit, evidence scope, logical parent and audited output hash where applicable.

Do not embed a supposedly permanent live HEAD in multiple documents. Documentation commits themselves advance HEAD; fresh recovery must resolve the live branch while using the recorded technical checkpoint as the proof anchor.

## Recovery success criterion

A new chat should be able to receive repository + Drive access + the verified canonical ROM and continue the exact current `NEXT` without reading the lost transcript.
