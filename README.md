# TrueRecall

TrueRecall is the engineering and design repository for a Sega Mega Drive / Genesis game based on the 1990 film **Total Recall**, using **True Lies (World)** as a reverse-engineered technical foundation.

## IMPORTANT — `main` is a recovery/bootstrap branch

Do **not** infer the current engineering milestone from the files on `main` and do not begin new technical work here merely because it is the repository default branch.

The live continuation state is maintained on the branch named by `RECOVERY_POINTER.md`. At the last reconciliation snapshot that branch is:

```text
m09c-native-sequence-seam
```

Fresh-context procedure:

1. Read `RECOVERY_POINTER.md` on `main`.
2. Fetch/switch to the active branch named there.
3. Read that branch's `docs/RECOVERY_MANIFEST.json`.
4. Refresh the live active-branch HEAD.
5. Read `docs/PROJECT_STATE.md` and execute its `NEXT`.
6. Read `AGENTS.md` and `docs/TECHNICAL_STATE.md` for operating rules and cumulative background.
7. Locate/provide and verify the canonical ROM before ROM-dependent work.

If any older file on `main` describes M0.5/M0.6 as current, treat it as historical repository content rather than continuation authority.

## Canonical base ROM

`True Lies (World)`

- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`

The original ROM and copyrighted extracted asset dumps are never committed. ROM availability is session-local and must be re-established in a fresh environment.

## Source-of-truth model

- Active-branch `docs/PROJECT_STATE.md`: human-readable continuation authority.
- Active-branch `docs/RECOVERY_MANIFEST.json`: machine-readable continuation authority.
- Active-branch `docs/TECHNICAL_STATE.md`: cumulative technical compendium.
- Google Drive: project/design continuity, decisions, bibles and redundant recovery mirrors.
- Old chat transcripts and superseded milestone documents: historical context only.

No code from the active experimental branch is merged into `main` merely to make this bootstrap current; `main` points safely to the branch that owns the actual work.
