# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. Closed gates reopen only on contradictory evidence.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M1.1A — canonical palette + scene-source-v2 promotion
checkpoint: 0942f0d9ef58a37c37c19d9da9a5e8caa37d92d0
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE and FROZEN.**

**M1.0A/B is COMPLETE.** The first Total Recall integration baseline now proves that the frozen Quaid player, declarative persistent objects and authored world collision coexist in one reproducible gameplay scene and behave correctly at runtime.

The active task is M1.1A: promote the preserved M11F/M11G/M11H palette + scene-source-v2 work onto the current branch, execute it against the canonical ROM now available in raw form, and integrate it with the closed M1.0 scene0 baseline without reopening player/control/object/collision gates.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed. Generated builds remain reproducible from source/manifests plus this verified base.

## Stable engine foundation

Stable and closed unless contradictory evidence appears:

- M0.1–M0.6 ROM/entity/VM/map/authoring reconstruction;
- M0.7 deterministic held-Y sprint;
- M0.8 runtime-authored player-local graphics;
- M0.9C native six-phase player presentation;
- M0.9D frozen production Quaid sprint family;
- M0.10 world-collision authoring;
- M0.11A–D canonical scene-source authoring;
- M1.0A/B player + object + collision integration baseline.

## M0.9D production player — CLOSED / FROZEN

```text
source fingerprint: da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA-1:       49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum:          0x266C
F9F8 descriptor:   0x000A0000
native phases:     0,2,4,6,8,10
```

Evidence:

`extracted_metadata/m09d_quaid_v11_production_freeze.json`

Do not edit v11 player pixels or mapping geometry during M1.1.

## M1.0A static integration — COMPLETE / CONFIRMED

Scene 18 was initially selected because it had a sparse static world-collision baseline. Runtime evidence later showed that scene18 follows a scripted/non-normal player-control path: distinct directional inputs produced the same scripted trajectory. That is new evidence and formally retires scene18 as the vertical-slice gameplay sandbox.

The active integration sandbox is **scene 0**, already used by the deterministic player/runtime harness.

Source manifest:

`tools/build/examples/m100a_scene0_baseline.json`

Authored additions:

```text
shotgun pickup: type 69, stride 6, x=690, y=558
world wall:     type 9, rect=[668,540,676,580]
```

Compositor:

`tools/build/m100a_vertical_slice_baseline.py`

Static scene-only parent:

```text
SHA-1:   fe2d8f7bbffba42379aa72d697b91364f9734c96
checksum: 0xA5D8
```

Integrated M1.0A candidate:

```text
size:     4,194,304 bytes
SHA-1:    84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027
checksum: 0x6E6A
direct parent: 49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
```

Containment proof:

- frozen v11 phase banks remain byte-exact;
- scene/object/world deltas are preserved exactly;
- player and scene deltas have no incompatible overlap;
- the only shared non-checksum byte is the identical 4 MiB ROM-end header byte;
- final checksum is recomputed once after composition.

Evidence:

`extracted_metadata/m100a_vertical_slice_baseline.json`

## M1.0B runtime integration — COMPLETE / CONFIRMED

Runner:

`tools/runtime/m100b_vertical_slice_runtime.py`

Verified CI snapshot:

```text
commit:          e88ffe045d339e43a95de60b8df32fd5ab553c74
Actions run:     38053439943
artifact id:     11670751788
artifact SHA256: 177a35bfb755f2eea7985d8ff8a61c5c601e974e35f903bc1ec03c7a14d7c5cf
static:          PASS
BlastEm harness: PASS
```

Runtime comparison uses frozen v11 as the direct parent and the exact M1.0A candidate as child.

Confirmed behavior under 30 frames of normalized `Y+Left = 0x2044`:

```text
spawn, both:     x=701 y=558
parent final:    x=652 y=558, ownership=0x01, shotgun ammo=0
candidate final: x=688 y=558, ownership=0x03, shotgun ammo=5
```

Interpretation:

