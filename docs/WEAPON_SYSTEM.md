# Weapon System

The weapon system is table-driven and is a major extension seam.

## Selector and ownership

- `FFFFFB8C`: selected weapon as even offset `0,2,4,6,8,10` — CONFIRMED.
- `FFFFFB8E`: ownership bitmask — CONFIRMED.
- `0x003F` owns all six weapon families.

## Families

| FB8C | Weapon | Own bit | Ammo | Capacity / max | Primary handler | Roll-fire/secondary |
|---:|---|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | 15 | `0x008720` | `0x00871A` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | 99 | `0x008968` | `0x008962` |
| 4 | Uzi | `0x04` | `FFFFFB74` | 999 | `0x008C28` | `0x008C22` |
| 6 | Grenade | `0x08` | `FFFFFB76` | 9 | `0x008FC2` | `0x008FBC` |
| 8 | Mine | `0x10` | `FFFFFB78` | 9 | `0x00914A` | returns to normal control |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | 99 | `0x008E1C` | `0x008E16` |

Primary dispatch begins at `0x00845E`; the roll-fire secondary dispatch is at `0x0084BA`.

## Roll-fire integration — CONFIRMED

The secondary firearm/grenade entries set `FB7E bit 0x0004` before entering their normal handlers. This bit is therefore the roll-fire/kneeling-fire context.

Mine deliberately maps back to normal control instead of firing during the roll sequence.

This means roll-fire is implemented as **context + existing weapon handler**, not a parallel copy of the weapon system. This is favorable for new weapons: a future handler can choose whether to support the same context.

## `FB7C` action phases by weapon

M0.6 shows that the action word is composable rather than an enum.

### Pistol / Shotgun

Ordinary firing uses `FB7C = 0x0004`.

### Uzi / Flamethrower

Both automatic/continuous weapons use the same multi-phase pattern:

- initial entry uses normal fire bit `0x0004`
- active pulse/stream phase writes `0x0028` (`0x20 + 0x08`)
- sustain/recovery phase writes `0x000C` (`0x08 + 0x04`)
- current Fire held is tested to loop back into the active phase; release returns to main control

The exact animation-semantic names are not yet locked, but the structural grouping is HIGH CONFIDENCE.

Player special-turn logic tests `FB7C bit 5` (`0x20`) and routes to a dedicated handler around `0x009A22`, strongly tying that handler to the Uzi/flamethrower active phase.

### Grenade

Grenade entry writes `FB7C = 0x0048` (`0x40 + 0x08`) while the throw is primed/held. The routine explicitly tests current Fire held before advancing.

After release it writes `FB7C = 0x0008` for the throw/release/follow-through sequence.

Player special-turn logic tests `FB7C bit 6` (`0x40`) and routes to a separate handler around `0x009AB0`, strongly tying that control path to grenade priming.

### Mine

Mine placement uses `FB7C = 0x0008`, sharing the special/deployable base bit with the grenade release phase.

## Working action-bit interpretation

| Bit | Structural use | Status |
|---:|---|---|
| `0x0002` | locomotion/walk | CONFIRMED |
| `0x0004` | ordinary firing context | CONFIRMED |
| `0x0008` | special/deployable/continuous-weapon action context | HIGH CONFIDENCE |
| `0x0020` | Uzi/flamethrower active special phase modifier | HIGH CONFIDENCE |
| `0x0040` | grenade priming/held phase modifier | HIGH CONFIDENCE |

Bit `0x0001` remains unresolved and must not be assigned a convenient name prematurely.

## Extension questions

- projectile constructor mapping per weapon
- fire-rate / recoil / spread / sound parameters
- whether the six-entry primary/secondary tables can be enlarged in place or should be relocated
- HUD selection dependencies
- whether new Total Recall weapons should support roll-fire/kneeling context
- exact semantic names and timing of the automatic-weapon subphases

## Total Recall use

Do not merely reskin the six existing families. Preserve compatible behaviors, but make room for genuinely new weapon handlers and projectile behaviors after the table layout and relocation strategy are proven.

The primary/secondary dispatcher architecture suggests a clean way to implement new Quaid weapons while deciding per weapon whether roll-fire is supported.
