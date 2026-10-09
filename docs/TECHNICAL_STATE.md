# Technical State — TrueRecall

Status vocabulary follows `AGENTS.md`. Detailed subsystem evidence lives in the dedicated files under `docs/`; this file is the current technical checkpoint and recovery summary.

## Canonical ROM — CONFIRMED

- Title: `True Lies (World)`
- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`
- Reset entry: `0x00000200`
- System signature: `GENSYSv1.4(May94)`
- Audio signature: `MAXMUS T Bardo 1993 V2.1a` near `0x0134A2`

The original ROM is immutable and is never committed.

## Milestone state

Completed foundation:

- **M0.1** ROM validated
- **M0.2** static landmarks recovered
- **M0.3** entity architecture recovered
- **M0.4** asset/cutscene pipeline recovered
- **M0.5** gameplay map format recovered

M0.6 reconstruction/authoring line:

- **M0.6A** static player-control architecture recovered
- **M0.6B** held input, weapon-cycle direction and dual-player-object architecture recovered
- **M0.6C** object stream / object VM / archetype / animation / renderer reconstruction
- **M0.6D** controlled in-place VM/data patch
- **M0.6E** source-level VM relocation/edit/reassembly
- **M0.6F** independently addressable scripted-type proof
- **M0.6G/H** gameplay-map relocation and one-tile authored edit
- **M0.6I–K** placement replacement/insertion/mixed-stride descriptor regeneration
- **M0.6L** declarative scene-object compiler
- **M0.6M** new scripted-class + persistent placement static build proof
- **M0.6O** runtime proof that a relocated VM representation changes live game behavior; its original placement-causality interpretation was corrected after discovering retail runtime use of type 1

### M0.7 — COMPLETE: runtime-validated controlled player extension

A new held-Y sprint overlay has been executed and measured in BlastEm.

- trigger: Genesis **Y**, normalized input bit 13
- animation hook: `0x0083A6` → trampoline `0x1FE000`
- movement hook: `0x009864` → trampoline `0x1FE080`
- sprint movement parameters: `0x0300`, `0x0280`
- common animation-direction table relocated `0x013F32 → 0x1FB000`
- independent sprint selector: `0x1FF0`
- sprint row address: `0x1FCFF0`
- M0.7C output SHA-1: `55e02728cb0b7f3627f410202c889197c0e3d0d2`

Deterministic runtime comparison proves faster world traversal: at frame 2118 the sprint run has 24 px of registered camera/world progress versus 12 px in retail; at frame 2124 it is 36 px versus 21 px. The same 37 px camera plateau is reached at frame 2126 under sprint versus frame 2136 in retail.

The animation-table relocation is pixel-identical to retail in the tested runtime windows, and the no-Y gameplay region is pixel-identical to retail in the tested frames.

Important limitation: the new sprint row has an **independent selector and ROM-resident row**, but for this proof its presentation bytes clone the retail JLLBFR row. M0.7 therefore proves new runtime behavior and an independent presentation slot, **not yet original new sprite art/animation frames**.

See `docs/M07_RUNTIME_SPRINT.md`, `extracted_metadata/m07_runtime_validation.json` and `tools/runtime/m07_sprint_compare.py`.

## Runtime harness — CONFIRMED

BlastEm fork build:

```text
blastem-linux-x86_64-1.0.0-6e5677969b59
SHA-256 b511890bd1cd6616050e8b009aa9bf1d5d791a326682d3da76d9524467dfb0d2
```

The project now has deterministic frame-script navigation from boot into the first mission, screenshot capture and image-based regression comparison. Copyrighted screenshots remain local/generated and are not committed.

Remote GDB remains useful but has been less reliable than the control-socket/frame-script path and is not required for the M0.7 proof.

## Core entity architecture — CONFIRMED / HIGH CONFIDENCE

- generic object record size: `0x72` bytes
- generic pool: **35** records
- pool base: `FFFFF9FE`
- free-list head: `FFFFF9FC`
- active count: `FFFFF9F2`
- active-list sentinel: `FFFFF9F4`
- allocator: `0x00F732`
- linked allocator: `0x00F7CC`
- destroy/free: `0x00F8F8`
- insertion: `0x00FA40`
- `object+0x34`: entity↔entity interaction callback — HIGH CONFIDENCE
- `object+0x38`: entity↔world/structure collision callback — HIGH CONFIDENCE
- `object+0x50`: 8-way facing — CONFIRMED

Retail static scene analysis reaches a retention-window upper bound of all 35 generic slots. Treat the pool as a hard production budget.

## Player/control architecture — CONFIRMED / HIGH CONFIDENCE

Normalized input:

- `F6EA` previous input
- `F6EC` current input
- `F6EE` pressed edges
- `F6F0` held overlap
- D-pad mask `0x000F`
- Fire edge bit 4
- Roll edge bit 5
- Lock held bit 6 — HIGH CONFIDENCE
- weapon cycle bit 12 next / bit 14 previous

The player is represented by two synchronized engine objects:

- `F9F8`: world/render avatar — HIGH CONFIDENCE
- `FB6E`: control/collision proxy — HIGH CONFIDENCE

`FB7C` is an action bitfield and `FB7E` is a separate context/overlay word. Roll, post-roll, roll-fire, lock/fire and alternate-player contexts are structurally recovered. See `docs/PLAYER_SYSTEM.md`.

M0.7 demonstrates that this architecture can be extended additively without replacing the retail player loop.

## Weapons — CONFIRMED

`FFFFFB8C` uses even selectors and `FFFFFB8E` is the ownership mask:

| Selector | Weapon | Ammo | Handler |
|---:|---|---|---|
| 0 | Pistol | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `FFFFFB7A` | `0x008E1C` |

The system is table-driven and remains a major Total Recall extension seam.

## Persistent scene-object stream — CONFIRMED / AUTHORABLE

Across 19 retail scenes:

- 2,449 placements
- 128 placed `type_id`s
- 1,689 six-byte records
- 760 eight-byte records
- Y-sorted, spatially materialized
- low 10 status bits = `type_id`
- descriptor records count, offsets, LZBeam source and mixed `(stride, quantity)` runs

The project can parse, replace, remove, add, reorder, re-encode, relocate and regenerate scene-object descriptors from declarative source. See `docs/OBJECT_STREAM.md` and the M0.6I–M documentation.

## Object VM — CONFIRMED / AUTHORABLE

- dispatcher: `0x011934`
- 72-opcode jump table: `0x011814–0x011933`
- type representation selector: `0x07A33C`
- type pointer table: `0x07953E`

Assembler/disassembler round-trip covers 136 scripted type IDs, 27,818 reachable instruction addresses and all 53 opcodes used by retail with exact reachable-byte re-encoding.

Object behavior is therefore source-representable rather than an opaque binary blob. See `docs/OBJECT_VM.md` and `docs/VM_AUTHORING.md`.

## Archetype / animation / renderer — CONFIRMED enough for inverse-authoring work

Generic placements initialize `archetype_id = type_id`. `0x00F9D4` stores the archetype in `object+0x2A` and resolves an animation descriptor from table `0x079906` into `object+0x2C`. Archetypes also index difficulty-dependent HP/damage tables.

Animation mapping records use a 16-byte header plus `N × 4-byte` pieces. Every piece is a fixed 16×16 sprite chunk:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Each chunk is 128 bytes / four Genesis tiles. Raw and indexed/RLE-backed chunk storage are both recovered, and true-color diagnostic reconstruction works with scene CRAM.

M0.7 proves that the common direction table can be relocated and extended safely at runtime. The next authoring target is a genuinely new mapping/chunk presentation rather than a cloned retail row.

See `docs/ANIMATION_FORMAT.md` and `docs/SPRITE_RENDERER.md`.

## Semantic object catalog and spawn graph — PARTIALLY RECOVERED

The authoring catalog structurally covers all 128 placed type IDs / 2,449 placements. Current evidence-based labels/classes include pickups, objective items, doors, civilians, ranged/spread hostile actors, hazards/destructibles, controllers, vehicles and loot props. Visual appearance alone is never sufficient to freeze a semantic name.

The constant spawn graph currently proves:

- 58 parent types with at least one child
- 79 parent→child edges
- 42 runtime-only child types

Examples include standard projectile 170, spread projectile 175, boss projectile 225 and truck destruction/effect child 227.

See `docs/SPAWN_GRAPH.md` and semantic-catalog probes.

## Asset/map pipeline — BIDIRECTIONAL for recovered map data

LZBeam decode/encode is operational and deterministic. Gameplay maps can be decoded, edited, re-encoded, relocated, pointer-patched and re-decoded for structural regression. M0.6H changes exactly one map word while preserving every other decoded word.

Cutscene screen/tilemap/CRAM structure is also recovered. Full inverse authoring for every graphics/animation asset class is not yet complete.

## Current branch / checkpoint

Active integration branch:

`m0.7-sprint-runtime`

M0.7 evidence is isolated from `main` pending further hardening and presentation-authoring work. Generated ROMs and extracted copyrighted imagery are not committed.

## Highest-value next work

1. **Original presentation authoring:** create a genuinely new sprint mapping/frame/chunk in free ROM space, not a byte clone of a retail animation row; runtime-prove that only the sprint path uses it.
2. Convert the deterministic BlastEm harness into broader regression coverage for idle/walk/fire/roll/roll-fire/Lock/hit/invulnerability.
3. Harden M0.7 movement integration: test collision edges, roll/fire interaction, weapon cycling and alternate-player overlays while Y is held.
4. Continue semantic classification of unresolved placement classes without visual-only naming.
5. Finish collision/material and mission-script authoring structures needed for a complete level schema.
6. After original presentation authoring is proven, begin the first Total Recall vertical-slice asset/mechanic prototype on top of the now runtime-validated extension seam.
