# TrueRecall

TrueRecall is the engineering and design repository for a Sega Mega Drive / Genesis game based on the 1990 film **Total Recall**, using the **True Lies (World)** engine as a reverse-engineered technical foundation.

## Project model

- **Google Drive** is the project-control source of truth: status, roadmap, decisions, recovery handoff, design bibles, references and checkpoints.
- **GitHub** is the technical source of truth: reverse-engineering documentation, tools, symbols, tests, build logic and patch data.
- The original copyrighted ROM is never committed to this repository.

## Canonical base ROM

`True Lies (World)`

- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`

All tooling must verify the base ROM before modifying or extracting data.

## Current milestone

Reverse engineering has reached **M0.5 — map format recovered**. The next active milestone is **M0.6 — player state machine recovery**, followed by **M0.7 — first controlled engine extension**.

See `AGENTS.md` and `docs/TECHNICAL_STATE.md` before modifying the project.
