# Player System

This document records the cumulative player-control architecture. Live continuation priority comes from `docs/PROJECT_STATE.md`.

## Layered control model — CONFIRMED

The player is not controlled by one monolithic state enum. Five cooperating layers are established:

1. normalized input (`F6EA/F6EC/F6EE/F6F0`);
2. 16-bit action/state word `FB7C`;
3. 16-bit overlay/context word `FB7E`;
4. per-frame event bits returned in `D7`;
5. a synchronized linked pair: F9F8 world/render avatar + FB6E control/collision proxy.

This explains combinations such as walking while Lock is held, firing from a roll, temporary invulnerability and alternate-player overlays without inventing a combined enum state for every combination.

## Normalized input — CONFIRMED / HIGH CONFIDENCE

The input update around `0x012B62` maintains:

```text
FFFFF6EA  previous normalized input
FFFFF6EC  current normalized input
FFFFF6EE  newly pressed edges
FFFFF6F0  continuously held overlap
```

Derived relations:

```text
F6EE = current & (current XOR previous)
F6F0 = current & previous
```

Known controls:

- `F6EC & 0x000F`: D-pad mask;
- `F6EC bit 6`: Lock held — HIGH CONFIDENCE;
- `F6EE bit 4`: Fire press — CONFIRMED;
- `F6EE bit 5`: Roll press — CONFIRMED;
- `F6EE bit 12`: next owned weapon — CONFIRMED;
- `F6EE bit 14`: previous owned weapon — CONFIRMED;
- main action-edge filter: `0x5030`.

## Direction / facing — CONFIRMED

Direction table at `0x0147C4` maps D-pad mask to `object+0x50` facing:

| D-pad | Facing | Direction |
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

## Linked player entities — CONFIRMED architecture

The controllable character is represented by two synchronized engine objects.

### Runtime globals are signed word pointers — CONFIRMED

M0.9C canonical tracing corrected an earlier tooling assumption. Retail loads both globals using `MOVEA.W`; they are signed 16-bit RAM pointers, not adjacent halves of 32-bit pointers.

Observed canonical gameplay values:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

The exact RAM object addresses are allocation-dependent; do not hard-code `C632/C7FA` as universal object locations.

### F9F8 world/render avatar — CONFIRMED role in tested path

Evidence accumulated from construction/synchronization plus canonical runtime tracing:

- stored from stage/world object path at `0x0109D0`;
- loaded throughout synchronization as the linked world/render-side object;
- receives synchronized motion/facing from proxy;
- visibility/blink and geometry synchronization operate on it;
- canonical held-Y sprint runtime: `object+0x2A = 139`, `object+0x2C = 0x000A0000`;
- descriptor remains stable through the observed native animation cycle.

### FB6E control/collision proxy — CONFIRMED role in tested path

- allocated during player-control construction and stored at `0x008284`;
- helper `0x00F8E8` promotes newly allocated `A0` into `A5`;
- receives player callbacks/control/motion state;
- entity-interaction callback `0x00356C` explicitly ignores F9F8, suppressing collision with its linked avatar.

Original Beam source terminology remains unknown; `world/render avatar` and `control/collision proxy` are project names for the recovered roles.

## Synchronization — CONFIRMED / HIGH CONFIDENCE

At `0x009B60`, the frame synchronizer loads the linked pair.

- `0x009BE8`: `+0x18/+0x1A/+0x56` motion fields copy proxy→avatar;
- `0x009C7A`: `+0x10/+0x12/+0x14/+0x16` and `+0x54` geometry/position can copy avatar→proxy;
- aim/facing synchronization can be suppressed by Lock/fire context;
- animation-phase synchronization is conditional on player action state.

M0.9C recovered a specific phase-transfer bridge at `0x009D5E`:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Observed writer cluster:

```text
0x009D72 -> avatar+0x1E
0x009D7E -> avatar+0x24
0x009D88 -> avatar+0x20
```

