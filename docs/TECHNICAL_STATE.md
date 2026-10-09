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
- **M0.10 — ACTIVE:** M0.10A/B are runtime-confirmed. **M0.10C broadphase serialization is now statically recovered exactly and a cross-cell geometry build is reproducible; runtime validation of that geometry build remains pending.**

The first Total Recall vertical slice has not started.

## Active technical branch

Primary continuation branch: `m0.6c-level-stream`.

The latest structural collision proof is M0.10C. Read branch head before new writes; do not rely on older checkpoint SHAs embedded in past handoffs.

The historical sprint branch `m0.7-sprint-runtime` remains a proof branch, not the active continuation point.

## Runtime harness — CONFIRMED

A debug-capable BlastEm build is controlled through deterministic frame scripts. The harness can boot canonical/generated ROMs, navigate title/briefing flow at fixed frames, inject six-button input, capture screenshots at absolute frames and compare logical parent/child builds.

Representative boot path:

```text
930   Start
1320  A
1500  A
1680  A
1860  A
2040  A
```

Runtime regression is mandatory for behavior/presentation/collision authoring claims.

Current environment note: this container no longer has the debug BlastEm binary used for M0.7–M0.10B and has no direct DNS egress. M0.10C therefore remains static-only until the runtime harness is restored; this is an environment limitation, not an engine ambiguity.

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

LZBeam decoding and deterministic encoding are implemented. M0.6G/H prove the complete decode→edit→encode→relocate→reparse path for gameplay tilemaps.

## Animation / sprite renderer — CONFIRMED and runtime-authorable

Mapping pieces are 4 bytes:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Each piece renders one fixed 16×16 chunk = 128 bytes = four Genesis tiles. The renderer uses a dynamic VRAM chunk cache keyed by `piece_word & 0x3FFF`.

### M0.8 runtime authored graphics — COMPLETE

The 4 MiB runtime build proves authored avatar bytes can replace active sprint presentation only while Y is active, with exact gameplay convergence after Y release.

```text
output SHA-1 a540621010aa529fc2371f6c7f433f6fa1cafbac
ROM size      4,194,304
checksum      0x934F
raw bank      0x210000
avatar desc   0x0F0000
```

## M0.9 sprite sequence authoring — ACTIVE

`tools/build/sprite_sequence_compiler.py` supports multiple source frames and emits one shared raw chunk bank, mapping records, global cross-frame deduplication and cost/working-set metadata.

Pixel-exact retail round-trip on four player frames:

```text
frames                    4
global unique chunks      6
chunk bytes               768
max per-frame working set 2
piece count per frame     2
```

M09B2 retains retail mapping/geometry and selects among four authored banks while Y is held. Pre/post-Y frames converge exactly with the M07C parent; active differences remain avatar-local.

M0.9C remains: integrate an authored mapping/chunk sequence through native `FDDC` progression while preserving retail player descriptor/control semantics.

## M0.10 world collision authoring — ACTIVE

### M0.10A — runtime-confirmed relocation

Scene-0 world resource:

```text
scene record  0x013B9A
retail base   0x07A42E
next base     0x07C7EC
length        0x23BE = 9,150 bytes
relocated to  0x230000
```

A deterministic 13-frame gameplay comparison is pixel-identical.

### M0.10B — runtime-confirmed local collision behavior

World record base layout:

```text
+0x00 world_type
+0x02 x_min
+0x04 y_min
+0x06 x_max
+0x08 y_max
```

A single `type 9 -> 11` edit at record `0x1C46` disables player collision for that rectangle; a `type 9 -> 10` edit at `0x1C6E` preserves player collision while allowing projectiles through.

### M0.10C — exact broadphase serializer — STATIC CONFIRMED / RUNTIME PENDING

Scene-0 broadphase prefix is fully recovered:

```text
0x0000..0x09B3  54×23 grid (1242 words)
0x09B4..0x1059  deduplicated cell-list pool (1702 bytes retail)
0x105A          0xFFFF sentinel
0x105C..0x1F01  375 ten-byte world records
```

Each grid cell is 64×64 pixels. Non-zero grid words point to a list whose first reference has bit15 set; continuation refs have bit15 clear. Retail contains 373 unique lists of 1..8 records.

For **all 1242 cells**, membership is exactly half-open rectangle intersection:

```text
rx0 < cell_x1 && rx1 > cell_x0 && ry0 < cell_y1 && ry1 > cell_y0
```

References are sorted by record offset descending. Unique membership tuples are emitted on first row-major encounter and deduplicated by pointer reuse.

`tools/build/world_collision_codec.py` reproduces the retail grid and full list pool byte-for-byte.

M10C proof build moves record `0x1C46` 64 pixels east:

```text
before (736,544) .. (752,800)
after  (800,544) .. (816,800)
changed semantic cell memberships: 10
list pool: 1702 -> 1698 bytes
output SHA-1 5bf78090cbc54acbed1bc70211666f5f1d1645bf
checksum 0xDAE9
```

Tool/evidence:

```text
tools/build/world_collision_codec.py
tools/build/m10c_broadphase_geometry.py
extracted_metadata/m10c_broadphase_geometry.json
docs/M10C_BROADPHASE_SERIALIZER.md
```

Runtime validation is the only remaining M10C gate.

## Audio

Maxmus `T Bardo 1993 V2.1a` is confirmed. Exact 68000↔Z80 command API, sequence encoding and production authoring path remain unresolved.

## Highest-value next work

1. Restore the deterministic BlastEm runner and runtime-validate M0.10C.
2. Generalize broadphase serializer discovery/compilation across all 19 scenes.
3. Add/serialize entirely new world records and integrate them into the declarative scene compiler.
4. Complete M0.9C native `FDDC` sequence integration.
5. Promote proof pixels into a deterministic Quaid source-art compiler and coherent original animation.
6. Add VRAM-cache/sprite-per-line budget assertions to production art builds.
7. Start the Total Recall vertical slice once player-art sequencing and arbitrary collision geometry are deterministic and regression-protected.
