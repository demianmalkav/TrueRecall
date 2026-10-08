# RAM Map

Known and working RAM locations for True Lies (World).

## Normalized controller buffer — M0.6

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF6EA` | previous normalized controller word | CONFIRMED |
| `FFFFF6EC` | current normalized controller word | CONFIRMED |
| `FFFFF6EE` | newly pressed input edges | CONFIRMED |
| `FFFFF6F0` | inputs held across consecutive samples (`current & previous`) | CONFIRMED |

The input routine around `0x012B62` copies `F6EC→F6EA`, decodes the new controller state into `F6EC`, then derives:

```text
F6EE = current & (current XOR previous)   ; newly pressed
F6F0 = current & previous                 ; continuously held
```

Known normalized bits:

- low nibble `F6EC & 0x000F`: D-pad direction mask
- `F6EC bit 6`: Lock held — HIGH CONFIDENCE
- `F6EE bit 4`: Fire edge — CONFIRMED
- `F6EE bit 5`: Roll edge — CONFIRMED
- `F6EE bit 12`: cycle to next owned weapon (`FB8C += 2`, wrap `0x000C→0`) — CONFIRMED
- `F6EE bit 14`: cycle to previous owned weapon (`FB8C -= 2`, wrap below zero→`0x000C`) — CONFIRMED

## Entity allocator globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF9F2` | active generic-entity count | CONFIRMED |
| `FFFFF9F4` | fixed active-list sentinel | CONFIRMED |
| `FFFFF9F8` | linked world/render avatar entity pointer | HIGH CONFIDENCE |
| `FFFFF9FC` | free-list-head **pointer variable** | CONFIRMED |
| `FFFFF9FE` | generic pool-base **pointer variable**; stores heap allocation result | CONFIRMED |

`F9FE` is not the physical beginning of the entity pool. Pool initialization requests `0x0F96` bytes from heap allocator `0x12A2A` and stores the returned low-RAM pointer in `F9FE` and initially in `F9FC`.

## Player / inventory globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFFB6E` | player control/collision proxy/companion entity | HIGH CONFIDENCE |
| `FFFFFB70` | pistol ammo | CONFIRMED |
| `FFFFFB72` | shotgun ammo | CONFIRMED |
| `FFFFFB74` | Uzi ammo | CONFIRMED |
| `FFFFFB76` | grenades | CONFIRMED |
| `FFFFFB78` | mines | CONFIRMED |
| `FFFFFB7A` | flamethrower ammo | CONFIRMED |
| `FFFFFB7C` | 16-bit player action/state bitfield | CONFIRMED structure |
| `FFFFFB7D` | low byte of `FB7C`; **not a separate variable** | CONFIRMED |
| `FFFFFB7E` | 16-bit player overlay/context flags | CONFIRMED structure |
| `FFFFFB7F` | low byte of `FB7E`; **not a separate variable** | CONFIRMED |
| `FFFFFB8A` | lives | HIGH CONFIDENCE |
| `FFFFFB8C` | weapon selector as even offset `0,2,4,6,8,10` | CONFIRMED |
| `FFFFFB8E` | weapon ownership bitmask | CONFIRMED |
| `FFFFFB90` | temporary invulnerability/blink duration counter | HIGH CONFIDENCE |
| `FFFFFB92` | invulnerability/blink cadence counter | HIGH CONFIDENCE |
| `FFFFFC4A` | difficulty: `0=Normal`, `1=Hard` | CONFIRMED |
| `FFFFFC4E` | mission-scoped script counter/state; concrete meaning is assigned by the active mission/object scripts | CONFIRMED reusable semantics |

### Difficulty — `FC4A`

Options code around `0x0053F0–0x005530` reads and toggles `FC4A` between zero and one while selecting the `Normal` / `Hard` option text.

Entity stat initializer `0x001EEC` multiplies `FC4A` by four and uses it to choose between Normal and Hard HP/damage table pointers before indexing them with `object+0x2A`.

Therefore `FC4A` is the gameplay difficulty selector, not a mission-state word.

### Player health

The architectural player-health location is the word at:

