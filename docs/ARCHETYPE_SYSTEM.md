# Object Archetype / Animation System

True Lies separates placement `type_id` from a second runtime key stored in the entity itself. The latter is best described as an **archetype/animation-set ID** rather than a pure graphics ID.

## Archetype setter — CONFIRMED

Routine `0x00F9D4` performs:

```text
object+0x2A = D0                 ; archetype ID
D0 *= 4
A1 = *(0x079906 + D0)           ; descriptor pointer
object+0x2C = A1                 ; animation descriptor/table
clear object+0x1C..+0x28         ; animation state fields
```

Therefore:

- `object+0x2A` = archetype/animation-set ID — CONFIRMED
- `object+0x2C` = animation descriptor/table pointer — CONFIRMED
- master archetype→descriptor table = `0x079906` — CONFIRMED
- setter = `0x00F9D4` — CONFIRMED

VM native wrapper `0x002436` passes a word argument to `0x00F9D4`, so object scripts can choose an archetype declaratively.

The world/avatar player path also calls `0x00F9D4` directly with archetype ID `0x00BF` (191).

Reproducible probe: `tools/rom_probe/object_archetype_probe.py`.

## Why this is not merely a visual ID — CONFIRMED

Routine `0x001EEC` reads `object+0x2A` and uses it to index difficulty-dependent stat tables. `FC4A` selects the table pair:

```text
FC4A = 0  -> Normal tables
FC4A = 1  -> Hard tables
```

The routine clears and then writes the low byte of two entity words:

- `object+0x6C` ← HP table value
- `object+0x6E` ← damage/impact table value

The HP interpretation is independently confirmed by the health-pickup script, which resolves the player world/avatar object and operates directly on `avatar+0x6C`.

The damage interpretation is confirmed by entity-hit logic around `0x002882`, which loads target `+0x6C` and subtracts the interacting object's `+0x6E` value before evaluating the result.

Thus the archetype ID selects both presentation and combat statistics.

## Difficulty tables — CONFIRMED

| Purpose | Normal | Hard |
|---|---:|---:|
| HP byte table | `0x07A066` | `0x079F74` |
| damage byte table | `0x079E82` | `0x079D90` |

The player archetype `191` has HP value `23` (`0x17`) in both tables, matching the health cap observed in the health-pickup bytecode.

## Recovered retail archetype families

The VM control-flow probe can currently prove constant calls to native `0x2436` for five placed archetype IDs:

| Archetype | Animation descriptor | Placed type IDs | Placements | HP N/H | Damage N/H |
|---:|---:|---|---:|---:|---:|
| 8 | `0x0DFD48` | 46 | 4 | 6 / 8 | 0 / 0 |
| 166 | `0x12E720` | 6,11,20,37,41,49,50,84,86,89,90,91,99,102,103,105,108,109,110,111,119,120,128 | 260 | 1 / 1 | 0 / 0 |
| 176 | `0x1008CE` | 26,29,31,113,130 | 229 | 1 / 1 | 5 / 5 |
| 177 | `0x1008CE` | 44 | 137 | 1 / 1 | 5 / 5 |
| 178 | `0x1008CE` | 19 | 16 | 1 / 1 | 2 / 2 |

### Descriptor aliasing

Archetypes `176`, `177` and `178` all point to the same animation descriptor `0x1008CE`, while retaining distinct archetype IDs and stat-table entries.

This is direct evidence that `object+0x2A` cannot be reduced to “sprite set”. It is an entity archetype key that can distinguish gameplay variants sharing one animation resource.

## Animation descriptor consumption — PARTIALLY RECOVERED

Routine `0x00FDDC` consumes `object+0x2C` as a word-indexed animation table. It stores animation-selection/state values in `object+0x1C/+0x1E/+0x20/+0x24/+0x26/+0x28` and interprets flag bits from descriptor words.

The descriptor's complete nested format and frame/sprite mapping chain remain under study. No graphics resource should yet be rewritten by treating `0x2C` as a flat sprite pointer.

## Production consequence for Total Recall

A future authoring format should distinguish at least three concepts:

```text
placement type_id        -> object script / behavioral class
archetype ID (+0x2A)     -> animation-set identity + difficulty stats
animation descriptor     -> actual animation presentation data
```

This separation is valuable: a new Total Recall enemy can potentially reuse an existing script family with a new archetype, or reuse an animation descriptor while changing HP/damage through a separate archetype ID.

## Next objectives

1. Decode the nested animation descriptor format consumed by `0xFDDC`.
2. Locate the sprite/mapping/tile resource chain beneath each descriptor.
3. Recover all VM-native archetype assignments, including branch-dependent assignments.
4. Cross-correlate archetype families with callback families and scene distribution.
5. Assign gameplay names only when script behavior and presentation independently agree.
