# Object Type Catalog

This document maps retail placement `type_id` values to functional identities only when the ROM itself provides enough evidence. Visual names are not frozen from appearance alone.

## Standard pickup family — CONFIRMED

The standard inventory/survival pickups install actor-contact callback `0x009DF8`. Their identities and effects are recoverable from reachable object-VM code, inventory RAM, the weapon-ownership helper and player-health field.

| type_id | Working label | Confirmed effect |
|---:|---|---|
| 51 | Flamethrower weapon pickup | grants ownership bit `0x20`; adds 30 fuel up to 99 |
| 52 | Flamethrower fuel pickup | adds 50 fuel up to 99 |
| 53 | Grenade pickup | adds 3 grenades up to 9; sets ownership bit `0x08` |
| 54 | Health pickup | heals 12 when low; otherwise clamps to maximum 23 |
| 61 | Extra-life pickup | increments lives by 1 while current lives are `<=9` |
| 62 | Mine pickup | adds 3 mines up to 9; sets ownership bit `0x10` |
| 68 | Shotgun-ammo pickup | adds 25 or 30 shells by difficulty; cap 99 |
| 69 | Shotgun weapon pickup | grants ownership bit `0x02`; adds 5 shells |
| 70 | Uzi weapon pickup | grants ownership bit `0x04`; adds 15 rounds |
| 71 | Uzi-ammo pickup | adds 50 or 70 rounds by difficulty; cap 999 |

Reproducible probes: `object_pickup_probe.py`, `pickup_type_probe.py`.

### Health and weapon helpers — CONFIRMED

`object+0x6C` is HP/health and `object+0x6E` is damage/impact. VM native `0x00AEF8` calls helper `0x005CF4`, which maps weapon selectors `0,2,4,6,8,10` to ownership bits `1,2,4,8,0x10,0x20` and ORs the result into `FB8E`.

## Mission / key / objective objects — CONFIRMED

Reachable VM control-flow ties these classes directly to mission word `FC54`, the game's message table and native display path around `0xAF08`.

### Collectible / activatable objectives

| type_id | Functional identity | `FC54` bit/progression |
|---:|---|---:|
| 63 | Security passcard | `0x8000` |
| 58 | Gate key | `0x8000` |
| 60 | Subway lever | `0x4000` |
| 55 | Palace key | `0x0400` |
| 56 | Catacombs key | `0x0800` |
| 57 | Brass key | `0x1000` — class exists, no recovered retail placement |
| 64 | Alpha security pass | `0x1000` |
| 65 | Beta security pass | `0x2000` |
| 66 | Gamma security pass | `0x4000` |
| 67 | Delta security pass | `0x8000` |
| 9 | Bomb-disarming key | sequential `0x2000 → 0x4000 → 0x8000` |

### Doors / controllers gated by objective flags

| type_id | Functional identity | Required bit |
|---:|---|---:|
| 13 | Security-passcard door | `0x8000` |
| 16 | Palace gate | `0x0400` |
| 17 | Catacombs gate | `0x0800` |
| 18 | Locked gate using palace-key profile | `0x0400` |
| 77 | Alpha-pass door | `0x1000` |
| 78 | Beta-pass door | `0x2000` |
| 79 | Gamma-pass door | `0x4000` |
| 80 | Delta-pass door | `0x8000` |
| 87 | Subway signal box | `0x4000` |

Reproducible probe: `tools/rom_probe/object_objective_probe.py`.

## Civilian actor family — CONFIRMED

Thirteen placement classes are functionally civilians because their reachable scripts invoke the game's own civilian-hit penalty messages:

- `0x1A`: Harry is warned to watch out for taxpayers/civilians.
- `0x1C`: the game explicitly reports that another civilian was hit.

The confirmed civilian `type_id` set is:

```text
11, 40, 49, 50, 84, 102, 105, 108, 109, 110, 119, 120, 128
```

This classification comes from reachable script/message behavior, not from sprite appearance. Their visuals may represent different civilian subtypes and should remain separately addressable.

## Truck class — CONFIRMED

`type_id 46` is a truck class.

