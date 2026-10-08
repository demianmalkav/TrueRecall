# Engine Map

This file records subsystem boundaries, stable seams and working labels.

## Boot / system

- Reset entry: `0x00000200` — CONFIRMED.
- System signature: `GENSYSv1.4(May94)` — CONFIRMED.
- Interrupt/system handlers cluster around the low ROM/system region; full naming still pending.

## Player

- Initialization near `0x0081C0` — CONFIRMED.
- Facing vector helper near `0x001B40` — HIGH CONFIDENCE.
- Player actor-interaction callback: `0x00356C` — HIGH CONFIDENCE.
- Player world-collision callback: `0x003750` — HIGH CONFIDENCE.
- Player weapon/control region: `0x008140–0x009244` — HIGH CONFIDENCE.
- Post-hit invulnerability initializer: `0x009714` — HIGH CONFIDENCE.
- Player control dispatcher: `0x009780–0x0098BA` — HIGH CONFIDENCE.

## Generic entities

- `object+0x34`: actor/entity interaction callback — HIGH CONFIDENCE.
- `object+0x38`: world/structure collision callback — HIGH CONFIDENCE.
- Generic entity↔entity callback invocation near `0x00EBC2` — HIGH CONFIDENCE.
- Generic world-collision callback invocation near `0x010FF2` — HIGH CONFIDENCE.
- Intrusive circular object list rooted around RAM `F9F4` — HIGH CONFIDENCE.

## Projectiles

- Projectile actor-interaction routine around `0x0027EE` — HIGH CONFIDENCE.
- Projectile world-collision routine around `0x002C10` — HIGH CONFIDENCE.

## Weapons

- Selection/HUD region around `0x005C00–0x005EB8` — HIGH CONFIDENCE.
- Fire dispatcher begins around `0x00845E` — HIGH CONFIDENCE.
- Six-family table-driven weapon system — CONFIRMED.

## Rendering / assets

- LZBeam resource format — CONFIRMED.
- Cutscene descriptor table at `0x00AC3A` — CONFIRMED.
- Gameplay resource-package descriptors around bank-end tables such as `0x00FFA8` — HIGH CONFIDENCE.

## Audio

- Maxmus driver signature at `0x0134A2` — CONFIRMED.
- 68000↔Z80 Maxmus command interface — UNRESOLVED.

## Extension seams

Most promising seams for Total Recall additions:

1. Entity callback interface (`+0x34/+0x38`).
2. Table-driven weapon dispatch.
3. Player control/state dispatcher.
4. Data-driven gameplay map packages.
5. Resource decompression/reinsertion pipeline.
