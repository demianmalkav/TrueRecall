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
checkpoint: 0c5b3fa96e9f710ae150efd76e3c478fb60bdc54
```

M0.9C is COMPLETE. M0.9D is COMPLETE/FROZEN. M1.0A/B and M1.1A/B/C are COMPLETE. The active work is now **production content**, not further generic engine stabilization.

The selected vertical-slice sequence is **L3 — urban pursuit / subway** from the Level Bible. It exercises the frozen Quaid player, normal combat, sprint, objective flow, civilian/pursuit pressure and one Total Recall-specific chase subsystem without making unproven melee the first blocker.

## Canonical ROM identity

```text
title: True Lies (World)
size:  2,097,152 bytes
CRC32: 18C09468
MD5:   2fee5ef253faebaff73c017a7bda1cff
SHA-1: d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed.

## Frozen contracts

### Player — M0.9D

```text
source fingerprint: da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA-1:       49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum:          0x266C
F9F8 descriptor:   0x000A0000
native phases:     0,2,4,6,8,10
```

Do not edit v11 player pixels or mapping geometry during M1.2A.

### M1.0 gameplay proof

```text
shotgun pickup: type 69, x=690, y=558
world wall:     type 9, [668,540,676,580]
candidate:      84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027 / 0x6E6A
runtime:        M100B 14/14 PASS
```

The shotgun/wall remain proof content only and may be deliberately replaced by the production manifest once new runtime invariants supersede them.

### M1.1A palette

```text
palette index 8: 0x0464 -> 0x0648
player line 32..47 exact
M110A: 270e1d633db7883c9170bb1e4eb367abdf97a2bd / 0x6B9E
```

Actual VDP CRAM runtime proof is closed.

### M1.1B/C scene graphics and unified source

Scene0 confirmed primary graphics identity:

```text
retail descriptor: 0x00FFAA
primary LZBeam:    0x014898
decoded bytes:     24,960 / 780 tiles
retail SHA256:     0f73aff41d28f9cae5b17368f78979f720474ce342c85e53f9a46174e3bbb171
```

`scene_source.v3` owns map + objects + world collision + palette + confirmed primary graphics in one transaction. v1/v2 remain unchanged anchors. Scene0 reproduces the closed M1.1B candidate byte-for-byte:

```text
scene parent: 4a169bec49ca6fd571c6ea621e525d7968cc79c5 / 0x3245
integrated:   b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0 / 0xFAD7
```

Primary-only v3 is exact/no-op for 18/19 retail scenes. **Scene10 remains deliberately out of confirmed graphics scope** because C000 references tiles beyond the primary set; secondary/auxiliary graphics ownership is unresolved and must not be guessed.

M1.1C CI checkpoint: commit `965d1a54117b9aad69cdc9771e2f679059e91be2`, run `38074354446`, artifact `11677847802`, digest `c26452066d123b81f4f63b02e2b07cf297c794a175b5f9843c9067ff99c8a2b3`, both jobs PASS.

## M1.2A — production overlay — O1 COMPLETE / CONFIRMED

Production content no longer requires committing a full exported retail scene source.

Tooling:

```text
tools/build/scene_overlay.py
tools/build/m120a_scene_overlay_vertical_slice.py
tools/build/examples/m120a_scene0_closed_proof_overlay.json
```

`scene_overlay.v1` stores only authored deltas plus stable identity guards. It supports:

- palette replacement;
- single map-tile replacement and hash-guarded rectangular map replacement;
- object add/remove/replace by stable ID;
- world-collision add/remove/replace by stable ID;
- primary graphics tile replacement with exact retail-tile SHA guard.

The overlay is exported into canonical `scene_source.v3` **in memory** and lowered only through `scene_compiler_v3`; it does not duplicate allocation logic.

M120A reproduces the closed M112A candidate exactly:

```text
scene parent: 4a169bec49ca6fd571c6ea621e525d7968cc79c5
integrated:   b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0
checksum:     0xFAD7
```

Evidence: `extracted_metadata/m120a_scene_overlay_reproduction.json`.

## M1.2A — L3 environment starter — O2 IN PROGRESS

A first original station/subway vocabulary is runtime-visible through the overlay layer. It is a **prototype visual pass, not an art freeze**.

Current starter:

```text
manifest:     tools/build/examples/m120b_l3_urban_subway_starter_overlay.json
builder:      tools/build/m120b_l3_starter_build.py
scene parent: 7c14d479413e0efb412027209de6b85d6c67821f
candidate:    05fafc33f96a74d57765bacdba888d79e7eee860
checksum:     0xB78C
map rect:     E000 x=0,y=12,w=27,h=11
retail rect:  SHA256 9c71e0899ec8c3e74189209e8976ad2aabfca2d65289bef96dfc824427e16967
```

