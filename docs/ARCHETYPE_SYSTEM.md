# Object Archetype / Animation System

True Lies separates placement `type_id` from a runtime archetype key stored in the live entity. Allocator, VM and renderer analysis now recover the initial presentation for almost the entire retail placement population without running the emulator.

## Archetype setter — CONFIRMED

Routine `0x00F9D4` performs:

```text
object+0x2A = D0                 ; archetype ID
D0 *= 4
A1 = *(0x079906 + D0)           ; descriptor pointer
object+0x2C = A1                 ; animation descriptor/table
clear animation-state fields
```

Therefore:

- `object+0x2A` = archetype/animation-set/stat ID — CONFIRMED
- `object+0x2C` = animation descriptor/table pointer — CONFIRMED
- master archetype→descriptor table = `0x079906` — CONFIRMED
- setter = `0x00F9D4` — CONFIRMED

VM native wrapper `0x002436` passes a word argument to the setter, so scripts can change archetype declaratively during an entity lifecycle. The world/avatar player path also calls `0x00F9D4` directly with archetype `0x00BF` (191).

## Initial placement archetype — CONFIRMED

For normal scene placements, **initial archetype ID equals placement `type_id`.**

The materializer masks the source word with `0x03FF` and calls generic allocator `0x00F732` with that value in `D0`. The allocator preserves `D0`, initializes the record and calls `0x00F9D4` before the object VM script begins.

```text
placement status/type
    ↓ & 0x03FF
D0 = type_id
    ↓ F732 allocator
F9D4 archetype setter
    ↓
object+0x2A = type_id
object+0x2C = table_079906[type_id]
    ↓
object VM behavior begins
```

This is reproduced by `tools/rom_probe/initial_visual_probe.py`.

## Lifecycle archetype changes — CONFIRMED

A reachable call to VM native `0x2436` is not automatically the placement's initial identity. It can represent damage, destruction, transformation or another later state.

Use this terminology:

```text
initial archetype   = type_id assigned by F732/F9D4 before script execution
reachable archetype = later value assigned by VM native 0x2436
```

This resolves the earlier apparent mismatch where archetypes `166` and `176–178` were reached from many placed classes but render as effect/destruction-like graphics.

## Difficulty-dependent stats — CONFIRMED

Routine `0x001EEC` indexes archetype-dependent tables selected by `FC4A`:

| Purpose | Normal | Hard |
|---|---:|---:|
| HP byte table | `0x07A066` | `0x079F74` |
| damage byte table | `0x079E82` | `0x079D90` |

It writes:

```text
object+0x6C = HP
object+0x6E = damage / impact value
```

The meanings are independently confirmed by the health-pickup script and entity-hit logic. VM native `0x204E` wraps this stat initializer. Player archetype `191` has HP 23 on both difficulties, matching the recovered health cap.

## Recovered reachable lifecycle families

The control-flow-aware archetype probe proves constant script-set transitions to several shared effect/state archetypes, including:

| Reachable archetype | Descriptor | Source type IDs | Placements | HP N/H | Damage N/H |
|---:|---:|---|---:|---:|---:|
| 8 | `0x0DFD48` | 46 | 4 | 6 / 8 | 0 / 0 |
| 166 | `0x12E720` | 6,11,20,37,41,49,50,84,86,89,90,91,99,102,103,105,108,109,110,111,119,120,128 | 260 | 1 / 1 | 0 / 0 |
| 176 | `0x1008CE` | 26,29,31,113,130 | 229 | 1 / 1 | 5 / 5 |
| 177 | `0x1008CE` | 44 | 137 | 1 / 1 | 5 / 5 |
| 178 | `0x1008CE` | 19 | 16 | 1 / 1 | 2 / 2 |

Archetypes `176`, `177` and `178` intentionally share descriptor `0x1008CE` while retaining separate stat rows. Archetype is therefore broader than a pure sprite-set ID.

## Initial presentation API — CONFIRMED

The earlier straight-line probe recognized only direct animation native `0x001F9A`. CFG analysis shows that retail objects use a small family of presentation natives:

| VM native | Working role | Engine helper |
|---:|---|---:|
| `0x001F9A` | direct animation selector | `0x00FDDC` path |
| `0x001FF6` | facing-aware animation family, set/activate | `0x001A52` |
| `0x00200C` | facing-aware animation family variant | `0x001A8E` |
| `0x002022` | direction-aware animation family | `0x001AB2` |
| `0x002448` | direction-aware animation family variant | `0x001B1C` |

`0x001FF6`, for example, stores an animation-family/base value and combines it with facing `0..7` through the direction table around `0x013F32` before reaching the common descriptor resolver. This explains why many mobile actors had no early direct `0x1F9A` call.

Reproducible probes:

- `tools/rom_probe/initial_visual_cfg_probe.py` — direct-animation CFG regression probe.
- `tools/rom_probe/initial_presentation_cfg_probe.py` — full initial presentation API.
- `extracted_metadata/initial_presentation_summary.json` — safe coverage snapshot.

### Retail coverage

Across all 128 placed retail `type_id` values, the full presentation CFG probe finds:

```text
106  unique presentation families
 14  legitimate branch-dependent initial variants
  6  no recovered initial presentation native
  2  direct-code classes
```

This resolves **2,427 of 2,449 placements = 99.1%**.

The only scripted placement classes still lacking an initial presentation native are:

```text
4, 34, 81, 100, 133, 134
```

Several of these are now strongly indicated to be mission/controller logic rather than visible actors; the distinction is documented in `OBJECT_TYPES.md`. Direct-code types remain `10` and `101`.

Generated actor/contact-sheet images remain local debug artifacts and are not committed.

## Presentation chain — CONFIRMED through renderer

```text
placement type_id
→ initial archetype = type_id
→ descriptor 0x079906[type_id]
→ direct/facing/direction presentation API
→ animation selector / alias
→ mapping record
→ 4-byte pieces
→ 128-byte 16×16 chunks
→ dynamic VRAM cache
→ Genesis SAT
```

See `ANIMATION_FORMAT.md` and `SPRITE_RENDERER.md` for the mapping/chunk formats and true-color scene-CRAM export path.

## Production consequence for Total Recall

A future entity schema should separate:

```text
placement type_id              -> initial class + archetype
initial presentation family    -> spawn pose/directional family
behavior VM script             -> state machine / constructor logic
reachable lifecycle archetypes -> damage/destruction/transformation states
HP/damage profile              -> archetype-indexed stats
callbacks                      -> actor/world interaction interfaces
```

This means Total Recall can potentially reuse a behavior class while changing presentation/stats or reuse presentation resources while supplying a different script, without a bespoke 68000 routine for every visual variant.

## Next objectives

1. Classify the remaining visible actor families by combining presentation, callbacks, VM natives, stats and messages.
2. Separate visible actors/props from invisible mission controllers in a machine-readable authoring catalog.
3. Recover projectile/fire spawning paths for mechanical hostile classification.
4. Resolve the two direct-code scene-14 classes `10` and `101`.
5. Add inverse encoding only after the presentation exporter and round-trip tests are stable.