This cluster is one native phase-advance transaction. The `+0x24` write inside it is not automatically a new external selector event.

## Canonical native sprint phase — CONFIRMED

During the M0.9C held-Y runtime trace:

```text
F9F8 descriptor       0x000A0000
F9F8 base +0x1C       0x08B6
raw phase deltas      0, 2, 4, 6, 8, 10
```

Current `+0x1E` cycles:

```text
0x08B6 -> 0x08B8 -> 0x08BA -> 0x08BC -> 0x08BE -> 0x08C0 -> wrap
```

No F9F8 `+0x2C` write occurred in the observed cycle.

### M0.8 identity refinement

M0.8 proved that scoping renderer/cache substitution to `0x0F0000` produces a compact player-local visual difference with exact inactive fallback. M0.9C later falsified the stronger interpretation that `0x0F0000` is the canonical F9F8 world/render-avatar descriptor. In the tested canonical sprint path F9F8 is `0x000A0000`.

## `FB7C` action/state word — CONFIRMED structure

`FFFFFB7C` is a composable 16-bit bitfield. `FB7D` is its low byte, not a separate variable.

| Value | Working interpretation | Status |
|---:|---|---|
| `0x0000` | idle / neutral | CONFIRMED |
| `0x0002` | walking / locomotion | CONFIRMED |
| `0x0004` | normal weapon-fire class | CONFIRMED |
| `0x0008` | special-action base bit | HIGH CONFIDENCE |
| `0x000C` | special-action + normal-fire bits | STRUCTURAL; phase label unresolved |
| `0x0028` | special-action + `0x20`; Uzi/flamethrower phases | HIGH CONFIDENCE |
| `0x0048` | special-action + `0x40`; grenade phase | HIGH CONFIDENCE |
| `0x0001` | auxiliary/transition bit | UNRESOLVED |

Idle is written at `0x00832A`, walking at `0x0083A0`; ordinary pistol/shotgun/Uzi paths set `0x0004`.

## `FB7E` overlay/context word — CONFIRMED structure

`FFFFFB7E` is a second 16-bit flag word. `FB7F` is its low byte.

| Bit | Working interpretation | Status |
|---:|---|---|
| `0x0001` | roll active phase | HIGH CONFIDENCE |
| `0x0002` | post-roll transition | HIGH CONFIDENCE |
| `0x0004` | roll-fire / kneeling-fire context | CONFIRMED |
| `0x0008` | normal-control/update context | UNRESOLVED exact label |
| `0x0040` | JLLBFR alternate-player/maniac overlay | HIGH CONFIDENCE |
| `0x0080` | lock/fire pose latch | HIGH CONFIDENCE |

Higher bits `0x0100–0x4000` occur in terminal/special sequences and remain intentionally unnamed.

## Roll / roll-fire — CONFIRMED / HIGH CONFIDENCE

Roll begins at `0x008600`:

1. optionally update facing;
2. clear normal `FB7C` action word;
3. set `FB7E bit 0`;
4. select animation `0x0142`;
5. execute movement/collision;
6. later set `FB7E bit 1`;
7. test current Fire held (`F6EC bit 4`).

Fire held branches to secondary weapon dispatcher `0x0084BA`. Secondary pistol/shotgun/Uzi/grenade/flamethrower paths set `FB7E bit 2`; Mine returns to normal control. `0x0098BA` manages associated kneeling/roll-fire transition using animation `0x0172`.

Roll-fire is therefore an overlay/context layered over weapon firing.

## Lock / strafe — HIGH CONFIDENCE

Around `0x009BC0–0x009BE8`, when Lock (`F6EC bit 6`) is not held, aim/display-facing is resynchronized to locomotion facing. Holding Lock suppresses that synchronization, preserving aim while movement changes.

`FB7E bit 7` acts as a pose latch around `0x0099D2` during Lock/normal-fire context.

