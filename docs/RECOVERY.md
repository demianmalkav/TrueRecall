# Recovery Procedure

Use this when resuming after context loss, model change or a long interruption.

## Read order

1. Drive: `START_HERE — True Recall`.
2. Drive: `PROJECT_STATE_MASTER — True Recall`.
3. Drive: `RECOVERY_HANDOFF — True Recall`.
4. Repository: `AGENTS.md`.
5. Repository: `docs/TECHNICAL_STATE.md`.
6. Read the subsystem document relevant to the next task.
7. Inspect `main` HEAD and the latest recorded checkpoint.

## Before changing anything

- Verify the local ROM SHA-1 equals `d39174bed46ede85531b86df7ba49123ce2f8411`.
- Confirm which milestone is active.
- Confirm whether each relevant claim is CONFIRMED, HIGH CONFIDENCE or HYPOTHESIS.
- Re-run the existing probe/test for the subsystem being touched.

## Handoff update rule

At the end of a substantial work session, update:

- Drive project state
- Drive next actions
- Drive recovery handoff
- GitHub technical state
- subsystem documentation
- stable commit/checkpoint reference

A new chat should not need the old chat transcript to reconstruct project state.
