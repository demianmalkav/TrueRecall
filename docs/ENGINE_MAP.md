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

M0.6 player-control landmarks:

| Address | Working label | Status |
|---|---|---|
| `0x0082DA` | MainPlayerControl | HIGH CONFIDENCE |
| `0x008316` | NormalizePlayerControlFlags | HIGH CONFIDENCE |
| `0x00832A` | IdleControl | CONFIRMED action assignment |
| `0x0083A0` | WalkControl | CONFIRMED action assignment |
| `0x00842A` | ActionEdgeDispatch | HIGH CONFIDENCE |
| `0x00845E` | PrimaryWeaponDispatch | CONFIRMED |
| `0x0084BA` | RollFireSecondaryWeaponDispatch | CONFIRMED |
| `0x0084F4` | CycleWeaponForward | HIGH CONFIDENCE |
| `0x008528` | CycleWeaponBackward | HIGH CONFIDENCE |
| `0x008600` | RollControl | HIGH CONFIDENCE |
| `0x0086CA` | RollCleanup/Return | HIGH CONFIDENCE |
| `0x009244` | PlayerTerminalEventDispatch | HIGH CONFIDENCE |
| `0x009714` | BeginPlayerInvulnerability | HIGH CONFIDENCE |
| `0x009766` | PlayerControlOverlay/Synchronization | HIGH CONFIDENCE |
| `0x0098BA` | KneelingRollFireControl | HIGH CONFIDENCE |
| `0x0099D2` | UpdateLockFirePose | HIGH CONFIDENCE |
| `0x009B12` | UpdateFacingFromDpad | HIGH CONFIDENCE |
| `0x009CA0` | TickPlayerInvulnerability | HIGH CONFIDENCE |

Important architectural point: Lock, roll-fire and invulnerability are overlays/contexts layered over the main `FB7C` action word rather than exclusive enum states.

## Normalized input

The controller normalization routine around `0x012B62` maintains:

- previous input `F6EA`
- current input `F6EC`
- newly pressed edges `F6EE`

with `F6EE = current & (current XOR previous)`.

Known current/edge bits are documented in `PLAYER_SYSTEM.md` and `RAM_MAP.md`.

## Player terminal events

At least 27 player-action update sites mask per-frame event bits with `D7 & 0x63` and converge on `0x009244`.

This mask includes both life-loss routes and a non-life-loss terminal/transition route; it must not be named a pure death mask.

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
- Fire dispatcher begins around `0x00845E` — CONFIRMED.
- Six-family table-driven weapon system — CONFIRMED.
- Secondary dispatch `0x0084BA` provides a reusable roll-fire/kneeling entry seam — CONFIRMED.

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
2. Table-driven primary/secondary weapon dispatch.
3. Layered player action/overlay control model (`FB7C` + `FB7E`).
4. Normalized controller edge/current-word layer.
5. Data-driven gameplay map packages.
6. Resource decompression/reinsertion pipeline.

The layered player architecture is favorable for adding Quaid-specific actions because a new action can potentially occupy a new `FB7C` class while reusing Lock, invulnerability and other overlays rather than duplicating them.
