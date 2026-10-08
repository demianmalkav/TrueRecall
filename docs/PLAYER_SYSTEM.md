# Player System

## Confirmed anchors

- Player object construction near `0x0081C0`.
- Facing is an 8-way field at `object+0x50` with values `0..7`.
- Helper near `0x001B40` converts facing into X/Y movement fields `+0x18/+0x1A`.
- Retail diagnostics include `PlayFAnim13: Invalid direction`, `facing>7`, and `Arnie says: Illegal player control mode`.
- Player control/input dispatcher occupies approximately `0x009780–0x0098BA`.

## Important unresolved area

`object+0x54` must remain unnamed. Static analysis shows bit-pattern values such as `0x0700`, `0x0F00`, `0x1700` through `0x3F00`; calling it a control-mode field would be premature.

## M0.6 goals

1. Resolve `FB7C..FB7F` as physical input, edge-triggered input and/or control flags.
2. Trace idle, walk, strafe, roll, fire, post-roll crouch, hit and death transitions.
3. Identify animation-selection tables and state transition rules.
4. Determine which states suppress collision, firing or damage.
5. Produce a named state graph with reproducible probes.

## Extension target

The first controlled extension should add one isolated new player state/animation while preserving all original states. This is the proof required before implementing Total Recall-specific movement or melee.
