# AGENTS.md — TrueRecall bootstrap contract

## Purpose

`main` is not guaranteed to contain the live technical continuation. Its job is to provide a safe recovery entrypoint.

## Before technical work

1. Read `RECOVERY_POINTER.md` on `main`.
2. Fetch/switch to the active branch named there.
3. Read that branch's `docs/RECOVERY_MANIFEST.json`.
4. Refresh the live active-branch HEAD.
5. Read `docs/PROJECT_STATE.md`.
6. Read the active branch's `AGENTS.md` for the full operating contract.
7. Verify the canonical ROM before any ROM-dependent operation.

Do not resume from milestone statements embedded in older `main` documents.

## Non-negotiable bootstrap invariants

- Never commit the original True Lies ROM or copyrighted extracted asset dumps.
- Canonical base SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`.
- No hand-edited ROM is a source of truth.
- Do not silently promote hypotheses or revive falsified models.
- Technical continuation authority lives in the active branch's `docs/PROJECT_STATE.md` and `docs/RECOVERY_MANIFEST.json`.
- Google Drive provides project/design continuity and a redundant recovery mirror; it does not override the active GitHub project state.

If the recovery pointer and active-branch manifest disagree, inspect branch history and treat the active branch's internally consistent `PROJECT_STATE.md` + manifest pair as the stronger technical evidence; repair the bootstrap pointer before continuing work.
