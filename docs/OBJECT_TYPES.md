# Object Type Catalog

This document maps retail placement `type_id` values to functional identities only when the ROM itself provides enough evidence. Visual names are not assigned from guesswork.

## Standard pickup family — CONFIRMED

The object VM scripts for the standard pickup family all install actor-contact callback `0x009DF8`. Their identities are recoverable from the global inventory fields they read/write and, for weapons, from the ownership-grant helper.

| type_id | Working label | ROM evidence | Status |
|---:|---|---|---|
| 51 | Flamethrower weapon pickup | operates on `FB7A`; calls VM native `0xAEF8` with selector `10`; native reaches `0x5CF4`, which ORs a selector-derived bit into `FB8E` | CONFIRMED |
| 52 | Flamethrower fuel pickup | operates on `FB7A`; does **not** call weapon-acquisition native | CONFIRMED |
| 53 | Grenade pickup | modifies `FB76`; ORs `0x0008` into `FB8E` | CONFIRMED |
| 54 | Health pickup | resolves `F9F8` avatar pointer, accesses `avatar+0x6C`, compares against `0x17` and `0x0B`, and writes health through the computed address | CONFIRMED |
| 61 | Extra-life pickup | reads `FB8A`, compares against `9`, increments and stores the lives counter | CONFIRMED |
| 62 | Mine pickup | modifies `FB78`; ORs `0x0010` into `FB8E` | CONFIRMED |
| 68 | Shotgun-ammo pickup | operates on `FB72`; no weapon-acquisition native | CONFIRMED |
| 69 | Shotgun weapon pickup | tests `FB8E & 0x0002`, operates on `FB72`, invokes weapon-acquisition selector `2` | CONFIRMED |
| 70 | Uzi weapon pickup | tests `FB8E & 0x0004`, operates on `FB74`, invokes weapon-acquisition selector `4` | CONFIRMED |
| 71 | Uzi-ammo pickup | operates on `FB74`; no weapon-acquisition native | CONFIRMED |

Reproducible probe: `tools/rom_probe/pickup_type_probe.py`.

### Health field

The health pickup provides direct VM-level evidence that the `F9F8` world/avatar object's word at `+0x6C` is player health. It dynamically resolves the low-RAM pointer stored at `F9F8`, adds `0x6C`, reads the word, compares it against `0x17` and `0x0B`, and writes a replacement value through that address.

The long-known external cheat address `FFC69E` is consistent with this object-relative health field when the retail allocator produces its usual deterministic layout, but the project should treat `avatar+0x6C` as the architectural identity and `FFC69E` as a build/runtime address, not as a hard-coded engine invariant.

## Mission/key/objective pickup family — HIGH CONFIDENCE

Several low-frequency types share the same pickup/contact callback but operate on `FC54` and related mission-state words rather than weapon/ammo globals. They are therefore classified as mission/key/objective pickups or interactables, without assigning film/gameplay names until scene correlation is complete.

Strong candidates include type IDs `9, 55, 56, 58, 60, 63, 64, 65, 66, 67`.

Evidence:

- scripts test/set individual bitmasks in `FC54`;
- some also consult `FBEC`;
- placement counts are low and scene-specific;
- the scripts use the same `0x009DF8` contact interface as confirmed inventory pickups;
- several trigger VM natives around `0xAF08`, consistent with mission/UI side effects rather than generic enemy AI.

Exact narrative meanings remain unresolved.

## Pickup VM/API observations

`0x00AEF8` is a VM native wrapper around engine helper `0x005CF4`. The helper indexes a selector-to-bit table and ORs the resulting bit into `FB8E`, making it a weapon-acquisition operation rather than a generic HUD refresh.

This distinguishes weapon pickups from ammo-only pickups even when both operate on the same ammo word.

## Deliberately unresolved

The following should not yet be frozen:

- exact refill quantities for branch-heavy ammo scripts until VM control flow is decoded end-to-end;
- exact story/key names for `FC54`-based mission pickups;
- gameplay identities for enemy/civilian/prop callback families solely from placement counts;
- direct-code types `10` and `101` in scene 14.

## Next classification targets

1. Recover the native-call API used by scripted objects.
2. Identify animation/sprite descriptor writes in object scripts.
3. Correlate callback families with scene distribution and visual resources.
4. Assign enemy/civilian/prop names only after two independent evidence paths agree.
