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
- Audio signature: `MAXMUS T Bardo 1993 V2.1a` at `0x0134A2`

## Milestone state

Completed foundation:
- M0.1 ROM validated
- M0.2 static landmarks recovered
- M0.3 entity architecture recovered
- M0.4 asset/cutscene pipeline recovered
- M0.5 gameplay map format recovered

Active M0.6 has advanced beyond player-control recovery into static authoring:
- **M0.6A** static player-control architecture recovered
- **M0.6B** held-input, weapon-cycle direction and dual-player-object architecture recovered
- **M0.6C** object stream / object VM / archetype / animation / renderer reconstruction
- **M0.6D** controlled in-place VM/data patch
- **M0.6E** source-level VM relocation/edit/reassembly
- **M0.6F** new independently addressable scripted type in unused slot
- **M0.6G/H** gameplay map LZBeam relocation + one-tile authored edit
- **M0.6I/K** placement replacement/insertion/mixed-stride descriptor regeneration
- **M0.6L** declarative scene-object compiler
- **M0.6M** new scripted class placed directly into a persistent level stream

All M0.6D–M static build proofs are structurally reproducible but **runtime-unvalidated**.

Next formal gate:
- **M0.7** runtime-validated controlled engine extension / genuinely new behavior or player state/animation.

## Core architecture — CONFIRMED / HIGH CONFIDENCE

- `object+0x34`: entity↔entity interaction callback — HIGH CONFIDENCE.
- `object+0x38`: entity↔world/structure collision callback — HIGH CONFIDENCE.
- `object+0x50`: 8-way facing `0..7` — CONFIRMED.
- Player initialization near `0x0081C0` installs `+0x34 = 0x00356C`, `+0x38 = 0x003750`, `+0x50 = 4`.
- Generic `+0x34` invocation loop near `0x00EBC2`.
- Generic `+0x38` invocation loop near `0x010FF2`.
- Active gameplay entities use a doubly linked circular list rooted at `F9F4`; free objects use a separate free list at `F9FC` — CONFIRMED.

## Generic entity pool — CONFIRMED

The generic gameplay pool is fully bounded by static evidence:

- record size: `0x72` bytes = **114 bytes**
- records: **35**
- total allocation: `0x0F96` bytes (`35 × 0x72`)
- pool base: `FFFFF9FE`
- free-list head: `FFFFF9FC`
- active-object count: `FFFFF9F2`
- active-list sentinel: `FFFFF9F4`
- active list: `object+0x00` next / `object+0x02` previous
- allocator: `0x00F732`
- linked/clone allocator: `0x00F7CC`
- destroy/free: `0x00F8F8`
- active-list insertion: `0x00FA40`

Reproducible probe: `tools/rom_probe/entity_pool_probe.py`.

Static scene analysis has found a retention-window upper bound that can reach all 35 generic slots in retail content. This is not proof of simultaneous runtime occupancy, but it means Total Recall design must treat the 35-slot pool as a real resource budget.

## Player control — M0.6A/B

The player-control system is layered, not a single enum:

```text
normalized input
+ FB7C action/state bitfield
+ FB7E overlay/context flags
+ per-frame D7 event bits
+ synchronized avatar/proxy entity pair
```

### Normalized input

- `F6EA`: previous input word — CONFIRMED
- `F6EC`: current input word — CONFIRMED
- `F6EE`: pressed edges — CONFIRMED
- `F6F0`: continuously held overlap (`current & previous`) — CONFIRMED
- `F6EE = current & (current XOR previous)` — CONFIRMED
- D-pad mask `0x000F` — CONFIRMED
- Fire edge bit 4 — CONFIRMED
- Roll edge bit 5 — CONFIRMED
- Lock held bit 6 in current word — HIGH CONFIDENCE
- weapon cycle bit 12 = next owned weapon (`+2`) — CONFIRMED
- weapon cycle bit 14 = previous owned weapon (`-2`) — CONFIRMED

### Dual player entities

The player is represented by two linked engine objects:

- `F9F8`: world/render avatar entity — HIGH CONFIDENCE
- `FB6E`: control/collision proxy/companion entity — HIGH CONFIDENCE

Evidence includes separate creation paths (`0x0109D0` and `0x008284`), promotion of the newly allocated companion to `A5` in `0x00F8E8`, explicit suppression of collision with `F9F8` in callback `0x00356C`, and bidirectional synchronization around `0x009B60–0x009C98`.

Motion fields `+0x18/+0x1A/+0x56` flow proxy→avatar; position/geometry fields can flow avatar→proxy. This split is likely important for safely extending movement and melee without destabilizing rendering/world interaction.