```text
*(F9F8) + 0x6C
```

This is CONFIRMED by the scripted health pickup, which resolves the avatar pointer from `F9F8`, computes `+0x6C`, reads/writes that word and uses `0x17` as the full-health threshold.

The historically observed absolute address `FFC69E` is compatible with a particular retail runtime allocation, but it is not the stable architectural symbol and should not be hard-coded into new engine tooling.

### `FC4E` mission-scoped reuse — CONFIRMED

Community cheat documentation historically associated `FC4E` with civilians killed. That may describe its meaning in one mission/context, but it is not the architectural identity of the word.

The HQ computer objective proves reuse directly:

- scene 5 contains four `type_id 96` computer objects and one `type_id 125` objective controller;
- each type 96 adds `+2` to `FC4E` during initialization at `0x17F890–0x17F8A1`;
- reachable damage/destruction paths decrement the same word at `0x17F922`, `0x17FA04` and `0x17FA26`;
- type 125 repeatedly reads `FC4E` and drives the mission state/messages;
- message `0x3E` tells the player to “Destroy all of the computers”; message `0x40` confirms that the HQ was destroyed.

Therefore tooling and documentation must treat `FC4E` as a reusable mission/script counter-state word. A scenario-specific label such as `civilians_killed` is allowed only inside the scope where the corresponding scripts prove that meaning.

Reproducible evidence: `tools/rom_probe/computer_objective_probe.py`.

## Linked player-object model — M0.6B

The player uses two synchronized entities rather than one monolithic object.

Evidence:

- stage/world initialization stores an entity in `F9F8` at `0x0109D0`
- the player-control constructor allocates another entity and stores it in `FB6E` at `0x008284`
- allocator helper `0x00F8E8` promotes the newly allocated object into `A5`, after which the player callbacks/state are installed on it
- player entity-interaction callback `0x00356C` explicitly ignores `F9F8`, suppressing collision with its own linked avatar
- `0x009B60` loads `F9F8→A1` and `FB6E→A5`
- `0x009BE8` copies motion fields `+0x18/+0x1A/+0x56` from `FB6E` to `F9F8`
- `0x009C7A` copies geometry/position fields back from `F9F8` to `FB6E` when synchronization is allowed

Working interpretation: `FB6E` is the control/collision proxy and `F9F8` the linked world/render avatar representation. The exact original Beam terminology is unknown, so these names remain HIGH CONFIDENCE rather than CONFIRMED source names.

## `FB7C` action word

Confirmed direct values in player code:

- `0x0000`: idle / neutral
- `0x0002`: walking
- `0x0004`: ordinary weapon-fire class
- `0x0008`: special-action base bit — HIGH CONFIDENCE
- `0x000C`: special-action + fire bits
- `0x0028`: Uzi/flamethrower special phase combination
- `0x0048`: grenade special phase combination
- `0x0001`: auxiliary/transition bit — UNRESOLVED

This word is composable and must not be treated as an enum.

## `FB7E` overlay/context word

Current low-bit map:

- `0x0001`: roll active phase — HIGH CONFIDENCE
- `0x0002`: post-roll transition — HIGH CONFIDENCE
- `0x0004`: roll-fire/kneeling-fire context — CONFIRMED
- `0x0008`: normal-control/update context — exact label unresolved
- `0x0040`: JLLBFR maniac/chainsaw alternate-player overlay — HIGH CONFIDENCE
- `0x0080`: lock/fire pose latch — HIGH CONFIDENCE

Higher bits `0x0100–0x4000` occur in terminal/special sequences and remain intentionally unnamed pending stronger cause-level evidence.

## Temporary invulnerability

`0x009714` sets:

- `FB90 = 24`
- `FB92 = 1`
- `object+0x06 |= 0x0020`

The constructor uses the same object flag with `FB90 = 100`, providing a longer spawn-protection interval. `0x009CA0` decrements the duration and blink cadence and eventually tears down the protection state.

## Player object fields

See `ENTITY_MODEL.md`, `PLAYER_SYSTEM.md` and `ARCHETYPE_SYSTEM.md` for per-object offsets.
