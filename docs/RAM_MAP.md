# RAM Map

Known and working RAM locations for True Lies (World). Live continuation state is defined by `docs/PROJECT_STATE.md`.

## Normalized controller buffer — CONFIRMED / HIGH CONFIDENCE

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF6EA` | previous normalized controller word | CONFIRMED |
| `FFFFF6EC` | current normalized controller word | CONFIRMED |
| `FFFFF6EE` | newly pressed input edges | CONFIRMED |
| `FFFFF6F0` | inputs held across consecutive samples (`current & previous`) | CONFIRMED |

Input routine around `0x012B62` derives:

```text
F6EE = current & (current XOR previous)
F6F0 = current & previous
```

Known bits:

- low nibble `F6EC & 0x000F`: D-pad mask;
- `F6EC bit 6`: Lock held — HIGH CONFIDENCE;
- `F6EE bit 4`: Fire edge — CONFIRMED;
- `F6EE bit 5`: Roll edge — CONFIRMED;
- `F6EE bit 12`: next owned weapon — CONFIRMED;
- `F6EE bit 14`: previous owned weapon — CONFIRMED.

## Entity allocator globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF9F2` | active generic-entity count | CONFIRMED |
| `FFFFF9F4` | fixed active-list sentinel | CONFIRMED |
| `FFFFF9F8` | signed 16-bit RAM pointer to linked world/render avatar | CONFIRMED in canonical tested path |
| `FFFFF9FC` | free-list-head pointer variable | CONFIRMED |
| `FFFFF9FE` | generic pool-base pointer variable; stores heap allocation result | CONFIRMED |

`F9FE` is not the physical beginning of the pool. Initialization requests `0x0F96` bytes from heap allocator `0x12A2A` and stores the returned low-RAM pointer in `F9FE` and initially `F9FC`.

Generic entity pool design: 35 records × `0x72` bytes.

## Player / inventory globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFFB6E` | signed 16-bit RAM pointer to control/collision proxy | CONFIRMED in canonical tested path |
| `FFFFFB70` | pistol ammo | CONFIRMED |
| `FFFFFB72` | shotgun ammo | CONFIRMED |
| `FFFFFB74` | Uzi ammo | CONFIRMED |
| `FFFFFB76` | grenades | CONFIRMED |
| `FFFFFB78` | mines | CONFIRMED |
| `FFFFFB7A` | flamethrower ammo | CONFIRMED |
| `FFFFFB7C` | 16-bit player action/state bitfield | CONFIRMED structure |
| `FFFFFB7D` | low byte of `FB7C`; not separate | CONFIRMED |
| `FFFFFB7E` | 16-bit player overlay/context flags | CONFIRMED structure |
| `FFFFFB7F` | low byte of `FB7E`; not separate | CONFIRMED |
| `FFFFFB8A` | lives | HIGH CONFIDENCE |
| `FFFFFB8C` | weapon selector as even offset `0,2,4,6,8,10` | CONFIRMED |
| `FFFFFB8E` | weapon ownership bitmask | CONFIRMED |
| `FFFFFB90` | temporary invulnerability/blink duration | HIGH CONFIDENCE |
| `FFFFFB92` | invulnerability/blink cadence | HIGH CONFIDENCE |
| `FFFFFC4A` | difficulty: `0=Normal`, `1=Hard` | CONFIRMED |
| `FFFFFC4E` | civilian-related counter/state; exact cause semantics unresolved | HIGH CONFIDENCE relation |

## Canonical linked-player pointer semantics — CONFIRMED

M0.9C canonical runtime evidence corrected a v1 tooling error.

Retail uses `MOVEA.W` when loading `F9F8` / `FB6E`; each variable stores a **signed 16-bit RAM pointer**, not half of a 32-bit pointer.

Observed values in the tested gameplay path:

```text
FFFFF9F8 = 0xC632 -> sign-extended FFFFC632
FFFFFB6E = 0xC7FA -> sign-extended FFFFC7FA
```

Do not combine adjacent RAM words when reconstructing these pointers.

These object addresses are runtime allocations, not stable hard-coded entity locations.

During held-Y sprint, the object reached through F9F8 has:

```text
object+0x2A = 139
object+0x2C = 0x000A0000
```

and the descriptor remains stable through the observed native phase cycle.

