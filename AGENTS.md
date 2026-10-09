# AGENTS.md — TrueRecall operating contract

## Purpose

This repository reconstructs the True Lies (World) Mega Drive / Genesis engine and extends it into a new Total Recall game. Every agent must preserve reproducibility and distinguish evidence from inference.

## Non-negotiable rules

1. **Never commit the original True Lies ROM or copyrighted extracted asset dumps.**
2. Canonical base SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`.
3. Verify the base ROM before every extraction, patch or build.
4. Write ROM addresses in hexadecimal with `0x` prefix.
5. Every reverse-engineering claim is `CONFIRMED`, `HIGH CONFIDENCE` or `HYPOTHESIS`.
6. Never silently promote a hypothesis.
7. Important discoveries record evidence: offsets, RAM, code paths, runtime traces, extracted structures or reproducible probes.
8. Preserve retail behavior until a deliberate design decision replaces it.
9. New mechanics/assets/material edits must be isolated and regression-tested before integration.
10. Generated artifacts must be reproducible from source assets/tools plus the verified base ROM.
11. No hand-edited ROM is a source of truth.
12. Keep True Lies reconstruction facts separate from Total Recall design decisions.
13. Runtime evidence must compare against the correct logical parent build, not automatically against retail.
14. Do not regenerate unresolved spatial indexes/tables from guessed policies merely because record geometry is understood.

## Sources of truth

- Google Drive: project state, decisions, roadmap, next actions, recovery handoff, design bibles and checkpoints.
- GitHub: technical state, code, tools, probes, symbols, tests, build logic and reproducible patch data.

## Required recovery sequence

Before work in a fresh context:

1. Read Drive `START_HERE — True Recall`.
2. Read Drive `PROJECT_STATE_MASTER — True Recall`.
3. Read Drive `RECOVERY_HANDOFF — True Recall`.
4. Read Drive `NEXT_ACTIONS — True Recall`.
5. Read this file.
6. Read `docs/TECHNICAL_STATE.md`.
7. For current work read `docs/M09_SPRITE_SEQUENCE_AUTHORING.md` and/or `docs/M10_WORLD_COLLISION_AUTHORING.md`.
8. Refresh the active branch HEAD before changing code.

## Checkpoint discipline

A material milestone is not complete until these agree:

1. Drive project state.
2. GitHub technical state.
3. Stable Git checkpoint SHA.
4. Drive recovery handoff.
5. Evidence scope: static-only vs runtime-confirmed is explicit.

## Current project position

Completed: **M0.1–M0.8**.

Active/incomplete: **M0.9 — sprite sequence authoring/integration**.

Active: **M0.10 — world collision authoring**.

Latest runtime-confirmed collision step: **M0.10A — byte-identical world spatial resource relocation**.

Next collision proof: **M0.10B — controlled `world_type` 9→10 edit with existing grid membership preserved**.

Parallel animation proof: **M0.9C — authored sequence integration through the native `FDDC` progression seam without replacing player control/proxy descriptor semantics**.

Active technical branch: `m0.6c-level-stream`.

Refresh branch HEAD rather than trusting a SHA copied from an older handoff.

The Total Recall vertical slice begins only after player-art sequencing and at least one authored collision/material property are deterministic and regression-protected.
