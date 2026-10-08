# RAM Map

Known and working RAM locations for True Lies (World).

## Normalized controller buffer — M0.6

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF6EA` | previous normalized controller word | CONFIRMED |
| `FFFFF6EC` | current normalized controller word | CONFIRMED |
| `FFFFF6EE` | newly pressed input edges | CONFIRMED |
| `FFFFF6F0` | related current/previous input helper | UNRESOLVED |

The input routine around `0x012B62` copies `F6EC→F6EA`, decodes the new controller state into `F6EC`, then computes `F6EE = current & (current XOR previous)`.

Known normalized bits:

- low nibble `F6EC & 0x000F`: D-pad direction mask
- `F6EC bit 6`: Lock held — HIGH CONFIDENCE
- `F6EE bit 4`: Fire edge — CONFIRMED
- `F6EE bit 5`: Roll edge — CONFIRMED
- `F6EE bits 12/14`: weapon-cycle edges — CONFIRMED

## Player / inventory globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFFB6E` | low-RAM pointer to main player object | HIGH CONFIDENCE |
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
| `FFFFFC4E` | civilian-kill counter | HIGH CONFIDENCE |
| `FFFFC69E` | player health representation | HIGH CONFIDENCE / legacy evidence; direct damage path still to map |

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
- `0x0040`: hidden/special visual-control toggle — UNRESOLVED
- `0x0080`: lock/fire pose latch — HIGH CONFIDENCE

Higher bits are intentionally unnamed pending stronger evidence.

## Temporary invulnerability

`0x009714` sets:

- `FB90 = 24`
- `FB92 = 1`
- `object+0x06 |= 0x0020`

The constructor uses the same object flag with `FB90 = 100`, providing a longer spawn-protection interval. `0x009CA0` decrements the duration and blink cadence and eventually tears down the protection state.

## Object-list infrastructure

- Sentinel/root near `FFFFF9F4` — HIGH CONFIDENCE.
- Object links use 16-bit low-RAM addresses that are sign-extended into `FFxxxx` — HIGH CONFIDENCE.
- `FFFFF9F8` is repeatedly paired with the main player object during pose/facing synchronization; exact object role remains deliberately unnamed.

## Player object fields

See `ENTITY_MODEL.md` and `PLAYER_SYSTEM.md` for per-object offsets.
