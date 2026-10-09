# Technical State — TrueRecall

Status vocabulary follows `AGENTS.md`.

## Canonical ROM — CONFIRMED

- Title: `True Lies (World)`
- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`
- Reset entry: `0x00000200`
- System signature: `GENSYSv1.4(May94)`
- Audio signature: `MAXMUS T Bardo 1993 V2.1a` near `0x0134A2`

The original ROM is immutable and never committed.

## Milestone state

Completed foundation:

- **M0.1** canonical ROM validation
- **M0.2** static landmarks / RAM / cheat-correlated seams
- **M0.3** entity architecture
- **M0.4** asset/cutscene extraction pipeline
- **M0.5** gameplay map format

Completed reconstruction / authoring foundation:

- **M0.6A/B** player input/control architecture and dual-player-object model
- **M0.6C** object stream / VM / archetype / animation / renderer reconstruction
- **M0.6D/E** controlled VM editing plus source-level relocation/reassembly
- **M0.6F** new independently addressable scripted type in an unused slot
- **M0.6G/H** gameplay-map LZBeam relocation and one-tile authored edit
- **M0.6I/J/K/L** placement replacement/insertion, mixed-stride descriptor regeneration and declarative scene-object compiler
- **M0.6M** new scripted class placed directly into a persistent level stream
- later M0.6 runtime probes proved the recovered type/placement path can execute under BlastEm

Runtime extension milestones:

- **M0.7 — COMPLETE:** deterministic BlastEm runtime harness plus held-Y sprint extension with measured movement change and clean inactive fallback.
- **M0.8 — COMPLETE:** ROM expansion to 4 MiB plus runtime-visible authored avatar bytes routed through renderer/cache/VRAM/SAT during sprint only.

Active authoring milestones:

- **M0.9 — ACTIVE / integration-in-progress:** multi-frame sprite compiler, global chunk deduplication, pixel-exact retail round-trip and runtime-stable four-phase authored-pixel path proven. Native `FDDC`-driven authored sequence integration remains open.
- **M0.10 — ACTIVE:** **M0.10A COMPLETE and runtime-confirmed**. Scene-0 world spatial/collision resource can be relocated to expanded ROM with 13/13 pixel-identical gameplay screenshots. **M0.10B** is the next controlled material/type edit.

The first Total Recall vertical slice has not started.

## Active technical branch

Primary continuation branch: `m0.6c-level-stream`.

Checkpoint before documentation reconciliation: `0f6a97a2f2cf0d6525da7696f8469f84565e92d2` (`Document M10A world collision relocation proof`).

The historical sprint branch `m0.7-sprint-runtime` remains a proof branch, not the active continuation point.

## Runtime harness — CONFIRMED

A debug-capable BlastEm build is controlled through deterministic frame scripts. The harness can:

- boot canonical or generated ROMs;
- navigate title/briefing flow at fixed frames;
- inject six-button input;
- capture screenshots at absolute frames;
- compare gameplay-region pixels against the correct logical parent build;
- run at accelerated emulator speed for regression.

Representative validated sequence:

```text
930   Start
1320  A
1500  A
1680  A
1860  A
2040  A
2100  Left + Y down
2142  Y + Left up
```

Runtime regression is now mandatory for behavior/presentation/collision authoring claims.

## Player control — CONFIRMED / HIGH CONFIDENCE

Normalized input globals:

- `F6EA` previous input word — CONFIRMED
- `F6EC` current input word — CONFIRMED
- `F6EE` newly pressed edges — CONFIRMED
- `F6F0` held overlap — CONFIRMED

The player-control system is layered:

```text
normalized input
+ FB7C action/state bits
+ FB7E context/overlay bits
+ event routing
+ synchronized avatar/proxy pair
```

Player representation:

- world/render avatar via `F9F8` — HIGH CONFIDENCE
- control/collision proxy via `FB6E` — HIGH CONFIDENCE

M0.7 deliberately uses an unused six-button input rather than replacing a retail action.

## Generic entity architecture — CONFIRMED

Shared seams:

- `object+0x34` entity↔entity interaction callback — HIGH CONFIDENCE
- `object+0x38` entity↔world/structure collision callback — HIGH CONFIDENCE
- `object+0x50` 8-way facing `0..7` — CONFIRMED
- `object+0x2A` archetype/stat identity — CONFIRMED
- `object+0x2C` animation descriptor pointer — CONFIRMED

Generic pool:

- record size `0x72`
- 35 records
- pool base `FFFFF9FE`
- free-list head `FFFFF9FC`
- active count `FFFFF9F2`
- active-list sentinel `FFFFF9F4`
- allocator `0x00F732`
- linked allocator `0x00F7CC`
- destroy/free `0x00F8F8`
- active-list insertion `0x00FA40`

The 35-slot pool is a real Total Recall design budget.

## Weapons — CONFIRMED

`FFFFFB8C` is the even-offset selector and `FFFFFB8E` the ownership mask.

| FB8C | Weapon | Own bit | Ammo | Handler |
|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | `0x008E1C` |

## Persistent scene-object stream — CONFIRMED / AUTHORABLE

All 19 retail scenes parse structurally.

- 2,449 placements
- 128 placed `type_id`s
- 1,689 six-byte records
- 760 eight-byte records
- Y-sorted spatial materialization
- descriptor contains count, decoded offsets, compressed source and `(stride,quantity)` runs

The project can reproducibly decode, replace/remove/add, regenerate mixed strides, LZBeam-encode, relocate, patch scene pointers, repair checksum and reparse generated scenes.

## Object VM — CONFIRMED / AUTHORABLE

Most behavior uses a 72-opcode VM:

- dispatcher `0x011934`
- opcode table `0x011814–0x011933`
- representation selector `0x07A33C`
- type pointer table `0x07953E`

Assembler/disassembler round-trip covers 136 scripted IDs and 27,818 reachable instruction addresses, with exact re-encoding of all retail-reached opcodes.

## Semantic catalog / spawn graph — PARTIAL BUT PRODUCTION-USEFUL

Structural coverage: all 128 placed IDs / 2,449 placements.

Persisted semantic state:

- 58 explicitly named identities from mechanical/direct evidence;
- 37 IDs intentionally unresolved at broad authoring-class level rather than guessed from graphics;
- pickups, objective items, doors, controllers, civilians, ranged actors, spread actors, hazards/destructibles, vehicle/loot props and bosses separated mechanically.

Constant spawn graph:

- 58 parent types with proven children
- 79 unique parent→child edges
- 42 runtime-only child types

## Gameplay map / LZBeam authoring — CONFIRMED

LZBeam decoding and deterministic encoding are implemented.

M0.6G/H prove:

```text
retail map
→ decode
→ controlled no-op/edit
→ encode
→ relocate
→ pointer patch
→ checksum
→ exact re-decode
```

## Animation / sprite renderer — CONFIRMED and runtime-authorable

Mapping pieces are 4 bytes:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Each piece renders one fixed **16×16** chunk = 128 bytes = four Genesis tiles.

Piece word:

- bit15 V flip
- bit14 H flip
- bits13..8 resource group
- bits7..0 chunk index

The renderer uses a dynamic VRAM chunk cache keyed by `piece_word & 0x3FFF`.

### M0.8 runtime authored graphics — COMPLETE

The 4 MiB runtime build proves authored avatar bytes can replace the active sprint presentation only while Y is active, with exact gameplay convergence after Y release.

Audited build:

```text
output SHA-1 a540621010aa529fc2371f6c7f433f6fa1cafbac
ROM size      4,194,304
checksum      0x934F
raw bank      0x210000
avatar desc   0x0F0000
```

## M0.9 sprite sequence authoring — ACTIVE

`tools/build/sprite_sequence_compiler.py` supports multiple source frames and emits:

- one shared raw 16×16 chunk bank;
- one mapping record per frame;
- global cross-frame chunk deduplication;
- cost/working-set manifest.

Pixel-exact retail round-trip proof on four player frames:

```text
frames                    4
global unique chunks      6
chunk bytes               768
max per-frame working set 2
piece count per frame     2
```

### M09B2 — runtime-confirmed multi-phase authored pixels

M09B2 retains retail mapping/geometry and selects among four authored banks while Y is held. Separate cache namespaces prevent stale retail/phase data from masking new bytes.

Regression against M07C:

- pre-Y frame 2098: 0 gameplay-region pixel difference
- active frames 2102–2140: avatar-local non-zero authored differences
- maximum active difference box ~30×17 px
- post-Y frame 2144: 0 gameplay-region difference

This proves time-varying authored player pixels can execute stably.

### M0.9 remaining gate

Do **not** replace the player control/proxy descriptor wholesale. M09A showed that full descriptor replacement can cause world/camera divergence.

Next proof: **M0.9C** — integrate authored mapping/chunk sequence through native `FDDC` progression while preserving retail player descriptor/control semantics.

## M0.10 world collision authoring — ACTIVE

### M0.10A — runtime-confirmed relocation

Scene-0 world spatial resource:

```text
scene record  0x013B9A
field         scene+0x0E
retail base   0x07A42E
next base     0x07C7EB
length        0x23BE = 9,150 bytes
relocated to  0x230000
```

Only `scene+0x0E` is redirected; retail bytes remain untouched.

Audited build:

```text
output SHA-1 38f586b8478487a1662326054764bbe6f3631ce7
ROM size     4,194,304
checksum     0x16C5
```

Runtime comparison at frames 2098, 2102, 2106, 2110, 2114, 2118, 2122, 2126, 2130, 2134, 2138, 2140 and 2144 is **13/13 pixel-identical**.

This proves `scene+0x0E` is a safe runtime relocation seam.

Base world record layout — CONFIRMED:

```text
+0x00 word world_type
+0x02 word x_min
+0x04 word y_min
+0x06 word x_max
+0x08 word y_max
```

Coordinates are world pixels.

### Broadphase constraint

The dense 64×64 grid is not a trivial rasterization of record rectangles. Retail overlap/priority pruning is not fully recovered. Therefore full grid regeneration is **not authorized**.

### M0.10B next proof

Change one existing world record:

```text
world_type 9 → 10
```

while preserving geometry and current grid membership.

Expected isolation:

- player collision remains normal;
- projectile collision differs/pass-through behavior changes.

Runtime proof must demonstrate the semantic projectile change without player locomotion regression.

## Audio

Maxmus `T Bardo 1993 V2.1a` is confirmed. Exact 68000↔Z80 command API, sequence encoding and production authoring path remain unresolved.

## Highest-value next work

1. **M0.10B** controlled world material/type edit with runtime validation.
2. **M0.9C** native authored player sequence integration through `FDDC`.
3. Promote proof pixels into a deterministic Quaid source-art compiler and coherent original animation.
4. Add VRAM-cache/sprite-per-line budget assertions to production art builds.
5. Continue collision/material/objective-script recovery and unresolved semantic classification only where it advances authoring.
6. Start the Total Recall vertical slice only after the player-art and collision seams are deterministic and regression-protected.
