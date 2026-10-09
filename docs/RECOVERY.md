# Recovery Procedure

Use this after context loss, model change or a long interruption.

## Read order

1. Drive: `START_HERE — True Recall`.
2. Drive: `PROJECT_STATE_MASTER — True Recall`.
3. Drive: `RECOVERY_HANDOFF — True Recall`.
4. Drive: `NEXT_ACTIONS — True Recall`.
5. Repository: `AGENTS.md`.
6. Repository: `docs/TECHNICAL_STATE.md`.
7. Current subsystem docs: `docs/M09_SPRITE_SEQUENCE_AUTHORING.md` and/or `docs/M10_WORLD_COLLISION_AUTHORING.md`.
8. Refresh `m0.6c-level-stream` HEAD before changing code.

## Before changing anything

- Verify local ROM SHA-1 = `d39174bed46ede85531b86df7ba49123ce2f8411`.
- Confirm the active branch rather than assuming `main` is current.
- Confirm the evidence scope of the subsystem: static-only, runtime-confirmed, or still hypothesis/high-confidence.
- Re-run the relevant build/probe/regression before extending it.
- Compare runtime changes against the correct logical parent build.

## Current recovery anchor

Project state:

- M0.1–M0.8 complete.
- M0.9 active/integration-in-progress.
- M0.10 active; M0.10A runtime-confirmed.
- Vertical slice not started.

Primary branch: `m0.6c-level-stream`.

The checkpoint before the documentation-sync commits was:

`0f6a97a2f2cf0d6525da7696f8469f84565e92d2`

Refresh HEAD because documentation synchronization itself advances the branch.

Current next proofs:

- M0.10B: controlled `world_type 9 → 10` edit with grid membership/geometry preserved, followed by projectile-behavior runtime validation.
- M0.9C: native authored animation-sequence integration through `FDDC` while preserving player avatar/proxy control-descriptor semantics.

Do not regenerate the world broadphase grid from rectangle overlap alone; the retail priority/pruning policy is not fully recovered.

## Handoff update rule

At the end of substantial work, synchronize:

- Drive project state
- Drive next actions
- Drive recovery handoff
- GitHub technical state
- subsystem documentation
- active branch SHA
- exact evidence scope and audited output ROM hash when applicable

A new chat should be able to recover the project without the old transcript.