The current vocabulary uses 15 explicitly verified resident primary slots `2..16`. Pinned BlastEm savestate inspection proves all **15/15 32-byte authored tile payloads are present byte-exactly in VDP VRAM** during scene0. The resulting image reads as an industrial/subway environment rather than the diagnostic X proof.

Runtime regression remains green:

```text
M100B gameplay: 14/14 PASS
M110B CRAM:     PASS; only index 8 changes 0x0464 -> 0x0648
player line:    exact
```

Evidence: `extracted_metadata/m120b_l3_starter_runtime.json`.

### FALSIFIED production assumption

The earlier exploratory assumption that primary tile indices `565+` were safe merely because the retail scene0 tilemaps did not reference them is **FALSIFIED**. Runtime presentation showed those slots receiving dynamic/overwritten data and producing mosaic corruption. Behavioral tests staying green did not make those VRAM slots safe.

Current rule: **unreferenced in a retail tilemap does not imply free at runtime.** Production graphics slots must have direct runtime residency evidence or a separately recovered ownership/allocation contract.

### Viewport localization — HIGH CONFIDENCE / local scope only

Deterministic diagnostic partitions show the dominant initial E000 viewport contribution in rows `12..22`, columns `0..26`. Rows `23..44` and columns `27..106` did not produce map-driven presentation change in that initial capture. This is a placement aid, not a universal camera/map formula.

### Latest M1.2A CI

```text
commit:          0c5b3fa96e9f710ae150efd76e3c478fb60bdc54
Actions run:     38076261154
artifact id:     11678700540
artifact SHA256: 5c7f24601ba4868ebc5de8b62eb33de49e3d6674878bf3b78a71b2fae6ef3c8f
static:          PASS
BlastEm harness: PASS
```

## Objective seam selected for O3 — CONFIRMED retail mechanism, not yet integrated

The recovered objective system already contains a subway-specific pair:

```text
type 60 = subway lever      -> FC54 bit 0x4000
 type87 = subway signal box -> requires FC54 bit 0x4000
```

Retail placement identities are exact:

```text
scene5 type60: status 0x7800, stride 6, x=672, y=1280
scene6 type60: status 0x7800, stride 6, x=884, y=77
scene6 type87: status 0x7800, stride 6, x=176, y=3072
```

This is the preferred first L3 objective path because it is already mechanically and thematically aligned with the subway sequence. Do not implement the pursuit controller until the production scene skeleton is sufficiently readable and the lever/signal-box behavior is runtime-probed in scene0.

## OPEN — M1.2A

### O2 — finish readable L3 scene skeleton

The starter is technically valid but not final art. Establish three readable gameplay zones rather than one repeating texture field:

1. pursuit-entry zone;
2. combat/objective platform space;
3. subway-transition/exit zone.

Keep proof shotgun/wall explicitly temporary until production interactions supersede them.

### O3 — objective + pursuit subsystem

First prove the native type60/type87 subway objective path in scene0. Then add one scene-specific pursuit/chase trigger through recovered VM/object seams; do not invent a universal AI subsystem unless the scene-specific route proves insufficient.

### O4 — production runtime gate

Require deterministic pinned-BlastEm evidence for environment presentation, objective state transitions and pursuit trigger while preserving frozen Quaid and all still-applicable closed contracts.

## NEXT

1. Refine the M120B map composition into three visually distinct zones using only runtime-verified graphics slots or newly proven slots; keep status `NOT_ART_FREEZE`.
2. Re-run VRAM residency, presentation, M100B player semantics and M110B CRAM after the composition change.
3. Create an isolated scene0 type60 probe using the exact retail `status=0x7800, stride=6` contract and prove the `FC54 0x4000` transition at runtime.
4. Create a type87 signal-box probe and distinguish its no-lever versus lever-present branch using `FC54`/message-state evidence.
5. Only after those objective gates are green, place the pair deliberately in the L3 layout and design the scene-specific pursuit trigger.

## Retry / anti-loop rules

- Maximum two implementation retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1A/B/C gates reopen only on contradictory evidence.
- Do not edit v11 player pixels during M1.2A.
- Keep scene_source v1/v2/v3 closed contracts stable; production overlays sit above v3.
- Never infer free VRAM merely from an unreferenced tilemap index.
- Never commit exported retail scene sources or retail tile dumps.
- Prefer scene-specific scripted modules over speculative universal systems.
- Prefer small semantic Git commits.

## CONTINUATION FOOTER

```text
DONE     M1.1C closed; M1.2A authored-delta overlay closed; corrected L3 subway starter is runtime-visible with 15/15 authored tiles byte-exact in VRAM and gameplay/CRAM regression green.
EVIDENCE m120a_scene_overlay_reproduction.json + m120b_l3_starter_runtime.json + Actions run 38076261154.
OPEN     finish three-zone L3 composition, then prove type60/type87 subway objective behavior and add pursuit trigger.
NEXT     refine three-zone M120B composition, rerun runtime gates, then isolate type60 FC54 0x4000 and type87 signal-box branch behavior in scene0.
```
