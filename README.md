# TrueRecall

TrueRecall is the engineering and design repository for a Sega Mega Drive / Genesis game based on the 1990 film **Total Recall**, using **True Lies (World)** as a reverse-engineered technical foundation.

## Project model

- **Google Drive** is the project-control source of truth: status, roadmap, next actions, decisions, recovery handoff and design bibles.
- **GitHub** is the technical source of truth: reverse-engineering evidence, tools, probes, build logic, runtime regression and reproducible patch/authoring data.
- The original copyrighted ROM and extracted copyrighted assets are never committed.

## Canonical base ROM

`True Lies (World)`

- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`

All tools must verify the base ROM before extraction, patching or builds.

## Current state

Completed through **M0.8**, including a runtime-validated held-Y sprint and runtime-visible authored avatar graphics.

Two authoring tracks are active:

- **M0.9 — sprite sequence authoring:** multi-frame source compilation, global 16×16 chunk deduplication, pixel-exact round-trip and a stable four-phase runtime authored-pixel path are proven. Native `FDDC`-driven authored sequence integration remains open.
- **M0.10 — world collision authoring:** **M0.10A is runtime-confirmed**. Scene-0 world spatial/collision data can be relocated to expanded ROM with 13/13 pixel-identical gameplay screenshots. M0.10B is the next controlled material/type edit.

Active technical branch: `m0.6c-level-stream`.

Current checkpoint: `0f6a97a2f2cf0d6525da7696f8469f84565e92d2`.

Before changing anything, read `AGENTS.md`, `docs/TECHNICAL_STATE.md`, `docs/M09_SPRITE_SEQUENCE_AUTHORING.md` and `docs/M10_WORLD_COLLISION_AUTHORING.md`.
