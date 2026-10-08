# Object Type Catalog

This document maps retail placement `type_id` values to functional identities only when the ROM itself provides enough evidence. Visual names are not assigned from guesswork.

## Standard pickup family — CONFIRMED

The standard inventory/survival pickups install actor-contact callback `0x009DF8`. Their identities and effects are recoverable from reachable object-VM code, inventory RAM, the weapon-ownership helper and the player-health field.

| type_id | Working label | Confirmed effect |
|---:|---|---|
| 51 | Flamethrower weapon pickup | grants flamethrower ownership bit `0x20`; adds 30 fuel up to 99 |
| 52 | Flamethrower fuel pickup | adds 50 fuel up to 99; no weapon-acquisition native |
| 53 | Grenade pickup | adds 3 grenades up to 9; sets ownership bit `0x08` |
| 54 | Health pickup | heals 12 when health is low; otherwise clamps to maximum 23 |
| 61 | Extra-life pickup | increments lives by 1 while current lives are `<=9` (effective post-pickup maximum 10) |
| 62 | Mine pickup | adds 3 mines up to 9; sets ownership bit `0x10` |
| 68 | Shotgun-ammo pickup | adds 25 or 30 shells depending on `FC4A` difficulty; cap 99 |
| 69 | Shotgun weapon pickup | grants shotgun ownership bit `0x02`; adds 5 shells up to 99 |
| 70 | Uzi weapon pickup | grants Uzi ownership bit `0x04`; adds 15 rounds up to 999 |
| 71 | Uzi-ammo pickup | adds 50 or 70 rounds depending on `FC4A` difficulty; cap 999 |

Reproducible probes:

- `tools/rom_probe/object_pickup_probe.py` — control-flow-aware identity/effect validation.
- `tools/rom_probe/pickup_type_probe.py` — independent inventory/ownership signature validation.
- `extracted_metadata/object_pickups.json` — non-asset structural output.

### Health field — CONFIRMED

The health pickup resolves the world/avatar pointer stored at `F9F8`, computes `avatar+0x6C`, reads and writes that word, and uses maximum `0x17` (23). The damage path independently subtracts an attacker's `object+0x6E` from the target's `object+0x6C`.

Therefore:

```text
object+0x6C = HP / health
object+0x6E = damage / impact value
```

The long-known fixed RAM cheat address `FFC69E` is consistent with the retail runtime layout, but authoring/reconstruction should use the architectural field identity rather than hard-code that absolute address.

### Weapon-acquisition native — CONFIRMED

VM native wrapper `0x00AEF8` calls engine helper `0x005CF4`. The helper indexes a selector-to-bit table:

```text
selector 0  -> 0x01 pistol
selector 2  -> 0x02 shotgun
selector 4  -> 0x04 Uzi
selector 6  -> 0x08 grenade
selector 8  -> 0x10 mine
selector 10 -> 0x20 flamethrower
```

and ORs the selected bit into `FB8E`. This is the decisive distinction between a weapon pickup and an ammo-only refill.

## Mission / key / objective objects — CONFIRMED

Reachable VM control-flow analysis ties the following classes directly to mission flag word `FC54`, the game's message table and native message/display path around `0xAF08`.

### Collectible / activatable objective objects

| type_id | Functional identity | `FC54` bit/progression | Retail placement evidence |
|---:|---|---|---|
| 63 | Security passcard | `0x8000` | scene 0 |
| 58 | Gate key | `0x8000` | scene 4 |
| 60 | Subway lever | `0x4000` | scenes 5–6 |
| 55 | Palace key | `0x0400` | scene 11 |
| 56 | Catacombs key | `0x0800` | scene 9 |
| 57 | Brass key | `0x1000` | class exists; no recovered retail placement |
| 64 | Alpha security pass | `0x1000` | scene 13 |
| 65 | Beta security pass | `0x2000` | scene 13 |
| 66 | Gamma security pass | `0x4000` | scene 13 |
| 67 | Delta security pass | `0x8000` | scene 13 |
| 9 | Bomb-disarming key | sequential `0x2000 → 0x4000 → 0x8000` progression | three placements across scenes 9, 10, 11 |

The names above come from the game's own reachable message path and corresponding mission-flag behavior; they are not inferred solely from placement geography.

### Doors / controllers gated by objective flags

| type_id | Functional identity | Required `FC54` bit |
|---:|---|---:|
| 13 | Security-passcard door | `0x8000` |
| 16 | Palace gate | `0x0400` |
| 17 | Catacombs gate | `0x0800` |
| 18 | Locked gate using palace-key profile | `0x0400` |
| 77 | Alpha-pass door | `0x1000` |
| 78 | Beta-pass door | `0x2000` |
| 79 | Gamma-pass door | `0x4000` |
| 80 | Delta-pass door | `0x8000` |
| 87 | Subway signal box | `0x4000` lever state |

Reproducible probe: `tools/rom_probe/object_objective_probe.py`.

The probe traverses reachable VM instructions, validates `FC54` reads/writes, checks the exact flag constants and verifies message IDs through the game's own message table. It deliberately avoids treating arbitrary bytes inside a script as semantic evidence.

## Placement type versus archetype — CONFIRMED separation

A placement `type_id` is not itself the complete visual/combat identity. Scripted classes can call VM native `0x2436`, which invokes archetype setter `0xF9D4` and selects:

```text
object+0x2A = archetype ID
object+0x2C = animation descriptor
```

The archetype ID also indexes Normal/Hard HP and damage tables. Multiple placement types may therefore share one archetype, and multiple archetype IDs may share one animation descriptor while retaining different stats.

See `ARCHETYPE_SYSTEM.md` and `ANIMATION_FORMAT.md`.

## Sprite/presentation layer — CONFIRMED structure, semantic labels still gated

The mapping renderer is now recovered through 16×16 sprite chunks; see `SPRITE_RENDERER.md`. This enables visual cross-correlation, but presentation alone is not sufficient to assign a gameplay name.

Current policy for freezing actor/prop identities requires at least two independent evidence paths, e.g.:

```text
VM behavior / native calls / callbacks
+
archetype stats / visual frames / scene distribution
```

The current synthetic-palette renders suggest archetypes `166` and `176–178` are effect/prop-like rather than ordinary human actors, while archetype `8` is a large structured object. These remain descriptive observations, not final gameplay labels.

## Direct-code exceptions

Among retail-range IDs `0..138`, direct-code representation is selected only by types `1`, `10` and `101`.

- type `1` is present in the engine tables but absent from recovered retail placements;
- types `10` and `101` each occur seven times, only in scene 14;
- their routines are related/symmetric, but their gameplay names remain intentionally unresolved.

## Next classification targets

1. Use the recovered sprite renderer to export selectors actually reached by each placed archetype.
2. Recover palette/priority provenance so frames can be rendered using scene CRAM rather than a synthetic palette.
3. Cross-correlate the dominant callback families (`0x2568/0x28C8`, `0x2828/0x28C8`, etc.) with archetype assignment and VM-native use.
4. Identify enemy/civilian/prop families only after behavioral and presentation evidence agree.
5. Turn the confirmed catalog into a machine-readable authoring schema for level tools.
