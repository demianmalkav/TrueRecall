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
milestone:  M1.2A — L3 urban pursuit/subway production slice
checkpoint: 965d1a54117b9aad69cdc9771e2f679059e91be2
```

**M0.9C is COMPLETE.**

**M0.9D is COMPLETE and FROZEN.**

**M1.0A/B is COMPLETE.** Frozen Quaid, persistent object authoring and world collision coexist in one reproducible scene0 baseline and are runtime-confirmed.

**M1.1A is COMPLETE.** Palette authoring is canonical, source-level, transactional and runtime-confirmed at actual VDP CRAM.

**M1.1B is COMPLETE.** Primary scene0 environment graphics are source-authorable and runtime-confirmed at actual VDP VRAM/presentation.

**M1.1C is COMPLETE for the production scene0 path.** `scene_source.v3` now owns map + objects + world collision + palette + confirmed primary environment graphics through one source-level transaction and reproduces the closed M1.1B candidate byte-for-byte.

The active task returns to product work: build the first recognizably **Total Recall** production slice using scene0 as a technical chassis. The selected sequence is **L3 — urban pursuit / subway** from the Level Bible because it exercises normal combat, the proven sprint, objective flow, civilians/pursuit pressure and one film-specific scripted chase subsystem without forcing the still-unproven melee system as the first content blocker.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed. Generated builds remain reproducible from source/manifests plus this verified base.

## Frozen player contract

```text
M0.9D source fingerprint: da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA-1:              49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum:                 0x266C
F9F8 descriptor:          0x000A0000
native phases:            0,2,4,6,8,10
```

Do not edit v11 player pixels or mapping geometry during M1.2A unless a deliberate new player milestone is opened.

## Closed scene0 integration contracts

M1.0 gameplay baseline:

```text
shotgun pickup: type 69, stride 6, x=690, y=558
world wall:     type 9, rect=[668,540,676,580]
SHA-1:          84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027
checksum:       0x6E6A
M100B runtime:  14/14 PASS
```

M1.1A palette proof:

```text
palette index:       8
retail/authored:     0x0464 -> 0x0648
player line:         32..47 exact
palette allocation:  0x303080
M110A SHA-1:         270e1d633db7883c9170bb1e4eb367abdf97a2bd
checksum:            0x6B9E
```

Actual VDP CRAM proof: exactly index 8 differs; M100B remains green.

M1.1B graphics proof:

```text
scene0 graphics descriptor: 0x00FFAA
primary LZBeam:             0x014898
decoded resource:           24,960 bytes / 780 tiles
retail decoded SHA256:      0f73aff41d28f9cae5b17368f78979f720474ce342c85e53f9a46174e3bbb171
authored tile:              index 2
integrated SHA-1:           b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0
checksum:                   0xFAD7
```

Runtime proof: exactly VRAM `[0x0040,0x0060)` changes (32 bytes), CRAM is unchanged versus M110A, presentation delta is confined to the expected upper-environment region, M100B remains 14/14 and M110B remains green.

## M1.1C scene-source-v3 transaction — COMPLETE / CONFIRMED

Canonical additive tooling:

```text
tools/build/scene_source_v3.py
tools/build/scene_compiler_v3.py
tools/build/m112a_scene_source_v3_vertical_slice.py
```

`scene_source.v1` and v2 remain unchanged regression anchors. v3 adds only the M1.1B-confirmed primary graphics payload/identity. Secondary and auxiliary graphics pointers are preserved as opaque immutable identity; their semantics are **not** inferred.

The v3 transaction builds the existing v2 scene/palette stage first, allocates primary graphics after the same ledger with a `0x304000` floor, verifies non-overlap and repairs the Genesis checksum once at the end.

Canonical scene0 result:

```text
scene parent SHA-1: 4a169bec49ca6fd571c6ea621e525d7968cc79c5
scene checksum:     0x3245
integrated SHA-1:   b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0
checksum:           0xFAD7
```

The v3 path reproduces the closed M1.1B ROM **byte-for-byte**. Runtime reruns reproduce the exact M111D VRAM/presentation result and M111E closed-gate regression.

Evidence:

- `extracted_metadata/m112a_scene_source_v3_vertical_slice.json`
- `extracted_metadata/m112b_v3_graphics_runtime.json`
- `extracted_metadata/m112c_v3_regression.json`
- `extracted_metadata/m112_scene_source_v3_scope_matrix.json`

CI checkpoint:

```text
commit:          965d1a54117b9aad69cdc9771e2f679059e91be2
Actions run:     38074354446
artifact id:     11677847802
artifact SHA256: c26452066d123b81f4f63b02e2b07cf297c794a175b5f9843c9067ff99c8a2b3
static:          PASS
BlastEm harness: PASS
```

### Scope boundary — important

The current primary-only v3 graphics model is exact/no-op for 18 of 19 retail scenes:

`0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18`.

**Scene 10 is deliberately out of confirmed graphics scope.** Its C000 map references tile indices beyond the decoded primary set. This is evidence that unresolved secondary/auxiliary graphics ownership matters there. Do not generalize or guess those semantics merely to obtain 19/19. Scene0 — the current production chassis — is fully inside the confirmed model.

## M1.2A product target — L3 urban pursuit/subway

Design-source rationale:

- Level Bible L3: city/subway escalation, civilians and pursuit pressure with Total Recall-specific scripting.
- Game Design Bible: preserve responsive top-down combat/objectives, make Quaid physically distinct, and use custom modules for film-specific spectacle.
- Roadmap vertical-slice bar: converted/new environment, authored placements, enemies/props, objective flow, cutscene transition, audio path and at least one genuinely new mechanic/subsystem.

M1.2A uses scene0 only as a proven technical chassis; it is **not** a claim that True Lies scene0 geography is final Total Recall level design.

### Production-source rule

Do not commit a full exported scene_source.v3 because it contains derived retail maps/placements/graphics. Production content must be stored as a declarative **authored-delta overlay** containing only new/original project data and stable references to retail identities. The build exports canonical v3 in memory, applies the overlay, validates identity and compiles the result.

## OPEN — M1.2A

### O1 — declarative authored-delta overlay

Create a source-controlled overlay schema for scene0 supporting the already-confirmed production domains without copying retail payloads:

- palette index replacements;
- map tile-word replacements;
- object add/remove/replace by stable source ID;
- world-collision add/remove/replace by stable ID;
- primary-graphics tile replacements by tile index + original 32-byte authored payload.

The first overlay must be able to reproduce the closed M112A candidate exactly from canonical ROM + overlay + frozen player contract.

### O2 — L3 production scene skeleton

Replace diagnostic proof content with a first original urban/subway kit and layout pass. It must establish at least three readable zones: pursuit entry, combat/objective space, and subway-transition exit. Temporary proof pickup/wall may remain only where explicitly tagged temporary.

### O3 — objective + pursuit subsystem

Author one concrete objective/interact path and one scripted pursuit/chase trigger using recovered object/VM seams. Do not invent new universal AI systems if a scene-specific controller is sufficient.

### O4 — production runtime gate

Run the slice under pinned BlastEm and require:

- frozen Quaid presentation intact;
- M100B/M110B closed contracts unaffected unless the production manifest deliberately replaces their proof content;
- authored environment reaches VRAM/presentation;
- objective/pursuit state transitions are deterministic;
- no allocator overlap or scene-record containment violation.

## NEXT

1. Implement `scene_overlay.v1`, containing authored deltas only, and strict validation against exported canonical `scene_source.v3` identity.
2. Add an overlay compiler that applies the manifest in memory and lowers through `scene_compiler_v3`; do not duplicate v3 allocation logic.
3. Encode the current tile-2/palette/pickup/wall proof as the first overlay and require byte-exact reproduction of `b6c0303b... / 0xFAD7`.
4. Once the overlay gate is green, replace proof-only visual data with a small original L3 urban/subway environment starter kit while preserving the closed engine contracts.
5. Define the first objective and pursuit trigger only after the production scene skeleton is runtime-visible.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1A/B/C gates reopen only on contradictory evidence.
- Do not edit v11 player pixels during M1.2A.
- Keep `scene_source.v1`, v2 and the closed v3 contract stable; production overlays sit above v3.
- Do not resolve scene10 secondary/aux graphics unless the selected production content actually needs it.
- Never commit exported retail scene sources or retail tile dumps.
- Prefer scene-specific scripted modules over speculative universal systems.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M09C complete; M09D frozen; M1.0A/B complete; M1.1A/B/C complete, including source-v3 unified scene graphics transaction and runtime regression.
EVIDENCE m112a_scene_source_v3_vertical_slice.json + m112b_v3_graphics_runtime.json + m112c_v3_regression.json + m112_scene_source_v3_scope_matrix.json + Actions run 38074354446.
OPEN     M1.2A L3 urban pursuit/subway production slice.
NEXT     implement an authored-delta scene_overlay.v1 above scene_source.v3 and require it to reproduce the closed M112A candidate exactly before replacing proof content with original L3 production content.
```