Independent evidence:

1. Its recovered initial presentation is unambiguously a top-down truck/vehicle.
2. Its reachable script triggers the game's own message referring to the last of the trucks.
3. All four retail placements occur in scene 14, the scene whose placement composition is otherwise strongly vehicle/setpiece-specific.

This satisfies the project's two-evidence rule for semantic naming.

## Mission/controller objects — CONFIRMED or HIGH CONFIDENCE

Not every placement is meant to render as a normal actor. The message/control-flow scan identifies classes whose primary role is level logic.

### Confirmed controller logic by direct mission text/context

| type_id | Working role | Evidence |
|---:|---|---|
| 81 | mission transition/controller | one placement; triggers warhead/mission-transition messaging rather than an actor presentation |
| 100 | mission completion controller | one placement in scene 3; triggers the public-restroom/Aziz-escaped/Park transition message |
| 133 | crate-count objective controller | one placement in scene 7; messages track many crates despite a single controller placement |
| 134 | crate-count objective controller | one placement in scene 8; same count/controller pattern |

These four classes also belong to the tiny set with no recovered initial presentation native, which independently supports their role as logical controllers rather than visible actors.

### Strong controller/interactable candidates — HIGH CONFIDENCE

- `88`: extraction/van controller — reachable message tells Harry to get in the van.
- `97`: train-blockade/stronghold logic — mission guidance tied to the train/Crimson Jihad route.
- `125`: computer-destruction objective/controller — messages instruct and confirm destruction of computers/HQ.
- `129`: bomb-objective controller — key requirements and completion messaging.
- `131`: modem/computer objective/interactable — message instructs attaching modem to computer.
- `132`: objective completion trigger — reachable completion message.

Exact authoring categories such as `trigger`, `controller`, `interactable` versus visible prop remain to be refined where presentation exists.

## Special hostile / named-actor evidence — HIGH CONFIDENCE

`type_id 3` is a unique hostile actor in scene 17 whose script triggers the Crimson Jihad threat message. Its recovered presentation is a human hostile. This is strongly consistent with the scene's Aziz/final-hostile role, but the exact proper-name label remains HIGH CONFIDENCE until the boss/mission-state linkage is independently closed.

## Placement type versus archetype — CONFIRMED

For generic scene placements the allocator sets:

```text
initial object+0x2A archetype = placement type_id
object+0x2C = archetype descriptor table entry
```

Scripts may later switch archetype via VM native `0x2436`. Therefore a later explosion/death archetype must not be confused with the object's initial identity. See `ARCHETYPE_SYSTEM.md`.

## Initial presentation coverage — CONFIRMED

The recovered presentation API includes direct and facing/direction-aware animation natives. CFG analysis resolves the initial presentation family for:

```text
2,427 / 2,449 placements = 99.1%
```

Across 128 placed `type_id` values:

```text
106 unique presentation families
14 branch-dependent initial variants
6 no initial presentation native
2 direct-code types
```

The six scripted types without a presentation native are `4,34,81,100,133,134`; four of these are already independently identified as mission/controller logic. Direct-code types are `10` and `101`.

Reproducible probe: `tools/rom_probe/initial_presentation_cfg_probe.py`.

## Direct-code exceptions

Within retail range `0..138`, direct-code representation is selected only by types `1`, `10`, `101`.

- type `1` is absent from recovered retail placements;
- types `10` and `101` each occur seven times, only in scene 14;
- their routines are related/symmetric but their exact gameplay identity remains unresolved.

## Classification policy and next targets

A gameplay name should be frozen only after at least two independent paths agree, for example:

```text
VM behavior / messages / native calls / callbacks
+
initial presentation / stats / scene distribution
```

Next targets:

1. Recover projectile/fire spawning paths and classify hostile actor families mechanically.
2. Split the civilian family into visual/behavioral subtypes without losing its shared civilian semantics.
3. Resolve types `4`, `34`, `10`, `101` and remaining scene-specific special classes.
4. Convert confirmed actors, props, pickups, doors and controllers into a machine-readable authoring schema for level tools.
