# TrueRecall

TrueRecall is the engineering and design repository for a Sega Mega Drive / Genesis game based on the 1990 film **Total Recall**, using **True Lies (World)** as a reverse-engineered technical foundation.

## Do not infer current state from this README

Dynamic continuation state has exactly two authorities:

- human-readable: `docs/PROJECT_STATE.md`
- machine-readable: `docs/RECOVERY_MANIFEST.json`

`README.md`, old handoffs and milestone documents provide orientation/history only. They must not override `PROJECT_STATE.md` when choosing what to do next.

## Project model

- **GitHub** owns technical truth: reverse-engineering evidence, tools, probes, build logic, tests, runtime regressions and reproducible authoring data.
- **Google Drive** owns project/design continuity: roadmap, decisions, design bibles and recovery pointers.
- Dynamic state duplicated in Drive must defer to GitHub `docs/PROJECT_STATE.md`.
- The original copyrighted ROM and extracted copyrighted asset dumps are never committed.

## Canonical base ROM

`True Lies (World)`

- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`

ROM availability is session-local. Every ROM-dependent tool must verify the base before extraction, patching or builds.

## Current continuation snapshot

At the documentation reconciliation checkpoint:

```text
active branch: m09c-native-sequence-seam
active milestone: M0.9C
technical checkpoint: e77565bd0a56bc807806f9a91d2e87af70ed89e6
```

M0.9C has recovered the canonical F9F8/FB6E word-pointer model, F9F8 descriptor `0x000A0000`, the native phase bridge at `0x009D5E`, and the six native sprint deltas `0,2,4,6,8,10`. The six-bank native-phase proof builder exists; 12/12 trampoline executions and 42/42 CI tests pass.

The only material M09C completion gate is the deterministic full-game visual containment/fallback regression. Read `docs/PROJECT_STATE.md` for exact current evidence and `NEXT`.

Parallel M11 scene-authoring work is preserved on separate branches and is not the active next task unless `PROJECT_STATE.md` explicitly changes tracks.

## Fresh-context recovery

1. Refresh the live `m09c-native-sequence-seam` HEAD.
2. Read `docs/RECOVERY_MANIFEST.json`.
3. Read `docs/PROJECT_STATE.md`.
4. Read `AGENTS.md`.
5. Use `docs/TECHNICAL_STATE.md` for cumulative background, not for choosing `NEXT`.
6. Verify the canonical ROM if the next action is ROM-dependent.
7. Execute `NEXT` from `docs/PROJECT_STATE.md`.

Detailed disaster-recovery rules live in `docs/RECOVERY.md`.