Reproducible probe: `tools/rom_probe/player_links_probe.py`.

### Action/overlay words

`FB7C` is a 16-bit action bitfield; `FB7D` is its low byte. Confirmed structural values include `0x0000` idle, `0x0002` walking, `0x0004` normal weapon fire and several special-weapon/action combinations.

`FB7E` is a separate 16-bit context/overlay word; `FB7F` is its low byte.

- bit `0x0001`: roll active phase — HIGH CONFIDENCE
- bit `0x0002`: post-roll transition — HIGH CONFIDENCE
- bit `0x0004`: roll-fire/kneeling-fire context — CONFIRMED
- bit `0x0040`: JLLBFR alternate-player/maniac overlay — HIGH CONFIDENCE
- bit `0x0080`: lock/fire pose latch — HIGH CONFIDENCE

Higher bits participate in terminal/special sequences and remain intentionally unnamed at cause level.

### Roll-fire / Lock / hit routing

Roll begins at `0x008600`, uses animation `0x0142`, and can enter a secondary weapon dispatcher when Fire is held. Lock is an overlay rather than a separate state. Post-hit protection begins at `0x009714` (`FB90=24`, `FB92=1`, object flag change) and is maintained by `0x009CA0`.

At least 27 active action sites converge on `0x009244` for terminal events masked by `D7 & 0x63`. The mask is a terminal-event mask, not a pure death mask.

Reproducible control probe: `tools/rom_probe/player_state_probe.py`.

## Weapons — CONFIRMED

Weapon selector `FFFFFB8C` uses even offsets `0,2,4,6,8,10`; ownership mask is `FFFFFB8E`.

| FB8C | Weapon | Ownership bit | Ammo | Primary handler |
|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | `0x008E1C` |

## Persistent scene-object stream — CONFIRMED

All 19 retail scenes parse structurally.

- total placements: **2,449**
- used placement `type_id`s: **128**
- 6-byte records: **1,689**
- 8-byte records: **760**
- placement stream is Y-sorted and spatially materialized by the engine
- status low 10 bits = `type_id`; upper bits retain placement/runtime flags
- descriptor stores count, start/end offsets, LZBeam source and `(stride,quantity)` runs

The project can preserve or regenerate mixed stride runs and relocate both descriptor and compressed stream.

Docs/tools: `docs/OBJECT_STREAM.md`, `tools/rom_probe/level_objects_probe.py`, `tools/build/object_stream_codec.py`.

## Object VM — CONFIRMED / AUTHORABLE

Most object behavior is data-driven through a 72-opcode VM:

- VM dispatcher: `0x011934`
- opcode jump table: `0x011814–0x011933`
- type representation selector: `0x07A33C`
- type pointer table: `0x07953E`

The VM supports data access, arithmetic/logical operations, branching, subroutines, stack operations and native calls.

The assembler/disassembler round-trip probe covers **136 scripted type IDs**, **27,818 reachable instruction addresses** and all **53 of 72 opcodes used by retail**, with exact re-encoding of reachable retail bytecode.

This makes object scripts source-representable rather than opaque ROM blobs.

Docs/tools: `docs/OBJECT_VM.md`, `docs/VM_AUTHORING.md`, VM tools under `tools/rom_probe/`.

## Archetype / animation / stats — CONFIRMED

Generic placement allocation initializes **initial archetype ID = placement type_id**.

`0x00F9D4` stores:

- `object+0x2A` archetype ID;
- descriptor from master table `0x079906` into `object+0x2C`;
- reset animation-state fields.

Archetype ID also indexes difficulty-dependent HP and damage tables through `0x001EEC`, proving it is broader than a pure graphics ID.

Later VM `SetArchetype` calls are lifecycle transitions and must not be confused with initial identity.

## Animation / sprite renderer — CONFIRMED enough for export

Animation descriptors resolve selector aliases into variable-size mapping records. A record has a 16-byte header plus `N × 4-byte` pieces.

Each piece is a fixed **16×16** Genesis sprite chunk:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Piece word:
- bit15 V flip
- bit14 H flip
- bits13..8 graphics resource group
- bits7..0 chunk index

Each chunk is 128 bytes / four 8×8 tiles. Sources can be contiguous raw data or indexed per-chunk data with a small 128-byte RLE codec. The renderer dynamically caches chunks in VRAM and uses one four-tile slot per chunk.

True-color diagnostic reconstruction works when scene CRAM is supplied. Rendered retail assets remain local and are not committed.

Docs: `docs/ANIMATION_FORMAT.md`, `docs/SPRITE_RENDERER.md`.

