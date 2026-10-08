# Player System

## Model recovered in M0.6

The player is **not** controlled by one monolithic state enum. Static reconstruction shows five cooperating layers:

1. normalized input (`F6EA/F6EC/F6EE/F6F0`)
2. a 16-bit action/state word (`FB7C`, low byte `FB7D`)
3. a 16-bit overlay/context flag word (`FB7E`, low byte `FB7F`)
4. per-frame event bits returned in `D7`
5. a synchronized pair of engine entities (`F9F8` avatar + `FB6E` control/collision proxy)

This layered model explains combinations such as walking while Lock is held, firing from a roll, temporary invulnerability, and alternate-player overlays without requiring a separate combined state for every possibility.

## Normalized controller input — CONFIRMED / HIGH CONFIDENCE

The input update around `0x012B62` maintains:

- `FFFFF6EA`: previous normalized input word
- `FFFFF6EC`: current normalized input word
- `FFFFF6EE`: newly pressed edges
- `FFFFF6F0`: inputs continuously held across the previous and current sample

The formulas are directly visible in the input routine:

```text
F6EE = current & (current XOR previous)
F6F0 = current & previous
```

Known normalized controls:

- `F6EC & 0x000F`: directional pad mask
- `F6EC bit 6`: Lock held — HIGH CONFIDENCE, corroborated by control behavior
- `F6EE bit 4`: Fire press — CONFIRMED by primary weapon dispatch
- `F6EE bit 5`: Roll press — CONFIRMED by branch to `0x008600`
- `F6EE bit 12`: next owned weapon (`FB8C += 2`, wrapping `0x000C→0`) — CONFIRMED
- `F6EE bit 14`: previous owned weapon (`FB8C -= 2`, wrapping below zero→`0x000C`) — CONFIRMED
- main action-edge filter: `0x5030`

## Direction and facing — CONFIRMED

The direction lookup table at `0x0147C4` maps normalized D-pad combinations to `object+0x50` facing:

| D-pad mask | Facing | Direction |
|---:|---:|---|
| `0x1` | 0 | N |
| `0x9` | 1 | NE |
| `0x8` | 2 | E |
| `0xA` | 3 | SE |
| `0x2` | 4 | S |
| `0x6` | 5 | SW |
| `0x4` | 6 | W |
| `0x5` | 7 | NW |

`0x009B12` is the direct D-pad→facing helper used by player control.

## Dual player entities — M0.6B

The controllable character is implemented as two linked engine objects rather than one object doing everything.

### `F9F8` — world/render avatar entity — HIGH CONFIDENCE

- stored from the stage/world object path at `0x0109D0`
- used as the linked visual/world-side entity throughout player synchronization
- receives synchronized motion and facing from the player proxy
- visibility/blink and geometry synchronization operate on it directly

### `FB6E` — control/collision proxy/companion — HIGH CONFIDENCE

- allocated during player-control construction and stored at `0x008284`
- allocator helper `0x00F8E8` promotes the newly allocated `A0` object into `A5`
- receives the player callback pair and the control/motion state
- its entity-interaction callback at `0x00356C` explicitly ignores `F9F8`, suppressing collision with its own linked avatar

### Synchronization

At `0x009B60`, the frame synchronizer loads `F9F8→A1` and `FB6E→A5`.

- `0x009BE8`: motion fields `+0x18/+0x1A/+0x56` are copied proxy→avatar
- `0x009C7A`: position/geometry fields `+0x10/+0x12/+0x14/+0x16` and `+0x54` can be copied avatar→proxy
- aim/facing synchronization can be suppressed by Lock/fire context
- animation-phase synchronization is conditional on action bits

This architecture is directly relevant to M0.7: a new movement or melee state must respect both representations rather than patching only one object.

## Action/state word `FB7C` — CONFIRMED structure

`FFFFFB7C` is a **16-bit bitfield/action word**. `FB7D` is merely its low byte and must not be documented as a separate variable.

Direct values observed in player code:

