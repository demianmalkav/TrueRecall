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

Completed reconstruction / authoring chain:

- **M0.6A/B** player input/control architecture and dual-player-object model
- **M0.6C** object stream / VM / archetype / animation / renderer reconstruction
- **M0.6D** controlled in-place VM/data patch
- **M0.6E** source-level VM relocation/edit/reassembly
- **M0.6F** new independently addressable scripted type in an unused slot
- **M0.6G/H** gameplay-map LZBeam relocation and one-tile authored edit
- **M0.6I/J/K** placement replacement, insertion and mixed-stride descriptor regeneration
- **M0.6L** declarative scene-object compiler
- **M0.6M** new scripted class placed directly into a persistent level stream
- **M0.6O and subsequent runtime probes** proved that the recovered type/placement path can execute under BlastEm and that inserted/synthetic objects can be observed at runtime

Runtime extension milestones:

- **M0.7 — COMPLETE:** deterministic BlastEm runtime harness plus a new input-driven player sprint extension. Y activates a new code path, larger movement and a separately addressable animation row; frame-level comparison proves the extension executes and cleanly falls back when inactive.
- **M0.8 — COMPLETE:** ROM expansion to 4 MiB plus runtime-visible authored avatar sprite bytes routed through the recovered renderer/cache/VRAM path. The authored pixels affect only the avatar during Y and return to exact gameplay equivalence when Y is released.

Current production direction:

- replace diagnostic authored pixels with a proper Quaid source-asset compiler and coherent animation;
- keep strengthening scene/entity authoring and runtime regression coverage;
- continue unresolved semantic classification and mission/collision scripting recovery in parallel.

## Runtime harness — CONFIRMED

A debug-capable BlastEm build is installed in the analysis environment and controlled through its Unix socket / deterministic frame scripts. The harness can:

- boot the canonical or generated ROM;
- navigate title/briefing flow at fixed frame numbers;
- inject six-button input;
- capture screenshots at absolute frames;
- run at the configured 400% speed slot for fast regression;
- compare gameplay pixels against the correct parent build.

Representative deterministic navigation:

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

The harness distinguishes gameplay-region equivalence from small timing noise in non-gameplay/HUD rows.

## Player control — CONFIRMED / HIGH CONFIDENCE

Normalized input globals:

- `F6EA` previous input word — CONFIRMED
- `F6EC` current input word — CONFIRMED
- `F6EE` newly pressed edges — CONFIRMED
- `F6F0` held overlap — CONFIRMED

The player-control system is layered rather than a single enum:

```text
normalized input
+ FB7C action/state bits
+ FB7E context/overlay bits
+ per-frame event routing
+ synchronized avatar/proxy entity pair
```

The player is represented by two linked entities:

- world/render avatar via `F9F8` — HIGH CONFIDENCE
- control/collision proxy via `FB6E` — HIGH CONFIDENCE

Observed runtime addresses in the validated gameplay path included avatar `0xFFC632` and proxy `0xFFC6A4`.

Roll, roll-fire, Lock overlay, weapon cycling and post-hit protection have mapped static seams. The Y sprint proof deliberately uses an unused six-button input and does not replace an existing retail action.

See `docs/PLAYER_SYSTEM.md` and `docs/M07_RUNTIME_SPRINT.md`.

## Generic entity architecture — CONFIRMED

Shared per-object seams:

- `object+0x34`: entity↔entity interaction callback — HIGH CONFIDENCE
- `object+0x38`: entity↔world/structure collision callback — HIGH CONFIDENCE
- `object+0x50`: 8-way facing `0..7` — CONFIRMED
- `object+0x2A`: archetype/stat identity — CONFIRMED
- `object+0x2C`: animation descriptor pointer — CONFIRMED

Generic pool:

- record size `0x72` bytes
- 35 records
- pool base `FFFFF9FE`
- free-list head `FFFFF9FC`
- active count `FFFFF9F2`
- active-list sentinel `FFFFF9F4`
- allocator `0x00F732`
- linked allocator `0x00F7CC`
- destroy/free `0x00F8F8`
- active-list insertion `0x00FA40`

The 35-slot pool is a real Total Recall design budget; retail retention geometry can approach the full pool.

## Weapons — CONFIRMED

`FFFFFB8C` is an even-offset selector and `FFFFFB8E` is the ownership mask.

| FB8C | Weapon | Own bit | Ammo | Handler |
|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | `0x008E1C` |

The weapon system is table-driven and remains a major future Total Recall extension seam.

## Persistent scene-object stream — CONFIRMED / AUTHORABLE

All 19 retail scenes parse structurally.

- total placements: **2,449**
- placed `type_id`s: **128**
- 6-byte records: **1,689**
- 8-byte records: **760**
- stream is Y-sorted and spatially materialized
- descriptor contains count, decoded offsets, compressed source and `(stride, quantity)` runs

The project can now reproducibly:

- decode a scene object stream;
- replace/remove/add placements;
- insert both 6-byte and 8-byte records;
- regenerate mixed-stride runs;
- LZBeam-encode the result;
- relocate descriptor + stream;
- patch scene pointers;
- repair checksum;
- re-decode and verify the generated ROM.