The earlier M0.8 `0x0F0000` result remains player-local visual-component evidence only; it is not the canonical F9F8 descriptor in this path.

## Player health — CONFIRMED architectural location

Stable architectural health word:

```text
*(sign_extend_word(F9F8)) + 0x6C
```

Scripted health pickup resolves F9F8, computes `+0x6C`, reads/writes that word and uses `0x17` as full-health threshold.

Historically observed absolute `FFC69E` matches a specific retail allocation but must not be hard-coded into new tooling.

## Difficulty — `FC4A` — CONFIRMED

Options code around `0x0053F0–0x005530` toggles `FC4A` between zero/one for Normal/Hard.

Entity stat initializer `0x001EEC` multiplies `FC4A` by four to select Normal/Hard HP/damage table pointers before indexing with `object+0x2A`.

## `FC4E` caution

Community cheat documentation associated `FC4E` with civilians killed. Static script reachability confirms civilian-related manipulation, but reachable scripts increment, decrement and special-case compare it. Keep the broader label `civilian-related counter/state` until cause-level semantics are runtime-correlated.

## Linked player synchronization — CONFIRMED / HIGH CONFIDENCE

Evidence:

- stage/world initialization stores F9F8 at `0x0109D0`;
- player-control constructor stores FB6E at `0x008284`;
- callback `0x00356C` explicitly ignores F9F8;
- `0x009B60` loads the linked pair;
- `0x009BE8` copies motion fields `+0x18/+0x1A/+0x56` proxy→avatar;
- `0x009C7A` copies geometry/position fields avatar→proxy when permitted.

M0.9C additionally confirms native phase transfer through bridge `0x009D5E` with writer cluster:

```text
0x009D72  F9F8 +0x1E
0x009D7E  F9F8 +0x24
0x009D88  F9F8 +0x20
```

## `FB7C` action word

Known values:

- `0x0000`: idle / neutral — CONFIRMED;
- `0x0002`: walking — CONFIRMED;
- `0x0004`: ordinary weapon-fire class — CONFIRMED;
- `0x0008`: special-action base bit — HIGH CONFIDENCE;
- `0x000C`: special-action + fire bits — structural fact, exact phase unresolved;
- `0x0028`: Uzi/flamethrower special phase combination — HIGH CONFIDENCE;
- `0x0048`: grenade special phase combination — HIGH CONFIDENCE;
- `0x0001`: auxiliary/transition bit — UNRESOLVED.

Treat as a composable word, not an enum.

## `FB7E` overlay/context word

Current low-bit map:

- `0x0001`: roll active phase — HIGH CONFIDENCE;
- `0x0002`: post-roll transition — HIGH CONFIDENCE;
- `0x0004`: roll-fire/kneeling-fire context — CONFIRMED;
- `0x0008`: normal-control/update context — exact label unresolved;
- `0x0040`: JLLBFR alternate-player overlay — HIGH CONFIDENCE;
- `0x0080`: lock/fire pose latch — HIGH CONFIDENCE.

Higher bits `0x0100–0x4000` remain intentionally unnamed pending stronger evidence.

## Temporary invulnerability

`0x009714` sets:

```text
FB90 = 24
FB92 = 1
object+0x06 |= 0x0020
```

Constructor uses the same object flag with `FB90 = 100` for a longer spawn-protection window. `0x009CA0` decrements duration/cadence and tears down protection.

## Player native phase fields — CONFIRMED for M0.9C tested path

For F9F8 during sprint:

```text
object+0x1C  base phase = 0x08B6
object+0x1E  current phase cycles 08B6/08B8/08BA/08BC/08BE/08C0
object+0x20  resolved mapping-record offset
object+0x22  observed mirror of resolved record in current trace
object+0x24  encoded animation entry
object+0x2A  archetype/stat identity = 139
object+0x2C  descriptor = 0x000A0000
```

Raw phase deltas from `+0x1C` are exactly `0,2,4,6,8,10` in the observed cycle.

## Cross-references

See:

- `ENTITY_MODEL.md` for generic object fields;
- `PLAYER_SYSTEM.md` for control semantics;
- `ARCHETYPE_SYSTEM.md` for archetype initialization;
- `docs/M09C_NATIVE_SEQUENCE_SEAM.md` for canonical native-phase integration;
- `extracted_metadata/m09c_canonical_phase_bridge.json` for persisted runtime evidence.
