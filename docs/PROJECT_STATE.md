# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. In a fresh context, read this file before milestone documents, old handoffs or chat transcripts.

Machine-readable companion: `docs/RECOVERY_MANIFEST.json`.

## Authority rules

1. `docs/PROJECT_STATE.md` decides where work resumes.
2. `docs/RECOVERY_MANIFEST.json` exposes the same continuation state in machine-readable form.
3. `docs/TECHNICAL_STATE.md` is cumulative background and never overrides `NEXT` here.
4. HISTORICAL/FALSIFIED material is provenance, not a promotion gate.
5. Drive is the recovery/design mirror; duplicated dynamic technical state defers to GitHub.
6. Refresh the live branch before writes. The checkpoint below identifies the material baseline; documentation-only commits may advance HEAD.

## Active continuation

```text
branch:     m10-vertical-slice-baseline
milestone:  M1.0A — first Total Recall vertical-slice integration baseline
checkpoint: 00d9a0e9db501e7f8763515ce34fbe7476dd6c67
```

**M0.9C COMPLETE. M0.9D COMPLETE.**

The project has crossed from engine/pipeline proof into the first production integration track. The target vertical slice is **Post-Rekall / apartment and escape**: a compact Earth sequence able to combine normal combat, production Quaid presentation, authored objectives/interactions and the first genuinely Total Recall-specific physical/melee behavior without requiring Mars-specific systems yet.

This milestone does not mean “build the whole level immediately”. M1.0A first freezes a deterministic integration baseline in which the already-proven player-art pipeline and canonical scene-authoring pipeline coexist in one reproducible ROM.

## Canonical ROM

```text
True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

Original ROM remains immutable and uncommitted. ROM availability is session-local.

## Frozen player baseline — M0.9D v11

Production-freeze evidence:

`extracted_metadata/m09d_quaid_v11_production_freeze.json`

Source of truth:

`tools/build/m09d_quaid_sprint_source.py`

Closed contract:

```text
descriptor:             0x000A0000
native phases:          0,2,4,6,8,10
runtime facings:        8
authored facings:       N,NE,E,SE,S
native mirrored facings SW<-SE, W<-E, NW<-NE
unique mapping records: 10
resource group:         7
reserved slots/phase:   24
used slots/phase:       17
max pieces/frame:       4
palette:                proven player CRAM line 2, indices 0..15
```

Frozen v11 source fingerprint:

`da0a060e77f9da835b388ffe94a8090d75cd51ea`

Frozen phase-bank SHA-1 values:

```text
97a9f024374b75810dd060ff8c03b4b703cd7ab6
fce14e16bc2325ea603f7ad973a0033c56f68098
38c2f905c4f05cc01938f440f2e7cd8a9fa28d74
12fd0abb168d4983fc3b6d2d46a4589317c8f6c2
0cd1b90c15c55504e2e55e992197022a5856204f
416007b12132f06ff30fa009649e4b1c6379d5c1
```

Frozen deterministic build:

```text
size:     4,194,304 bytes
SHA-1:    49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum: 0x266C
```

Final runtime regression against the correct M07C parent passed all ten containment/fallback/control invariants with zero compared-state mismatches, all six native phases visible, canonical F9F8 descriptor preserved and maximum active difference box `65x64` host pixels.

CI checkpoint for source/banks/build:

```text
commit:  4e933f104292a88d6301d0c39855176253a077d1
run:     38019250327
static:  PASS (58 tests)
BlastEm: PASS
```

The visual freeze is deliberately scoped to the first sprint/locomotion production family. It is not a ban on later character animation families or future art polish justified by in-game production evidence.

## Stable scene-authoring baseline

M0.11A–D remain the canonical scene-authoring foundation. M11D provides a unified source representation for gameplay planes, persistent objects and world collision; broadphase and mixed-stride object structures are derived outputs rather than hand-edited state.

Canonical M11D tool/evidence family:

```text
tools/build/scene_source.py
tools/rom_probe/scene_source_probe.py
extracted_metadata/m11d_scene_source.json
docs/M11D_CANONICAL_SCENE_SOURCE.md
```

Representative retail no-op exact scenes already proven: `0,5,6,18`. Scene 18 also has a structural proof combining a tile edit, a persistent object addition and a new world-collision wall.

Parallel M11E–H work is preserved but is not automatically promoted into M1.0. M1.0A starts from M11D unless a concrete slice requirement demonstrates that one of those branches is necessary.

## M1.0 target — Post-Rekall / apartment and escape

Design intent for the first slice:

- Quaid presentation uses the frozen v11 family as the initial locomotion baseline;
- compact Earth/apartment visual identity rather than a generic True Lies reskin;
- normal top-down combat remains readable and regression-compatible;
- at least one authored objective/interactable;
- at least one Total Recall-specific physical/melee mechanic or encounter beat;
- deterministic entrance, gameplay and exit/transition;
- scene source, object placement and collision remain declarative/reproducible;
- no final copyrighted film audio is required for this engineering slice.

The exact retail donor scene is **not yet frozen**. It must be selected by evidence: dimensions, collision density, object pressure, indoor layout suitability and transformation cost.

## OPEN

### O1 — select and freeze the retail donor scene

Evaluate all 19 retail scenes using existing scene/object/world metadata. Select the donor that best matches an indoor apartment/escape slice with the least unnecessary engine-specific baggage. Selection must record dimensions, plane sizes, object count/types, collision complexity and why alternatives were rejected.

### O2 — unified M1.0A baseline build

Starting from the canonical ROM, reproduce the frozen M09D player baseline and apply an M11D no-op/controlled scene transaction in the same 4 MiB output. Prove that player presentation and scene authoring coexist without relocating/overwriting one another.

### O3 — first authored Total Recall scene delta

After O1/O2 are green, create the first declarative apartment-slice delta: initial environment geometry/tile changes, spawn/placement set and collision changes. This is an integration proof, not yet full content production.

## NEXT

1. Verify the canonical ROM locally before any ROM-dependent operation.
2. Inventory all 19 scenes from existing M11/M10/object metadata and rank candidates for the Post-Rekall/apartment slice.
3. Freeze one donor scene and persist the selection rationale/evidence.
4. Build a combined M09D-v11 + M11D no-op integration candidate and audit ROM allocation overlap before runtime.
5. Run deterministic BlastEm regression proving the frozen Quaid path remains intact and the selected donor scene remains retail-equivalent under no-op authoring.
6. If green, create the first controlled declarative Total Recall scene delta and begin M1.0 production iteration.

## Anti-loop / integration rules

- Do not reopen M09C/M09D without contradictory runtime evidence.
- Do not choose a donor scene from aesthetics alone; use recovered scene/object/collision metadata.
- Do not manually edit the generated ROM.
- Player-art banks and scene allocations must be checked for overlap before each integration build.
- Compare each integration candidate against its correct logical parent.
- One failing subsystem should not trigger unrelated rewrites.
- Keep creative scene intent separate from recovered retail facts.

## CONTINUATION FOOTER

```text
DONE     M09C/M09D complete; v11 first production Quaid sprint family frozen; M1.0 branch opened.
EVIDENCE extracted_metadata/m09d_quaid_v11_production_freeze.json + Actions run 38019250327.
OPEN     donor-scene selection -> combined M09D/M11D baseline -> first authored apartment-slice delta.
NEXT     rank all 19 retail scenes from recovered metadata and freeze the best donor for Post-Rekall/apartment.
```