M0.6M additionally combines a synthetic scripted class with a newly inserted persistent placement.

## Object VM — CONFIRMED / AUTHORABLE

Most object behavior is data-driven through a 72-opcode VM:

- dispatcher `0x011934`
- opcode table `0x011814–0x011933`
- representation selector `0x07A33C`
- type pointer table `0x07953E`

The assembler/disassembler round-trip covers 136 scripted IDs, 27,818 reachable instruction addresses and all 53 opcodes used by retail scripts, with exact re-encoding of reachable code.

This makes object behavior source-representable rather than opaque binary data.

## Semantic catalog / spawn graph — PARTIALLY RECOVERED

The machine-readable catalog structurally covers all 128 placed IDs / 2,449 placements.

Current persisted semantic coverage includes:

- 58 explicitly named identities from direct/mechanical evidence;
- pickups, objective items, keys/passcards, doors, controllers, civilians, shooters, hazards/destructibles, vehicle/loot props and bosses;
- 37 IDs intentionally unresolved at broad authoring-class level rather than guessed from graphics.

The constant spawn graph currently contains:

- 58 parent types with proven children;
- 79 unique parent→child edges;
- 42 runtime-only child types.

Examples:

- supply crate `113` → health `54` / shotgun ammo `68`
- standard ranged actors → projectile `170`
- spread actors → projectile `175`
- boss-class `104` → projectile `225`
- truck `46` → shared destruction child/effect `227`

Policy remains: appearance alone does not freeze semantic names.

## Gameplay map / LZBeam authoring — CONFIRMED

Beam LZBeam decoding and deterministic encoding are both implemented.

Gameplay maps have proven two-layer 16-bit tilemap packages; examples include `107×45` and `50×39` maps.

M0.6G/H prove the inverse path:

```text
retail map
→ decode
→ controlled edit/no-op
→ encode
→ relocate
→ patch pointer
→ checksum
→ exact re-decode
```

M0.6H changes exactly one decoded tile word while preserving every other map word.

## Animation / sprite renderer — CONFIRMED and runtime-authorable

Animation mappings resolve into variable-size records made of fixed 4-byte pieces:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Each piece renders as one fixed **16×16** Genesis sprite chunk = 128 bytes = four 8×8 tiles.

Piece word:

- bit15 V flip
- bit14 H flip
- bits13..8 resource group
- bits7..0 chunk index

The renderer uses a dynamic VRAM chunk cache keyed by `piece_word & 0x3FFF`.

Critical retail seam near `0x01143C`:

```text
MOVEA.L 0x2C(A6),A0
MOVE.L  0x02(A0,D1.W),D1
```

This identifies `A6` as the render entity and `A0` as the active descriptor used for graphics-source resolution.

### M0.8 runtime authored graphics — CONFIRMED

The runtime build expands the ROM to 4 MiB and places an authored raw chunk bank at `0x210000`.

A scoped alternate cache namespace (`0x3F00 | chunk_index`) prevents old retail VRAM-cache entries from masking changed source bytes.

Differential descriptor sweep identified `0x0F0000` as the avatar descriptor for the validated sprint path:

- frame 2098 before Y: **0 gameplay pixels different**
- frames 2102–2140 with Y active: **206–360 gameplay pixels different per sampled frame**, localized to an avatar-sized ~32×32 moving region
- frame 2144 after Y release: **0 gameplay pixels different**

Other tested descriptors behaved differently:

- `0x0CA38C`: no gameplay difference
- `0x0F6FD4`: changes a separate small moving object, not the avatar

Audited build:

```text
base SHA-1   d39174bed46ede85531b86df7ba49123ce2f8411
output SHA-1 a540621010aa529fc2371f6c7f433f6fa1cafbac
ROM size      4,194,304
checksum      0x934F
raw bank      0x210000
avatar desc   0x0F0000
```

See `docs/M08_RUNTIME_AUTHORED_GRAPHICS.md`, `tools/build/m08_runtime_authored_sprint_pixels.py` and `extracted_metadata/m08_runtime_authored_sprint.json`.

## Audio

Maxmus `T Bardo 1993 V2.1a` is confirmed. The exact 68000↔Z80 command API, sequence encoding and authoring path remain unresolved.

## Highest-value next work

1. Replace M0.8 diagnostic pixel mutations with a proper **Quaid source-asset compiler**: image/sprite-sheet → 16×16 pieces → deduplicated chunks → group/index IDs → mapping records → animation row.
2. Build one coherent new Quaid animation (not just a diagnostic frame mutation) and validate it under the same Y-state runtime harness.
3. Measure VRAM-cache pressure and sprite-per-line cost for the authored animation.
4. Extend the scene authoring schema to collision/material/objective-script layers that are still unresolved.
5. Continue semantic classification of the remaining unresolved placement IDs using mechanical/runtime evidence.
6. Begin the first Total Recall vertical-slice environment only after the player-art pipeline is deterministic and regression-protected.
