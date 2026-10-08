# Player System

## Confirmed anchors

- Player object construction near `0x0081C0`.
- Facing is an 8-way field at `object+0x50` with values `0..7`.
- Helper near `0x001B40` converts facing into X/Y movement fields `+0x18/+0x1A`.
- Retail diagnostics include `PlayFAnim13: Invalid direction`, `facing>7`, and `Arnie says: Illegal player control mode`.
- Player control dispatcher occupies approximately `0x009780–0x0098BA`.

## Controller input pipeline — CONFIRMED

The physical/semantic controller history is kept at `FFFFF6EA..FFFFF6F0`, not at `FB7C..FB7F`.

The update routine around `0x012B60..0x012BC8` does the following:

1. copies prior `F6EC` into `F6EA`;
2. reads a new controller word and stores it in `F6EC`;
3. computes `(old XOR new) AND new` and stores it in `F6EE`;
4. computes `old AND new` and stores it in `F6F0`.

Working labels:

- `F6EA`: previous controller word — CONFIRMED.
- `F6EC`: current controller word — CONFIRMED.
- `F6EE`: newly activated / rising-edge bits — CONFIRMED.
- `F6F0`: bits active in consecutive samples — HIGH CONFIDENCE.

The low nibble of `F6EC` is directional input. A 16-entry direction-to-facing table near `0x0147C4` maps:

- bit 0 → facing 0
- bit 1 → facing 4
- bit 2 → facing 6
- bit 3 → facing 2
- diagonal combinations map to the intervening facings 1/3/5/7

This is consistent with Up / Down / Left / Right respectively — HIGH CONFIDENCE.

`F6EC` bit 4 is repeatedly tested by firearm handlers while firing and is therefore the Fire control — HIGH CONFIDENCE.

`F6EC` bit 6 is repeatedly tested by movement/control routines and matches the documented held Lock behavior — HIGH CONFIDENCE.

`F6EE` bit 7 is used as a one-shot menu/pause/start event in several subsystems — HIGH CONFIDENCE.

The weapon-selection path around `0x008448` consumes edge bits 5, 12 and 14. Bits 5 and 12 take the forward/next-weapon path; bit 14 takes the reverse/previous-weapon path. This matches the Genesis game's 3-button/6-button control scheme — HIGH CONFIDENCE.

## `FB7C` / `FB7E` correction — CONFIRMED

`FB7D` and `FB7F` are not independent variables; they are simply the low bytes of the words at `FB7C` and `FB7E`.

These words are gameplay state/control bitfields, not raw controller input.

Observed whole-word values written directly to `FB7C` include:

`0x0000, 0x0001, 0x0002, 0x0004, 0x0008, 0x000C, 0x0028, 0x0048`.

`FB7C` is initialized to `0x0001`, cleared and rewritten by movement/weapon/action handlers, and individual low-byte bits are tested in the player dispatcher. Exact per-bit semantics remain ACTIVE RESEARCH.

`FB7E` is an even broader player/gameplay status bitfield. Code sets/clears/toggles individual masks ranging from low bits through `0x4000`; this rules out treating it as a simple enumerated control-mode value.

## Dispatcher structure — HIGH CONFIDENCE

At approximately `0x009784` the dispatcher clears player displacement fields, updates generic entity/world state, then branches on `object+0x54` and low-byte bits of `FB7C/FB7E` before selecting helper routines such as `0x009A22`, `0x009AB0`, `0x009B12` and `0x0099D2`.

The embedded `Arnie says: Illegal player control mode` string at `0x009892` is an assert/failure anchor immediately after the expected mode paths.

## Important unresolved area

`object+0x54` must remain unnamed. Static analysis shows bit-pattern values such as `0x0700`, `0x0F00`, `0x1700` through `0x3F00`; calling it a control-mode field would be premature.

## M0.6 remaining goals

1. Assign exact per-bit meanings to `FB7C` and `FB7E` using write-sites plus behavioral paths.
2. Trace idle, walk, strafe/lock, roll, fire, post-roll crouch, hit and death transitions.
3. Identify animation-selection tables and state transition rules.
4. Determine which states suppress collision, firing or damage.
5. Produce a named state graph with reproducible probes.

## Reproducible probe

Run:

`python tools/rom_probe/player_state_probe.py <canonical_rom> --json`

The probe verifies the canonical SHA-1 before scanning and records controller/history anchors plus direct writes to the two gameplay state words.

## Extension target

The first controlled extension should add one isolated new player state/animation while preserving all original states. This is the proof required before implementing Total Recall-specific movement or melee.
