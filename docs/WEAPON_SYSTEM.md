# Weapon System

The weapon system is table-driven and is a major extension seam.

## Selector and ownership

- `FFFFFB8C`: selected weapon as even offset `0,2,4,6,8,10` — CONFIRMED.
- `FFFFFB8E`: ownership bitmask — CONFIRMED.
- `0x003F` owns all six weapon families.

## Families

| FB8C | Weapon | Own bit | Ammo | Capacity / max | Primary handler |
|---:|---|---:|---|---:|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | 15 | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | 99 | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | 999 | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | 9 | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | 9 | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | 99 | `0x008E1C` |

Working fire-dispatch region begins around `0x00845E`.

## Extension questions

- exact table entry layout
- projectile constructor mapping per weapon
- fire-rate / recoil / spread / sound parameters
- whether table length can be enlarged in place or should be relocated
- HUD selection dependencies

## Total Recall use

Do not merely reskin the six existing families. Preserve compatible behaviors, but make room for genuinely new weapon handlers and projectile behaviors after the table layout and relocation strategy are proven.
