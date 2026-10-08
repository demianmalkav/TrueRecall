# Combat Families and Runtime Projectile Architecture

This document records mechanically proven combat families. Names such as `shooter`, `spread-shot`, `contact hazard` and `boss-class ranged actor` are based on code/data paths, not sprite appearance alone.

## Common actor-contact callbacks

### `0x002568` — physical overlap / separation — HIGH CONFIDENCE

This callback does not subtract HP. It resolves overlap geometry and pushes/separates entities through helpers around `0x0105CA/0x010616`, while propagating state to linked objects.

It is the dominant solid-body interaction family.

### `0x002698` — physical overlap except avatar — HIGH CONFIDENCE

If the other entity is the world/avatar object at `F9F8`, the callback returns immediately; otherwise it delegates to `0x002568`.

This is best treated as a physical-collision variant that deliberately ignores the player.

### `0x002828` — direct contact damage — CONFIRMED

This entry reaches the common damage path:

```text
target HP      = target+0x6C
attacker damage = attacker+0x6E
HP'            = HP - damage
```

It also propagates hit/death state through linked objects. Classes using this callback with nonzero archetype damage are mechanically contact-damage hazards/actors.

### `0x0028B0` — avatar-contact notification — HIGH CONFIDENCE

This callback reacts only when the overlapping entity is the world/avatar object and sets state on the caller's linked object. No HP subtraction occurs in the callback itself.

It is a trigger/contact-notification family rather than direct damage.

## Standard ranged-fire family — CONFIRMED

Shared attack routine/native `0x00DB48`:

1. evaluates/aims relative to the avatar;
2. allocates runtime class `170 (0xAA)`;
3. initializes that entity as a projectile.

Runtime projectile class 170:

- direct code: `0x00E10E`
- actor collision callback: `0x0027EE`
- world collision path reaches `0x002C10`
- damage Normal/Hard: `1 / 1`

Any retail placement script reaching `0x00DB48` is therefore a mechanically proven ranged shooter.

Confirmed retail shooter classes:

```text
5, 7, 24, 25, 28, 38, 39, 82, 98, 107, 112, 126, 127
```

They account for **581 retail placements**.

Reproducible evidence:

- `tools/rom_probe/ranged_attack_probe.py`
- `extracted_metadata/ranged_attack.json`

## Spread-shot family — CONFIRMED

Routine `0x00DAA4` accepts a projectile count, repeatedly creates runtime class `175 (0xAF)` and assigns angular offsets from a table.

Runtime class 175:

- direct code: `0x00E3E0`
- actor collision: `0x0027EE`
- world collision: `0x002C10`
- damage Normal/Hard: `1 / 1`

Retail placement types using this family:

```text
20  — 6 placements, scene 9
86  — 13 placements, scene 17
```

Reproducible evidence:

- `tools/rom_probe/spread_attack_probe.py`
- `extracted_metadata/spread_attack.json`

## Scene-17 boss-class ranged actor — CONFIRMED mechanical class

`type_id 104` is a unique scene-17 combat class with:

- one retail placement;
- HP `100 / 100` on Normal/Hard;
- repeated use of VM spawn native `0x00211C`;
- all recovered child spawns resolve to runtime class `225`.

Runtime class 225:

- scripted at `0x12FF54`;
- installs actor-collision callback `0x0027EE`;
- uses VM native `0x0021DA`, which wraps velocity helper `0x0127F0`;
- damage `1 / 1`.

This is sufficient to classify type 104 as a **boss-class ranged actor**. Its proper story/character name remains intentionally unresolved.

Reproducible evidence:

- `tools/rom_probe/boss_projectile_probe.py`
- `extracted_metadata/boss_projectile.json`

Do not conflate type 104 with type 3 merely because both are unique in scene 17. Type 3 is independently tied to a Crimson Jihad threat message, whereas type 104 is the mechanically proven 100-HP projectile-spawning combat class.

## Contact-hazard families — CONFIRMED mechanic; some visual sublabels HIGH CONFIDENCE

The following retail types have initial archetype damage and use the `0x002828` damage interface:

```text
29, 31
35, 36
72, 73, 74, 75
93, 94, 95
```

### Types 72–75 — spike traps — HIGH CONFIDENCE semantic label

Reconstructed initial frames show:

- `72/73`: horizontal rows of spikes;
- `74/75`: vertical rows of spikes.

Their mechanics independently show contact damage `2 / 3` (Normal/Hard) through callback `0x002828`.

The exact art label `spike trap` comes from reconstructed graphics; the broader `contact hazard` classification is mechanically confirmed.

### Types 29/31 — explosive barrel/destructible explosive prop — HIGH CONFIDENCE

Independent evidence:

1. initial presentation reconstructs as two barrel/drum variants;
2. HP is `1 / 1`;
3. damage is `4 / 7`;
4. script later installs contact-damage callback `0x002828`;
5. script transitions through VM archetype setter `0x2436` to archetype `176`, whose recovered presentation is explosion/debris-like.

This is strong evidence for an explosive destructible-barrel family. The two IDs remain distinct variants.

### Types 35/36 and 93/94/95

These are mechanically confirmed contact hazards (`0x2828`, damage `2/3`) but their precise gameplay/art names remain unresolved. Do not freeze a visual name solely from their small reconstructed sprites.

## Runtime projectiles versus placement classes

Projectile/effect classes are not restricted to the retail placement range. The engine creates runtime type IDs above the highest scene-placement ID through:

- generic/linked allocation natives;
- offset-linked allocation natives;
- direct 68000 routines such as the shared ranged/spread paths.

This is a key authoring distinction:

```text
placement class   -> persistent/spatial level object
runtime class     -> projectile/effect/child entity created by behavior code
```

A future Total Recall entity schema must model these separately.

## Production implications

The recovered architecture already supplies reusable combat primitives:

- solid overlap/separation;
- player-ignoring collision variants;
- contact damage;
- contact triggers;
- standard aimed projectile fire;
- angular spread fire;
- scripted boss projectile generation;
- runtime child/projectile entities.

A new Total Recall enemy does not necessarily require new low-level collision or projectile code. It can potentially be authored by combining an object VM script, existing/native attack primitive, archetype/presentation and stat profile.

## Next targets

1. Recover additional projectile/runtime attack families and map their parent actors.
2. Distinguish melee-only hostiles from non-hostile mobile actors.
3. Resolve direct-code scene-14 classes `10` and `101`.
4. Build a machine-readable semantic catalog separating placements, controllers, props, actors and runtime children.
