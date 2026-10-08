# RAM Map

Known and working RAM locations for True Lies (World).

## Controller history / input

| RAM | Meaning | Status |
|---|---|---|
| `FFFFF6EA` | Previous controller word | CONFIRMED |
| `FFFFF6EC` | Current controller word | CONFIRMED |
| `FFFFF6EE` | Newly activated / rising-edge controller bits | CONFIRMED |
| `FFFFF6F0` | Bits active in consecutive controller samples | HIGH CONFIDENCE |

The input-update routine around `0x012B60..0x012BC8` copies old `F6EC` to `F6EA`, stores the new pad word in `F6EC`, computes `(old XOR new) AND new` into `F6EE`, and computes `old AND new` into `F6F0`.

Directional semantics of `F6EC` low nibble are HIGH CONFIDENCE: bit 0 Up, bit 1 Down, bit 2 Left, bit 3 Right. Bit 4 is Fire and bit 6 is Lock at HIGH CONFIDENCE. `F6EE` bit 7 behaves as Start/pause edge. Edge bits 5/12 select next weapon and bit 14 selects previous weapon in the weapon-cycle path.

## Player / inventory globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFFB6E` | Low-RAM pointer to player/control object | HIGH CONFIDENCE |
| `FFFFFB70` | Pistol ammo | CONFIRMED |
| `FFFFFB72` | Shotgun ammo | CONFIRMED |
| `FFFFFB74` | Uzi ammo | CONFIRMED |
| `FFFFFB76` | Grenades | CONFIRMED |
| `FFFFFB78` | Mines | CONFIRMED |
| `FFFFFB7A` | Flamethrower ammo | CONFIRMED |
| `FFFFFB7C` | Gameplay action/state bitfield word | CONFIRMED as bitfield; per-bit semantics ACTIVE RESEARCH |
| `FFFFFB7D` | Low byte of `FB7C`, not an independent variable | CONFIRMED |
| `FFFFFB7E` | Gameplay/player status bitfield word | CONFIRMED as bitfield; per-bit semantics ACTIVE RESEARCH |
| `FFFFFB7F` | Low byte of `FB7E`, not an independent variable | CONFIRMED |
| `FFFFFB8A` | Lives | HIGH CONFIDENCE |
| `FFFFFB8C` | Weapon selector as even offset `0,2,4,6,8,10` | CONFIRMED |
| `FFFFFB8E` | Weapon ownership bitmask | CONFIRMED |
| `FFFFFB90` | Post-hit/invulnerability timer or related field | HIGH CONFIDENCE |
| `FFFFFB92` | Post-hit companion flag | HIGH CONFIDENCE |
| `FFFFFC4E` | Civilian-kill counter | HIGH CONFIDENCE |
| `FFFFC69E` | Player health representation | HIGH CONFIDENCE |

Direct whole-word values observed at `FB7C`: `0,1,2,4,8,0x0C,0x28,0x48`.

`FB7E` is modified as a broad mask field across low and high bits, including masks in the `0x0100..0x4000` range. Treating `FB7D/FB7F` as separate controls is therefore incorrect.

## Object-list infrastructure

- Sentinel/root near `FFFFF9F4` — HIGH CONFIDENCE.
- Object links use 16-bit low-RAM addresses that are sign-extended into `FFxxxx` — HIGH CONFIDENCE.

## Player object fields

See `ENTITY_MODEL.md` and `PLAYER_SYSTEM.md` for per-object offsets.
