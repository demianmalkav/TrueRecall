# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. Machine-readable companion: `docs/RECOVERY_MANIFEST.json`. Historical milestone documents and chat transcripts never override `NEXT` here.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M1.2A — L3 urban pursuit/subway production slice
checkpoint: fa676491696d8253e48c55472e4c8ad05a33f9a4
```

M0.9C is COMPLETE. M0.9D is COMPLETE/FROZEN. M1.0A/B and M1.1A/B/C are COMPLETE. M1.2A production authoring is active.

## Canonical ROM

```text
True Lies (World)
size  2,097,152
CRC32 18C09468
MD5   2fee5ef253faebaff73c017a7bda1cff
SHA1  d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed.

## Frozen contracts

Player M0.9D remains frozen:

```text
source fingerprint da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA1         49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum           0x266C
F9F8 descriptor    0x000A0000
native phases      0,2,4,6,8,10
```

Closed integration invariants remain available through M100B/M110B/M111/M112 evidence. Do not edit v11 player pixels, reopen scene-source v1/v2/v3 contracts, infer free VRAM from unused map indices, or guess secondary/aux graphics semantics.

## M1.2A production overlay — CLOSED / CONFIRMED

`scene_overlay.v1` is the production authored-delta layer above the closed `scene_source.v3` compiler. Production manifests carry guarded authored deltas only.

Core tooling:

```text
tools/build/scene_overlay.py
tools/build/m120a_scene_overlay_vertical_slice.py
```

## M120C — three-zone L3 skeleton — CONFIRMED RUNTIME / NOT ART FREEZE

```text
manifest:     tools/build/examples/m120c_l3_three_zone_overlay.json
builder:      tools/build/m120c_l3_three_zone_build.py
scene parent: be091e8e76af5d685d1ba2760ad821149141fcff
candidate:    7bd2144c22074bce5eebdf3e6e15f2f2c7db4ebe
checksum:     0x029E
map rect:     E000 x=0,y=12,w=27,h=11
```

Three readable bands use only runtime-confirmed primary graphics slots `2..16`: pursuit entry, objective platform and subway transition. 15/15 authored tiles are byte-exact in VDP VRAM; F9F8 remains `0x000A0000`; proxy remains `0x000F0000`; CRAM[8] remains `0x0648`.

Evidence: `extracted_metadata/m120c_l3_three_zone_runtime.json`.

Status remains `PROTOTYPE_VISUAL_PASS_NOT_ART_FREEZE`.

## Subway objective mechanism — CONFIRMED

```text
type60 subway lever      status 0x7800 stride 6 -> FC54 |= 0x4000
type87 subway signal box status 0x7800 stride 6 -> branches on FC54 & 0x4000
mission flag RAM         0xFFFFFC54
message offset RAM       0xFFFFFC06
```

Isolated evidence is retained in:

- `extracted_metadata/m120d_type60_scene0_runtime.json` — type60: `0x0000 -> 0x4000`, message `0x3C`, consumed with flag persistent;
- `extracted_metadata/m120e_type87_scene0_runtime.json` — type87: message `0x34` without flag, `0x36` with flag;
- `extracted_metadata/m120f_native_objective_pair_runtime.json` — native end-to-end type60→type87 sequence without debugger FC54 injection.

## M120G — production L3 objective integration — COMPLETE / CONFIRMED

M120G preserves the M120C visual skeleton and replaces temporary proof shotgun/wall content with the native subway objective pair.

Source truth is deliberately split to avoid duplicating the visual overlay:

```text
visual base: tools/build/examples/m120c_l3_three_zone_overlay.json
placement:   tools/build/examples/m120g_l3_objective_placement.json
builder:     tools/build/m120g_l3_objective_build.py
```

Production placements:

```text
type60 lever      x=724 y=558 status=0x7800 stride=6
type87 signal box x=652 y=558 status=0x7800 stride=6
```

The spawn is `x=701`. Runtime traversal confirms both ends are reachable and no object triggers prematurely. The native sequence is:

```text
frame 2200 x=701 FC54=0x0000 FC06=0x0002  ready
frame 2210 x=716 FC54=0x4000 FC06=0x003C  lever acquired
frame 2960 x=665 FC54=0x4000 FC06=0x0036  signal-box lever branch
```

No debugger write to FC54 is used.

Build identity:

