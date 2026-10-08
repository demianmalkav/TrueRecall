# Object Archetype / Animation System

True Lies separates placement `type_id` from a runtime archetype key stored in the live entity. The new allocator analysis resolves how these layers relate at object creation and how scripts may later diverge them.

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

VM native wrapper `0x002436` passes a word argument to this setter, so scripts can change archetype declaratively during the entity lifecycle.

The world/avatar player path also calls `0x00F9D4` directly with archetype ID `0x00BF` (191).

## Initial placement archetype — CONFIRMED

For normal scene placements, **initial archetype ID equals placement `type_id`.**

The materializer masks the placement source word with `0x03FF` and calls generic allocator `0x00F732` with that value in `D0`. The allocator preserves `D0`, clears/initializes the object, reads an auxiliary per-type byte from `0x07A158`, and then calls `0x00F9D4` before the object VM script begins.

Startup chain:

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

This makes the initial presentation/stat identity directly addressable from the placement class.

Reproducible probe: `tools/rom_probe/initial_visual_probe.py`.

## Lifecycle archetype changes — CONFIRMED

A reachable call to VM native `0x2436` is **not automatically the initial identity** of a placement. It may be a damage, destruction, transformation or other later state.

This distinction resolves the earlier apparent mismatch where archetypes `166` and `176–178` were reached by hundreds of placements yet rendered as effect/destruction-like graphics.

Use this terminology:

```text
initial archetype  = type_id assigned by F732/F9D4 before script execution
reachable archetype = later value assigned by VM native 0x2436
```

The previously recovered rows for archetypes 8/166/176/177/178 are therefore **reachable lifecycle archetype families**, not default type→archetype mappings.

## Difficulty-dependent stats — CONFIRMED

Routine `0x001EEC` reads `object+0x2A` and indexes difficulty-dependent tables selected by `FC4A`:

```text
FC4A = 0 -> Normal
FC4A = 1 -> Hard
```

| Purpose | Normal | Hard |
|---|---:|---:|
| HP byte table | `0x07A066` | `0x079F74` |
| damage byte table | `0x079E82` | `0x079D90` |

The routine writes:

```text
object+0x6C = HP
object+0x6E = damage / impact value
```

These meanings are independently confirmed by the health-pickup script and entity-hit logic around `0x00287A`.

VM native `0x204E` is a wrapper around this stat initializer. Many scripts call it while the initial `type_id` archetype is still active, which means the type's own table row defines its starting HP/damage unless a prior lifecycle archetype change occurs.

The player archetype `191` has HP 23 on both Normal and Hard, matching the independently recovered health cap.

## Recovered reachable lifecycle families

The control-flow-aware archetype probe currently proves constant script-set transitions to:

| Reachable archetype | Descriptor | Source type IDs | Placements | HP N/H | Damage N/H |
|---:|---:|---|---:|---:|---:|
| 8 | `0x0DFD48` | 46 | 4 | 6 / 8 | 0 / 0 |
| 166 | `0x12E720` | 6,11,20,37,41,49,50,84,86,89,90,91,99,102,103,105,108,109,110,111,119,120,128 | 260 | 1 / 1 | 0 / 0 |
| 176 | `0x1008CE` | 26,29,31,113,130 | 229 | 1 / 1 | 5 / 5 |
| 177 | `0x1008CE` | 44 | 137 | 1 / 1 | 5 / 5 |
| 178 | `0x1008CE` | 19 | 16 | 1 / 1 | 2 / 2 |

Archetypes `176`, `177` and `178` intentionally share descriptor `0x1008CE` while retaining distinct stat-table rows. Archetype is therefore broader than a pure sprite-set ID.

## Initial animation selector — conservative recovered subset

`initial_visual_probe.py` also recognizes the canonical animation native `0x1F9A` when its selector is constant in the straight-line entry prefix before the first VM control-flow split.

Across the 128 placed retail type IDs:

- 50 have a selector proven by this conservative rule;
- they account for 570 of 2,449 placements;
- 71 encounter a conditional-flow opcode first;
- the remaining cases are direct-code or other early flow forms.

Absence from this subset does not mean the object lacks an initial animation; it means CFG-aware state analysis is required.

The recovered subset independently renders coherent initial objects including keys, passcards, doors, pickups, trucks and barrels when using:

```text
archetype = type_id
selector = proven initial selector
```

Generated sprite images remain local/debug artifacts and are not committed to the repository.

## Presentation chain — CONFIRMED through renderer

The descriptor/mapping chain beneath `object+0x2C` is now substantially recovered:

```text
archetype/type ID
→ descriptor 0x079906[id]
→ animation selector / alias
→ mapping record
→ 4-byte pieces
→ 128-byte 16×16 chunks
→ dynamic VRAM cache
→ Genesis SAT
```

See `ANIMATION_FORMAT.md` and `SPRITE_RENDERER.md`.

## Production consequence for Total Recall

A future entity schema should explicitly separate:

```text
placement type_id             -> initial class + initial archetype
initial animation/state       -> presentation at spawn
behavior VM script            -> state machine / constructor logic
reachable lifecycle archetypes -> damage/destruction/transformation states
HP/damage profiles            -> archetype-indexed stats
callbacks                     -> actor/world interaction interfaces
```

This is useful for Total Recall because an object can reuse behavior while changing presentation/stats through lifecycle states without requiring a new hardcoded 68000 class for every visual variant.

## Next objectives

1. Extend initial-selector recovery through safe CFG branches.
2. Recover initial presentation for all placed type IDs.
3. Cross-correlate initial visuals with callback families, VM natives and scene distribution.
4. Classify actors/props only when behavior and presentation independently agree.
5. Decode remaining palette/priority provenance for true-color runtime-equivalent sprite export.