## JLLBFR alternate-player overlay — HIGH CONFIDENCE

Retail JLLBFR behavior remains useful architectural precedent:

- password path enables a cheat flag (`FBEE bit 1`);
- hidden input can toggle `FB7E bit 6 / 0x0040`;
- idle/walk logic uses presentation family `0x00F2`;
- movement parameters rise approximately `0x0180/0x0120 -> 0x0280/0x0220`.

Important M0.9C correction: the JLLBFR family selector does **not** imply that F9F8's canonical descriptor is `0x0F0000`. That older identity hypothesis is falsified.

## Nonfatal hit / invulnerability overlay — HIGH CONFIDENCE

`0x009714`:

- checks `object+0x06 bit 0x0020`;
- sets `FB90 = 24`;
- sets `FB92 = 1`;
- sets `object+0x06 bit 0x0020`.

Constructor uses a longer initial window (`FB90 = 100`). `0x009CA0` manages countdown/blink and eventual teardown. Normal loops route `D7 bit 13` into this response after terminal-mask handling, supporting the overlay model.

## Terminal events / death routing — CONFIRMED routing, semantics partial

Many active loops use:

```text
MOVE.L D7,D6
ANDI.L #$00000063,D6
BNE.W  $009244
```

At least 27 player-action sites converge on `0x009244`, a terminal-event dispatcher for `D7` bits `0,1,5,6`.

- external `FC47 bit 5` or `D7 bit 1` -> `0x0096B6`, no lives decrement observed — HIGH CONFIDENCE non-life-loss transition;
- `D7 bit 5` -> `0x00944E`, life decremented unless cheat applies;
- `D7 bit 0` -> `0x00960C`, life-loss path;
- remaining masked case, normally `D7 bit 6`, -> default life-loss path.

Therefore `D7 & 0x63` is not simply a “fatal mask.” Several life-loss variants use animation `0x0262`; exact cause labels remain unresolved.

## Animation family anchors — CONFIRMED

Per-weapon locomotion tables:

```text
walk  0x0147E4: 02 12 22 32 32 42
idle  0x0147F0: 52 62 72 82 82 92
```

Additional anchors:

- roll `0x0142`;
- roll-fire/kneeling `0x0172`;
- JLLBFR/maniac `0x00F2`;
- common life-loss family `0x0262`.

## Current architecture graph

```text
normalized input
   +--> FB7C action classes
   +--> FB7E overlays/contexts
   +--> weapon / roll / lock / hit routing

FB6E control/collision proxy
   ---- motion + phase ----> F9F8 world/render avatar

F9F8 world/render avatar
   ---- geometry/position -> FB6E proxy when allowed

after active update:
   D7 event bits -> terminal/nonfatal routing
```

## Remaining semantic gaps

Still intentionally unresolved:

- exact labels for all special weapon phases (`0x0008/0x000C/0x0028/0x0048`);
- cause-level meanings of higher `FB7E` bits;
- exact cause labels for terminal/death `D7` bits;
- original Beam terminology for linked objects;
- exact physical interpretation of `object+0x54` beyond spatial/collision-response/positional-correction role.

## Reproducible evidence

Static probes:

```text
python tools/rom_probe/player_state_probe.py "True Lies (World).md" --json state.json
python tools/rom_probe/player_links_probe.py "True Lies (World).md" --json links.json
```

Canonical M0.9C runtime tooling/evidence:

```text
tools/runtime/m09c_animation_state_trace_v2.py
tools/rom_probe/m09c_phase_bridge_analysis.py
extracted_metadata/m09c_canonical_phase_bridge.json
```

## Production extension rule

M0.7 already proved an isolated player extension. M0.9C has now recovered the native presentation-phase seam. New Total Recall movement/presentation mechanics must preserve the linked F9F8/FB6E contract, avoid wholesale descriptor replacement, and pass deterministic parent/child regressions before integration.