```text
scene parent: cd43a4b53371e4d8329eaa328582ffd64262bddf
candidate:    150373a312283f5c89e5fa00e99f19d7a83bff44
checksum:     0xB7B0
```

Regression:

- 15/15 M120C authored tiles remain byte-exact in VDP VRAM;
- F9F8 descriptor remains `0x000A0000`;
- proxy descriptor remains `0x000F0000`;
- full CRAM is byte-exact M120C == M120G; CRAM SHA256 `c3c6dd5ae3450caecb79cac0e7962a282e6058f356345de9cac5c295f076e8cd`;
- player CRAM line 32..47 remains exact;
- proof shotgun and proof wall are deliberately retired from the production candidate;
- native type60→type87 mission progression is green.

Evidence: `extracted_metadata/m120g_l3_production_objective_runtime.json`.

CI checkpoint:

```text
commit:          fa676491696d8253e48c55472e4c8ad05a33f9a4
Actions run:     38079266697
static:          PASS
BlastEm harness: PASS
```

## FALSIFIED / boundaries

- **FALSIFIED:** retail-unreferenced primary tile indices `565+` are safe production VRAM slots. Runtime proved dynamic overwrite/mosaic. Use only direct residency evidence or a recovered allocation contract.
- Scene10 remains outside confirmed primary-only v3 graphics scope.
- M120C/M120G visuals are production skeletons, not final-art freeze.
- Do not revive proof shotgun/wall as mandatory production content.

## Pursuit-pressure seam — investigation opened

The first pursuit event should reuse retail behavior rather than create a universal AI system.

Confirmed useful facts:

- generic VM object-spawn wrappers exist and are structurally recovered;
- VM sources are exportable, assemblable and relocatable;
- type24 is already a retail scene0 ranged actor (`status=0x7800`, stride 6, retail scene0 placement `(1708,250)`);
- type24 belongs to the confirmed standard ranged family that creates runtime projectile type170;
- type87 is exportable as symbolic VM source and provides a proven `FC54 & 0x4000` conditional template;
- historical M06F tooling demonstrates source-level injection of `SpawnLinkedObject` calls into relocated VM scripts.

This is enough to justify a **scene-specific VM controller prototype** as the next route, but not enough yet to claim a production pursuit controller.

## OPEN

### O4 — first scene-specific pursuit trigger

Build the smallest controller that uses a proven condition/activation seam and materializes or activates one existing scene0-compatible hostile actor. Prefer type24 or another mechanically confirmed scene0 hostile; do not introduce a new AI model.

### O5 — production runtime gate

Prove that the pursuit event happens only after its intended trigger, does not corrupt the objective progression, and preserves M120G visual/player/palette contracts.

## NEXT

1. Export/inspect one retail VM parent that calls `SpawnLinkedObject` or another proven spawn wrapper and pin its argument/stack ABI.
2. Decide whether the M120H controller should trigger on `FC54 & 0x4000`, on proximity/contact, or on a post-signal state. Do not guess: choose the condition that can be discriminated in runtime.
3. Build one isolated relocated-VM controller that spawns/activates a confirmed scene0-compatible hostile class, initially type24 unless runtime evidence rejects it.
4. Runtime-prove trigger-off vs trigger-on behavior, child creation and projectile/hostile activity before integrating it into M120G.
5. Only after the isolated controller is green, place it in the production L3 layout and rerun M120G objective, VRAM, CRAM and frozen-player regressions.

## Retry / anti-loop rules

- Maximum two retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1/M120G gates reopen only on contradictory evidence.
- Do not edit v11 player pixels during M1.2A.
- Keep scene_source v1/v2/v3 contracts stable; production overlays sit above v3.
- Never infer free VRAM from an unreferenced tilemap index.
- Never commit exported retail scene sources or retail tile dumps.
- Prefer small semantic commits and correct logical-parent comparisons.

## CONTINUATION FOOTER

```text
DONE     M120G production L3 objective integration closed: three-zone environment + native type60 lever + native type87 signal-box traversal; visual/player/CRAM contracts green; CI green.
EVIDENCE m120g_l3_production_objective_runtime.json + Actions run 38079266697.
OPEN     first scene-specific pursuit-pressure trigger and final production runtime integration.
NEXT     recover the smallest proven spawn-controller ABI, prototype one isolated relocated-VM trigger using an existing scene0-compatible hostile (type24 preferred candidate), prove trigger-off/on at runtime, then integrate into M120G.
```
