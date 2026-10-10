# TrueRecall — Recovery Pointer

This file exists so a clone that lands on the default `main` branch can find the live continuation without relying on old chat context or stale milestone text.

## Last reconciled active continuation

```text
active branch:       m09c-native-sequence-seam
technical checkpoint: e77565bd0a56bc807806f9a91d2e87af70ed89e6
active milestone:    M0.9C — native player sequence integration seam
```

The technical checkpoint identifies the proof state underlying the current recovery documents. It is **not** a permanent live HEAD; documentation and recovery-system commits may advance the branch.

## Required recovery path

1. Fetch/switch to `m09c-native-sequence-seam`.
2. Read `docs/RECOVERY_MANIFEST.json`.
3. Refresh the live branch HEAD.
4. Read `docs/PROJECT_STATE.md`.
5. Verify the canonical ROM if `NEXT` is ROM-dependent.
6. Execute `NEXT` from `docs/PROJECT_STATE.md`.

## Last reconciled technical state

Canonical runtime evidence corrected the M09C player identity model:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
native raw sprint deltas = 0,2,4,6,8,10
```

The old claim that `0x0F0000` is the canonical F9F8 descriptor is falsified; it remains only player-local visual-component evidence from M0.8.

At reconciliation time, the only material M0.9C completion gate was the deterministic full-game visual containment/fallback regression of the six-phase native build.

## Canonical ROM

```text
True Lies (World)
size  2,097,152 bytes
SHA-1 d39174bed46ede85531b86df7ba49123ce2f8411
```

ROM bytes are never committed and their availability is session-local.

If this pointer becomes stale, the internally consistent active-branch `docs/RECOVERY_MANIFEST.json` + `docs/PROJECT_STATE.md` pair is the technical authority. Repair this pointer before further handoff.