## Semantic object catalog — PARTIALLY RECOVERED

Current machine-readable authoring catalog covers all **128 placed type IDs / 2,449 placements** structurally.

- named identities with direct evidence: **58**
- broad classes include pickups, objective items, doors/interactables, civilians, hostile shooters, hazards/destructibles, controllers and vehicle/loot props
- 37 type IDs remain deliberately unresolved at broad authoring-class level

Confirmed examples include standard weapon/ammo pickups, health/life, mission keys/passcards and their gates, the subway lever/signal box, truck, loot crate, multiple mission controllers, civilian families and ranged/spread combat families.

Policy: no semantic name is frozen from sprite appearance alone.

Probe/summary: `tools/rom_probe/semantic_catalog_probe_v3.py`, `extracted_metadata/semantic_catalog_v3_summary.json`.

## Spawn graph — CONFIRMED structural graph

The VM exposes six generic allocation/spawn wrappers. The constant reachable spawn graph currently contains:

- **58** parent types with at least one proven child
- **79** unique parent→child edges
- **42** runtime-only child types
- only child types `54` and `68` are also normal retail placement classes

This cleanly separates persistent scene classes from transient projectiles/components/effects.

Examples:
- supply crate `113` → health `54` / shotgun ammo `68`
- standard shooters → runtime projectile `170`
- spread shooters → runtime projectile `175`
- boss-class `104` → projectile `225`
- truck `46` → shared destruction/effect child `227`

Docs/probe: `docs/SPAWN_GRAPH.md`, `tools/rom_probe/spawn_graph_probe_v2.py`.

## Asset pipeline — CONFIRMED / BIDIRECTIONAL for maps

- Beam LZBeam decode is validated against the ROM.
- A TrueRecall encoder emits valid deterministic streams that re-decode exactly.
- Strict scan found 101 structurally valid tile-aligned retail candidates.
- Full-screen cutscenes use `LZ tiles + LZ 32×28 tilemap + raw 128-byte CRAM + auxiliary/caption pointer`.
- Cutscene sequence table begins at `0x00AC3A`; fourteen full-color frames have been reconstructed.

Gameplay map format is recovered across independent packages. More importantly, M0.6G/H prove the inverse path:

```text
retail map → decode → edit/no-op → encode → relocate → pointer patch → checksum → exact re-decode
```

M0.6H changes exactly one tile word in a real 107×45 plane and validates that no other decoded tile word changes.

## Static authoring proofs M0.6D–M

The project now has reproducible static proof for increasingly strong operations:

- **D**: one controlled retail VM/data constant change
- **E**: export VM source, edit, reassemble in free ROM space, redirect type pointer
- **F**: create a new scripted class in unused `type_id 1`
- **G/H**: relocate/reinsert map and author exactly one tile
- **I**: replace one placement class while preserving stream layout
- **J**: insert a new six-byte placement
- **K**: introduce an eight-byte placement and regenerate/relocate descriptor
- **L**: declarative JSON scene-object compiler supporting replace/remove/add
- **M**: create a new scripted class and place it directly into a persistent level stream in the same build

Key M0.6M audited output:

```text
type-1 VM script = 0x1FB000
scene-1 descriptor = 0x1FC000
scene-1 object LZ = 0x1FC00C
placements = 72 → 73
checksum = 0x3CF5
SHA-1 = dc672e205686957c0c17655a387e7ea211eb9ef6
```

No generated ROM is committed.

## Runtime validation status — BLOCKING M0.7

The static pipeline is ahead of runtime validation. The current analysis container has no installed Genesis emulator. Current BlastEm Linux builds and a debug-capable fork have been identified, including headless/debug support, but binary retrieval is blocked by the container's network/download restrictions.

Therefore:

- static authoring proofs remain valid;
- they are **not** promoted to runtime-complete production guarantees;
- M0.7 remains gated on emulator/hardware execution of baseline and modified builds.

## Highest-value next work

1. Establish a repeatable BlastEm/Genesis runtime smoke-test path and execute baseline + M0.6D–M builds.
2. Runtime-validate idle/walk/fire/roll/roll-fire/Lock/invulnerability/terminal routing.
3. Use debugger/runtime watches to confirm object materialization, pool occupancy and newly inserted placements.
4. Continue semantic classification of the 37 unresolved placement classes without visual-only naming.
5. Decode remaining collision/material and mission scripting structures needed for a complete level authoring schema.
6. After runtime closure, implement M0.7 as a genuinely new isolated mechanic/state/animation rather than another cloned-data proof.