| Value | Working interpretation | Status |
|---:|---|---|
| `0x0000` | idle / neutral control | CONFIRMED |
| `0x0002` | walking / locomotion | CONFIRMED |
| `0x0004` | normal weapon-fire class | CONFIRMED |
| `0x0008` | special-weapon/action base bit | HIGH CONFIDENCE |
| `0x000C` | special-action + normal-fire bits | STRUCTURAL FACT; phase label unresolved |
| `0x0028` | special-action + `0x20` modifier; Uzi/flamethrower phases | HIGH CONFIDENCE |
| `0x0048` | special-action + `0x40` modifier; grenade phase | HIGH CONFIDENCE |
| `0x0001` | auxiliary/transition bit | UNRESOLVED |

Idle is written at `0x00832A`; walking at `0x0083A0`; ordinary pistol/shotgun/Uzi fire sets bit `0x0004` in their handlers.

The word should therefore be treated as **composable action-class bits**, not an enum.

## Overlay/context flags `FB7E` — CONFIRMED structure

`FFFFFB7E` is a second 16-bit flag word. `FB7F` is its low byte.

Current low-bit map:

| Bit | Working interpretation | Status |
|---:|---|---|
| `0x0001` | roll/dive active phase | HIGH CONFIDENCE |
| `0x0002` | post-roll transition phase | HIGH CONFIDENCE |
| `0x0004` | roll-fire / kneeling-fire context | CONFIRMED |
| `0x0008` | normal-control/update context | UNRESOLVED exact label |
| `0x0040` | JLLBFR alternate-player/maniac/chainsaw overlay | HIGH CONFIDENCE |
| `0x0080` | lock/fire pose latch | HIGH CONFIDENCE |

Higher bits `0x0100–0x4000` are used by terminal/special sequences and remain intentionally unnamed until their cause-level semantics are proven.

## Roll and roll-fire — CONFIRMED / HIGH CONFIDENCE

Roll starts at `0x008600`.

The routine:

1. optionally updates facing from the D-pad
2. clears the normal `FB7C` action word
3. sets `FB7E bit 0`
4. plays animation `0x0142`
5. runs movement/collision updates
6. later sets `FB7E bit 1` for the transition phase
7. tests **current Fire held** (`F6EC bit 4`)

If Fire is held, control branches to the secondary weapon dispatcher at `0x0084BA`. The secondary pistol/shotgun/Uzi/grenade/flamethrower paths set `FB7E bit 2` and enter their firing handlers. Mine deliberately routes back to normal control.

`0x0098BA` manages the associated kneeling/roll-fire transition and uses animation `0x0172`.

This statically proves that roll-fire is a context layered on top of weapon firing, not a separate weapon family.

## Lock / strafe — HIGH CONFIDENCE

Lock is also an overlay, not an exclusive player state.

The control synchronization region around `0x009BC0–0x009BE8` tests `F6EC bit 6`. When Lock is **not** held, the aim/display-facing representation is resynchronized to locomotion facing. When Lock **is** held, that synchronization is skipped, preserving the previous firing direction while movement can change.

`FB7E bit 7` is used as a pose latch around `0x0099D2` while Lock or normal-fire context is active.

This is the structural mechanism behind True Lies' independent movement/firing-direction behavior.

## JLLBFR alternate-player/maniac overlay — HIGH CONFIDENCE

The retail cheat path provides a valuable precedent for Total Recall extensions:

- decoded password `JLLBFR` enables a cheat flag (`FBEE bit 1`)
- a hidden normalized-input combination can toggle `FB7E bit 6 / 0x0040`
- idle/walk logic switches to animation `0x00F2`
- movement parameters increase from approximately `0x0180/0x0120` to `0x0280/0x0220`

This demonstrates that Beam already supports an alternate player presentation/behavior layered over the normal control architecture rather than requiring a completely separate engine path.

## Nonfatal hit / invulnerability overlay — HIGH CONFIDENCE

`0x009714` begins temporary invulnerability:

- tests whether `object+0x06 bit 0x0020` is already active
- sets `FB90 = 24`
- sets `FB92 = 1`
- sets `object+0x06 bit 0x0020`

The constructor establishes a longer initial protection window with `FB90 = 100`, `FB92 = 1` and the same object flag.

