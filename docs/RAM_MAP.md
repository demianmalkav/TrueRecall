# RAM Map

Known and working RAM locations for True Lies (World).

## Player / inventory globals

| RAM | Meaning | Status |
|---|---|---|
| `FFFFFB6E` | Low-RAM pointer to player object | HIGH CONFIDENCE |
| `FFFFFB70` | Pistol ammo | CONFIRMED |
| `FFFFFB72` | Shotgun ammo | CONFIRMED |
| `FFFFFB74` | Uzi ammo | CONFIRMED |
| `FFFFFB76` | Grenades | CONFIRMED |
| `FFFFFB78` | Mines | CONFIRMED |
| `FFFFFB7A` | Flamethrower ammo | CONFIRMED |
| `FFFFFB7C..FFFFFB7F` | Input/control flags | ACTIVE RESEARCH |
| `FFFFFB8A` | Lives | HIGH CONFIDENCE |
| `FFFFFB8C` | Weapon selector as even offset `0,2,4,6,8,10` | CONFIRMED |
| `FFFFFB8E` | Weapon ownership bitmask | CONFIRMED |
| `FFFFFB90` | Post-hit/invulnerability timer or related field | HIGH CONFIDENCE |
| `FFFFFB92` | Post-hit companion flag | HIGH CONFIDENCE |
| `FFFFFC4E` | Civilian-kill counter | HIGH CONFIDENCE |
| `FFFFC69E` | Player health representation | HIGH CONFIDENCE |

## Object-list infrastructure

- Sentinel/root near `FFFFF9F4` — HIGH CONFIDENCE.
- Object links use 16-bit low-RAM addresses that are sign-extended into `FFxxxx` — HIGH CONFIDENCE.

## Player object fields

See `ENTITY_MODEL.md` and `PLAYER_SYSTEM.md` for per-object offsets.
