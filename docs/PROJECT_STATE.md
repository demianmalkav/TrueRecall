# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh live branch HEAD before every write. The checkpoint below identifies the last material proof state; later documentation-only commits may advance HEAD.

## Active continuation

```text
branch:     m1.0b-post-rekall-apartment
milestone:  M1.0B — Post-Rekall apartment production source baseline
checkpoint: f2c8c5ac6e7d3b44608f6f56fa8207cb7e68ef3e
```

M0.9C, M0.9D and M1.0A are CLOSED. The player/native presentation seam, first Quaid production baseline and scene/player composition architecture are no longer active research gates.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed. ROM availability is session-local; verify size + SHA-1 before ROM-dependent work.

## Closed player baseline

Frozen M09D v9 contract:

```text
descriptor:             0x000A0000
native phases:          0,2,4,6,8,10
runtime facings:        8
authored facings:       N, NE, E, SE, S
native mirrors:         SW<-SE, W<-E, NW<-NE
unique mapping records: 10
reserved chunk slots:   24
used slots/phase:       17
max pieces/frame:       4
source art SHA-1:       94db7b28dca13720fd2656c37de4e57dc74d6dd4
ROM SHA-1:              eccbd54596c932ba3d7d2361af2437e59087b853
checksum:               0x7DCB
```

Evidence: `extracted_metadata/m09d_quaid_v9_candidate.json`. Pipeline and mapping contract remain frozen; later pixel polish is content revision unless contradictory engineering evidence appears.

## M1.0A integration baseline — CLOSED / CONFIRMED

M1.0A proved that the frozen M09D player layer and canonical M11D/M10 scene-authoring stack compose deterministically in one 4 MiB ROM.

Controlled scene-18 semantic mutation:

```text
C000 tile[0] = 1
health pickup type 54 @ (128,120), stride 6
world wall type 9 rect (64,64)..(80,256)
```

M11D component:

```text
SHA-1:    fac81fdc87b76a75c9b590d58707b16fcd6a5f04
checksum: 0x3E9A
allocation floor: 0x300000
```

Combined player+scene build:

```text
size:     4,194,304
SHA-1:    b96cfb9652a4c5dce7142fe0e03bfb1b257cc474
checksum: 0x5E8B
```

Exact byte-range accounting found **zero M09D/M11D intersections**. Scene-18 reparsing recovered exactly the authored tile, health object and world wall.

Runtime regression used M09D v9 as the correct logical parent while executing scene 0:

```text
44/44 captures pixel-identical
42 active Y+Left samples
all six native Quaid phases observed
0 runtime-state mismatches
F9F8 descriptor 0x000A0000 preserved
```

Primary evidence: `extracted_metadata/m1a_integration_baseline.json`.

M1.0A CI gate:

```text
Actions run:      38016506348
static tests:     61 / 61 PASS
BlastEm harness:  PASS
recovery doctor:  PASS
```

Deterministic composer: `tools/build/m1a_integration_baseline.py`.

## M1.0B production target — FROZEN

The first production vertical-slice sequence is **L2 — Post-Rekall escape / apartment**, matching the Level Bible's provisional film progression: post-Rekall agents/pursuit, contained apartment confrontation and a strong opportunity to prove Quaid-specific physical behavior without requiring later specialized systems such as disguise/scanner or vehicles.

The initial technical slot is **scene 18** because its canonical shape is especially clean for controlled conversion:

```text
map planes:      18 x 40 tiles
world grid:      9 x 20 cells
world records:   0
placements:      40
retail types:    only 114 and 115
record stride:   8 bytes
```

Scene 18 is therefore a production substrate, not narrative canon: its retail placements/content may be removed and replaced through source authoring while its known dimensions and scene lifecycle remain stable until evidence requires otherwise.

### Production design boundary

M1.0B should establish a playable **structural apartment/escape skeleton**, not finish all art/content. It should prove:

- editable scene source including palette data;
- authored room/corridor collision geometry;
- replacement of irrelevant retail placements with a deliberately small Total Recall encounter/objective set;
- frozen Quaid player layer intact;
- one distinct Earth/apartment palette direction;
- deterministic build, reparse and runtime entry into the authored scene.

Final tileset art, Lori-specific character art, bespoke melee/contact behavior, dialogue/cutscene polish and audio may remain later vertical-slice work after the structural source is green.

## Palette/source transaction decision

M11F/G/H are no longer treated as generic parallel distractions. Their architecture directly solves the next production requirement:

- M11F recovered editable 64-word gameplay CRAM palettes;
- M11G introduced versioned `scene_source.v2` with palette colors as source data;
- M11H composes scene resources first and allocates the authored palette **after the highest scene allocation**, preventing the `0x300000` collision that would occur if M11F were naively layered over M11D.

These implementations must be promoted into the active branch and revalidated against the now-accessible canonical ROM before being called production-stable. Do not independently recreate palette allocation logic.

## OPEN

### O1 — promote and canonically validate scene-source v2 transaction

Blocking. Port M11F palette authoring, M11G source-v2 and M11H transaction-v2 into this branch; run canonical 19-scene no-op/palette checks; prove palette allocation follows the scene allocation ledger and compose it with frozen M09D without overlap.

### O2 — Post-Rekall scene-18 structural source

Blocked by O1. Replace the retail scene-18 semantic payload with a first apartment/escape skeleton: room/corridor world geometry, deliberate placements, provisional map edits and Earth/apartment palette. Require exact reparse and runtime entry.

### O3 — vertical-slice encounter/mechanic layer

Blocked by O2. Add combat/objective pacing and one Quaid/film-specific interaction only after the structural source is runtime-stable.

## NEXT

1. Promote `scene_palette.py`, `scene_source_v2.py` and `scene_compiler_v2.py` plus their tests/probes from M11F/G/H into this branch without semantic rewrites.
2. Execute their canonical gates against SHA-1 `d39174...f8411`; persist real canonical fingerprints that the old branches could not obtain.
3. Extend the M1.0A composer so the v2 scene transaction and frozen M09D layer share one explicit allocation/range ledger; reject overlap.
4. Produce one scene-18 palette+map+object+world edit, reparse every authored component and run a runtime load proof.
5. Once green, begin the Post-Rekall apartment structural layout rather than returning to player-seam research.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- M09C, M09D and M1.0A reopen only on contradictory evidence.
- Do not create another palette/source schema if M11F/G/H can be promoted cleanly.
- Do not hand-place expanded resources; all allocations must be ledgered.
- Do not expand scene dimensions in v2 until the current immutable-dimension contract is intentionally superseded.
- Scene 18 is a production slot choice, not proof that its retail objects have useful Total Recall semantics.
- Generated ROMs/PNGs are outputs; source + manifests + verified base remain source truth.

## CONTINUATION FOOTER

```text
DONE     M09C/M09D closed; M1.0A player+scene composition closed with 61/61 CI and exact runtime regression.
EVIDENCE extracted_metadata/m1a_integration_baseline.json + Actions run 38016506348.
OPEN     canonical source-v2/palette transaction promotion for the Post-Rekall scene-18 production source.
NEXT     port M11F/G/H transaction stack, execute it against the canonical ROM, then author the first apartment/escape structural source.
```