`0x009CA0` decrements `FB90`, uses `FB92` as the blink cadence, toggles visibility-related flags, and eventually clears the protection state.

In normal locomotion and weapon loops, `D7 bit 13` triggers `0x009714` after the terminal-event mask has been ruled out. Therefore a nonfatal hit/invulnerability response is an **overlay**, not a dedicated `FB7C` action state.

## Terminal events and death — CONFIRMED routing, cause semantics partial

Most active player loops use the pattern:

```text
MOVE.L D7,D6
ANDI.L #$00000063,D6
BNE.W  $009244
```

The static probe finds this convergence from at least 27 player-action sites.

`0x009244` is therefore a terminal-event dispatcher for `D7` bits `0,1,5,6`.

Routing inside the dispatcher:

- external `FC47 bit 5` or `D7 bit 1` → `0x0096B6`; **no lives decrement observed**, so this is a non-life-loss terminal/transition path — HIGH CONFIDENCE
- `D7 bit 5` → `0x00944E`; life is decremented unless the relevant cheat flag is active
- `D7 bit 0` → `0x00960C`; life-loss path
- remaining masked case (normally `D7 bit 6`) → default life-loss path

Therefore **not every `D7 & 0x63` event is a death**. The old shorthand “fatal mask” would be incorrect.

Several life-loss variants use animation `0x0262`; the exact semantic names of the different death causes remain unresolved.

## Animation tables — CONFIRMED

Per-weapon locomotion tables:

- walk table `0x0147E4`: `0x02, 0x12, 0x22, 0x32, 0x32, 0x42`
- idle table `0x0147F0`: `0x52, 0x62, 0x72, 0x82, 0x82, 0x92`

Additional player animations currently anchored:

- roll `0x0142`
- roll-fire/kneeling transition `0x0172`
- JLLBFR/maniac `0x00F2`
- life-loss paths commonly use `0x0262`

## Current static state graph

```text
normalized input
   |
   +--> idle (FB7C=0)
   |      \--> walk (FB7C=2) when D-pad active
   |
   +--> Fire edge --> primary weapon dispatcher --> fire/special weapon phases
   |
   +--> Roll edge --> roll overlay
   |                    \--> Fire held --> secondary weapon dispatcher + kneeling-fire overlay
   |
   +--> bit12 edge --> next owned weapon
   +--> bit14 edge --> previous owned weapon

continuous overlays:
   Lock held --------> preserve aim-facing while locomotion changes
   JLLBFR mode ------> alternate presentation/movement behavior
   nonfatal hit -----> temporary invulnerability/blink overlay

linked objects:
   FB6E proxy/control ----motion----> F9F8 world/avatar
   F9F8 world/avatar ----geometry--> FB6E proxy/control

after each active update:
   D7 & 0x63 --------> terminal-event dispatcher
```

## Important unresolved area

`object+0x54` is now classified as a spatial/collision-response or positional-correction field, not a control mode. Its exact physical axis/unit is still unresolved.

Also still unresolved:

- exact semantic names for all special weapon phases (`0x0008/0x000C/0x0028/0x0048`)
- cause-level meanings of higher `FB7E` bits
- exact cause labels for each terminal/death `D7` bit
- exact original Beam terminology and lifecycle ordering for the `F9F8`/`FB6E` pair
- dynamic timing confirmation for the static graph

## Reproducible probes

```text
python tools/rom_probe/player_state_probe.py "True Lies (World).md" --json state.json
python tools/rom_probe/player_links_probe.py "True Lies (World).md" --json links.json
```

Both probes verify the canonical SHA-1 before producing data and assert the core offsets/signatures used by this document.

## M0.6 status

**Static player-control architecture is substantially recovered through M0.6B.** M0.6 remains active until runtime/playtest validation of the remaining special phases and a minimal runtime regression suite exist.

## Extension target

The first controlled extension should add one isolated player state/animation while keeping `FB7C` action classes, `FB7E` overlays and the `F9F8`/`FB6E` synchronization contract compatible. This is the proof required before implementing Total Recall-specific movement or melee.