- the authored type-69 pickup grants the shotgun ownership bit and five shells only in the candidate;
- the authored type-9 wall blocks the candidate at player-center x=688;
- the direct parent crosses the authored wall zone and reaches x=652;
- F9F8 remains `FFC632` and retains descriptor `0x000A0000`;
- adding the pickup shifts FB6E from `FFC7FA` to `FFC86C`, but the proxy retains exact semantic type/state/mapping/facing/descriptor fields (`type 1`, descriptor `0x000F0000`), so raw slot-address equality is deliberately not an invariant;
- all 14 runtime assertions pass.

Evidence:

`extracted_metadata/m100b_vertical_slice_runtime.json`

## Why M1.1A is now justified

M11D is sufficient for map words, persistent objects and world collision, but it intentionally treats palette identity as immutable metadata and does not provide a production source-level palette transaction. A real Total Recall environment needs authored color language before a Mars/industrial art pass can be evaluated.

Preserved branches provide the minimum next layer:

```text
m11f-palette-authoring     scene_palette.v1 + CRAM relocation/validation
m11g-scene-source-v2      versioned source schema with explicit colors[64]
m11h-scene-transaction-v2 one allocation ledger for maps/objects/world/palette
```

Those branches were left at static/synthetic status only because raw canonical ROM access was unavailable. That blocker is now closed. This is the recorded evidence-based reason to promote their minimal functionality onto the current branch.

M1.1A does **not** yet authorize new tile graphics. Palette authoring is isolated first; tile-graphics authoring becomes the next gate only after palette transactions are canonical- and runtime-confirmed.

## OPEN

### O1 — port minimal M11F/G/H authoring layer

Bring only the palette/source-v2/transaction-v2 modules, probes and tests required for canonical palette transactions onto the active branch. Do not merge historical project-state files or unrelated branch changes.

### O2 — canonical execution

Against the verified 2 MiB ROM:

- validate 19/19 retail palettes;
- require 19/19 palette no-op compiles to exact retail bytes;
- execute source-v2 exact no-op;
- execute one deterministic scene0 palette edit through the single v2 transaction arena;
- pin output SHA-1/checksum only after successful execution.

### O3 — integrate palette transaction with M1.0 baseline

Compose or lower the palette transaction into the closed M1.0 scene0 build without changing v11 player banks, pickup semantics or wall behavior. Allocation overlap must be mechanically impossible or rejected.

### O4 — runtime palette confirmation

Boot the palette-authored M1.1 candidate under pinned BlastEm, confirm the expected CRAM/palette change is actually loaded, and rerun the M1.0B pickup/wall/control invariants.

## NEXT

1. Copy the minimal M11F `scene_palette.py` + tests/probe from `m11f-palette-authoring` onto the active branch.
2. Copy the M11G `scene_source_v2.py` semantic migration layer and static tests.
3. Copy M11H `scene_compiler_v2.py` + canonical transaction probe/tests, preserving M11D/v1 unchanged.
4. Run all imported static suites on the active branch.
5. Execute the M11F canonical 19-scene palette probe against SHA-1 `d39174...f8411` and persist evidence.
6. Execute a scene0 source-v2 palette transaction, then integrate it with M1.0A and prove no overlap with the frozen player/object/collision resources.
7. Runtime-confirm CRAM/presentation plus all closed M1.0B invariants.
8. If green, mark M1.1A complete and open the tile-graphics authoring gate.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0 gates reopen only on contradictory evidence.
- Do not modify v11 player pixels during M1.1.
- Keep `scene_source.v1` readable and unchanged as a regression anchor.
- Do not merge whole M11F/G/H branches; port the minimum proven files deliberately.
- Do not start new tile graphics until M1.1A palette transactions are canonical + runtime green.
- Generated ROMs/PNGs are outputs; source code + manifests + verified canonical ROM remain source truth.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D frozen; M1.0A/B static + runtime integration baseline complete on scene0.
EVIDENCE extracted_metadata/m100a_vertical_slice_baseline.json + extracted_metadata/m100b_vertical_slice_runtime.json + Actions run 38053439943.
OPEN     M1.1A canonical palette + scene-source-v2 promotion.
NEXT     port minimal M11F/G/H palette/v2 transaction layer, run canonical ROM probes, then integrate palette authoring with the closed M1.0 scene0 baseline.
```
