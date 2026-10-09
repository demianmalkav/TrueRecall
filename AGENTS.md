# AGENTS.md — TrueRecall operating contract

## Purpose

This repository reconstructs the True Lies (World) Mega Drive / Genesis engine and extends it into a new Total Recall game. Every agent must preserve reproducibility, distinguish evidence from inference and recover project state without relying on prior chat context.

## Non-negotiable rules

1. **Never commit the original True Lies ROM or copyrighted extracted asset dumps.**
2. Canonical base SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`.
3. Verify base ROM size + SHA-1 before every ROM-dependent extraction, patch or build.
4. Write ROM addresses in hexadecimal with `0x` prefix.
5. Every reverse-engineering claim is `CONFIRMED`, `HIGH CONFIDENCE` or `HYPOTHESIS` unless explicitly marked `FALSIFIED/HISTORICAL`.
6. Never silently promote a hypothesis or revive a falsified model without new evidence.
7. Important discoveries record evidence: offsets, RAM, code paths, runtime traces, extracted structures or reproducible probes.
8. Preserve retail behavior until a deliberate design decision replaces it.
9. New mechanics/assets/material edits must be isolated and regression-tested before integration.
10. Generated artifacts must be reproducible from source assets/tools plus the verified base ROM.
11. No hand-edited ROM is a source of truth.
12. Keep True Lies reconstruction facts separate from Total Recall design decisions.
13. Runtime evidence must compare against the correct logical parent build, not automatically against retail.
14. Do not regenerate unresolved indexes/tables from guessed policies merely because record geometry is understood.
15. Maximum two implementation retries for the same failing hypothesis without new evidence.
16. A closed gate reopens only when later evidence contradicts it.

## Authority hierarchy

Dynamic project state is not duplicated here.

1. `docs/PROJECT_STATE.md` — authoritative human-readable continuation state and `NEXT`.
2. `docs/RECOVERY_MANIFEST.json` — authoritative machine-readable recovery state.
3. `docs/TECHNICAL_STATE.md` — cumulative technical compendium.
4. subsystem/milestone documents — local technical history and evidence.
5. Drive — project/design continuity and recovery pointers; any duplicated dynamic technical state must defer to `docs/PROJECT_STATE.md`.
6. old chat transcripts — historical context only.

If two documents disagree about active branch, milestone or `NEXT`, follow `docs/PROJECT_STATE.md` and record the contradiction for cleanup.

## Required fresh-context recovery sequence

1. Determine the live branch named by `docs/RECOVERY_MANIFEST.json`; never assume `main` is current.
2. Refresh that branch HEAD.
3. Read `docs/RECOVERY_MANIFEST.json`.
4. Read `docs/PROJECT_STATE.md`.
5. Read this file.
6. Read `docs/TECHNICAL_STATE.md` only as cumulative background.
7. Read only the subsystem documents referenced by current `PROJECT_STATE.md`.
8. Locate/provide and verify the canonical ROM before ROM-dependent work.
9. Execute `NEXT` from `docs/PROJECT_STATE.md`.

## Evidence discipline

Use these labels deliberately:

- `CONFIRMED`: directly supported by repeatable static/runtime evidence.
- `HIGH CONFIDENCE`: strong convergent evidence but not yet fully runtime-closed.
- `HYPOTHESIS`: plausible interpretation awaiting proof.
- `FALSIFIED`: contradicted by stronger evidence; retained only for provenance when useful.
- `HISTORICAL`: once-valid workflow/probe that no longer defines the current promotion gate.

Runtime identity evidence outranks static naming assumptions. Canonical runtime evidence outranks conclusions inferred from diagnostic builds.

## Checkpoint discipline

A material advance is complete only when:

- technical evidence/tooling is committed;
- evidence scope is explicit;
- `docs/PROJECT_STATE.md` is updated;
- `docs/RECOVERY_MANIFEST.json` agrees;
- the relevant subsystem document is updated or marked historical;
- Drive recovery pointers are synchronized when the advance changes project continuation;
- the logical parent build and audited output hash are recorded when applicable.

Do not write a permanently embedded "current HEAD" that becomes self-invalidating on every documentation commit. Record a technical checkpoint commit and require fresh contexts to resolve the live branch HEAD.

## Current position

Do **not** maintain current milestone details in this file. Read `docs/PROJECT_STATE.md`.
