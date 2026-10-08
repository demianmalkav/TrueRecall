# AGENTS.md — TrueRecall operating contract

## Purpose

This repository reconstructs the True Lies (World) Mega Drive / Genesis engine and extends it into a new Total Recall game. Every agent must preserve reproducibility and distinguish evidence from inference.

## Non-negotiable rules

1. **Never commit the original True Lies ROM or copyrighted extracted asset dumps.**
2. The canonical base ROM is identified by SHA-1 `d39174bed46ede85531b86df7ba49123ce2f8411`.
3. Verify the base ROM before every extraction, patch or build operation.
4. ROM addresses are written in hexadecimal with `0x` prefix.
5. Every reverse-engineering claim must carry one of these states:
   - `CONFIRMED`: reproduced directly from ROM/runtime evidence.
   - `HIGH CONFIDENCE`: multiple consistent observations, but not fully proven.
   - `HYPOTHESIS`: useful interpretation still requiring a probe.
6. Never silently promote a hypothesis to confirmed knowledge.
7. Every important discovery must record the evidence that supports it: ROM offsets, RAM addresses, code paths, observed behavior, cheat correlation, extracted structure or runtime trace.
8. Preserve original behavior until a deliberate design decision replaces it.
9. New mechanics must be isolated and regression-tested before integration.
10. Generated artifacts must be reproducible from source assets, tools and the verified base ROM.
11. No single hand-edited ROM is a source of truth.
12. Keep reverse-engineering facts separate from Total Recall creative decisions.

## Sources of truth

- Google Drive: project state, decisions, roadmap, recovery handoff, design bibles, references and checkpoints.
- GitHub: technical state, code, tools, symbols, tests, build logic and reproducible patch data.

## Required recovery sequence

Before starting work in a fresh context:

1. Read Drive `START_HERE — True Recall`.
2. Read Drive `PROJECT_STATE_MASTER — True Recall`.
3. Read Drive `RECOVERY_HANDOFF — True Recall`.
4. Read this file.
5. Read `docs/TECHNICAL_STATE.md`.
6. Read the subsystem document relevant to the task.
7. Check the current `main` head and last stable checkpoint before changing code.

## Checkpoint discipline

A milestone is not complete until all four are updated:

1. Drive project state.
2. GitHub technical state.
3. Stable Git commit/tag or explicitly recorded commit SHA.
4. Drive recovery handoff.

## Current milestone

Completed: **M0.5 — map format recovered**.

Active: **M0.6 — player state machine recovery**.

Next: **M0.7 — first controlled engine extension**.
