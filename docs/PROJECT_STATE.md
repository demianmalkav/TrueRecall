# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. Machine-readable companion: `docs/RECOVERY_MANIFEST.json`. Historical milestone documents and chat transcripts never override `NEXT` here.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M1.2A — L3 urban pursuit/subway production slice
checkpoint: 0ba0fa1fb1b5935c288b7e663af40ad28b125022
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

`scene_overlay.v1` is the production authored-delta layer above the closed `scene_source.v3` compiler. It supports guarded palette, map, object, world-collision and confirmed primary-graphics edits without committing exported retail scene sources.

Core tooling:

```text
tools/build/scene_overlay.py
tools/build/m120a_scene_overlay_vertical_slice.py
```

## M120C — three-zone L3 skeleton — CONFIRMED RUNTIME / NOT ART FREEZE

The corrected M120B safe-slot starter has been refined into three readable gameplay bands using **only runtime-confirmed primary graphics slots 2..16**.

```text
manifest:     tools/build/examples/m120c_l3_three_zone_overlay.json
builder:      tools/build/m120c_l3_three_zone_build.py
scene parent: be091e8e76af5d685d1ba2760ad821149141fcff
candidate:    7bd2144c22074bce5eebdf3e6e15f2f2c7db4ebe
checksum:     0x029E
map rect:     E000 x=0,y=12,w=27,h=11
```

Composition:

1. pursuit-entry zone — columns 0..7;
2. objective platform — columns 9..18;
3. subway transition — columns 20..26;
4. structural separators — columns 8 and 19.

Runtime evidence confirms:

- 15/15 authored tile payloads byte-exact in VDP VRAM;
- F9F8 descriptor remains `0x000A0000`;
- proxy descriptor remains `0x000F0000`;
- proof shotgun still grants ownership + five shells;
- proof wall still blocks at the closed M100B boundary;
- CRAM[8] remains authored `0x0648` and player palette line remains protected;
- same-stage presentation difference is confined to the gameplay environment above the HUD.

Evidence: `extracted_metadata/m120c_l3_three_zone_runtime.json`.

Status remains `PROTOTYPE_VISUAL_PASS_NOT_ART_FREEZE`: the zoning is now readable, but final L3 art direction is not frozen.

## Subway objective seam — CONFIRMED RUNTIME

Recovered retail mechanism:

```text
type60 subway lever      status 0x7800 stride 6 -> FC54 |= 0x4000
type87 subway signal box status 0x7800 stride 6 -> branches on FC54 & 0x4000
mission flag RAM         0xFFFFFC54
message offset RAM       0xFFFFFC06
```

### M120D — type60 isolated scene0 proof

At `(701,558)`, type60 produces:

```text
FC54: 0x0000 -> 0x4000
FC06: 0x003C during pickup message
active_count: 7 -> 6 after message/object consumption
```

The flag persists after the object is consumed. Control M120C keeps FC54 at zero.

Evidence: `extracted_metadata/m120d_type60_scene0_runtime.json`.

### M120E — type87 branch discrimination

With the same type87 instance at `(701,558)`:

```text
FC54=0x0000 -> FC06=0x0034
FC54=0x4000 -> FC06=0x0036
```

The second condition was injected only after scene initialization and immediately before type87 branch evaluation. This proves branch dependence but is not the end-to-end proof.

Evidence: `extracted_metadata/m120e_type87_scene0_runtime.json`.

### M120F — native type60 → type87 end-to-end proof

No debugger modification of FC54 is used.

```text
type60 @ (701,558)
type87 @ (724,558)
scene parent c5f572ee339ca9194d497c523feffd0366cd1862
candidate    ed3f52765d1cb76ad90df1a5bc74c5283c5115dc
checksum     0xF642
```

Observed runtime sequence:

```text
frame 1500 x=701 FC54=0x4000 FC06=0x003C  type60 branch
frame 1860 x=701 FC54=0x4000 FC06=0x0002  type60 consumed
frame 2200 x=701 FC54=0x4000 FC06=0x0002  gameplay resumed
frame 2270 x=710 FC54=0x4000 FC06=0x0036  type87 lever-present branch
```

This confirms the native objective pair can be transplanted into scene0 while preserving its retail mission-state contract.

Evidence: `extracted_metadata/m120f_native_objective_pair_runtime.json`.

## FALSIFIED / boundaries

- **FALSIFIED:** retail-unreferenced primary tile indices `565+` are safe production VRAM slots. Runtime proved dynamic overwrite/mosaic. Use only direct residency evidence or a recovered ownership contract.
- Scene10 remains outside confirmed primary-only v3 graphics scope.
- M120C zoning is a production skeleton, not final art.
- The objective pair is proven in an isolated scene0 probe; its final L3 placement is not yet frozen.

## OPEN

### O3 — integrate objective pair into the production L3 layout

Place type60 and type87 deliberately in different readable M120C zones so the player must traverse the authored space. Preserve the confirmed `0x7800/stride6/FC54 0x4000` contract and rerun VRAM/CRAM/player/objective regression.

### O4 — first scene-specific pursuit trigger

After the objective pair survives production integration, identify the smallest recovered VM/object seam capable of one L3 chase-pressure event. Prefer a scene-specific scripted module over a speculative universal pursuit AI system.

### O5 — production runtime gate

Require pinned-BlastEm evidence for environment presentation, native objective progression and the pursuit trigger while preserving frozen Quaid and every still-applicable closed contract.

## NEXT

1. Build an M120G production overlay derived from M120C that places type60 in the pursuit-entry/objective approach and type87 in the subway-transition zone with spatial separation that is actually traversable.
2. Run the native objective sequence without debugger state injection and prove `0x3C -> flag persists -> 0x36` in that production layout.
3. Re-run 15-slot VRAM residency, CRAM[8]/player-line checks, frozen player descriptors and applicable M100B behavior invariants.
4. Once M120G is green, inspect recovered VM/object controller seams for one scene-specific pursuit-pressure trigger; do not design a universal chase subsystem first.
5. Persist evidence, update this state/manifest and synchronize Drive only after the new production checkpoint is green.

## Retry / anti-loop rules

- Maximum two retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1 gates reopen only on contradictory evidence.
- Do not edit v11 player pixels during M1.2A.
- Keep scene_source v1/v2/v3 contracts stable; production overlays sit above v3.
- Never infer free VRAM from an unreferenced tilemap index.
- Never commit exported retail scene sources or retail tile dumps.
- Prefer small semantic commits and correct logical-parent comparisons.

## CONTINUATION FOOTER

```text
DONE     M120C three-zone L3 skeleton runtime-confirmed; type60 isolated proof confirmed; type87 FC54 branch discrimination confirmed; native type60->type87 end-to-end scene0 proof confirmed.
EVIDENCE m120c_l3_three_zone_runtime.json + m120d_type60_scene0_runtime.json + m120e_type87_scene0_runtime.json + m120f_native_objective_pair_runtime.json.
OPEN     integrate the proven objective pair into the production three-zone L3 layout, then add one scene-specific pursuit trigger.
NEXT     build M120G production objective placement from M120C, runtime-prove native 0x3C -> 0x36 progression, rerun closed visual/gameplay contracts, then investigate the smallest pursuit trigger seam.
```
