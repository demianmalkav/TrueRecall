# Technical State — TrueRecall

Status vocabulary follows `AGENTS.md`.

## Canonical ROM — CONFIRMED

- Title: `True Lies (World)`
- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`
- Reset entry: `0x00000200`
- System signature: `GENSYSv1.4(May94)`
- Audio signature: `MAXMUS T Bardo 1993 V2.1a` at `0x0134A2`

## Reverse-engineering milestone

Completed:
- M0.1 ROM validated
- M0.2 static landmarks recovered
- M0.3 entity architecture recovered
- M0.4 asset/cutscene pipeline recovered
- M0.5 gameplay map format recovered
- M0.6a controller/input pipeline recovered

Active:
- M0.6b player gameplay-state bitfields and state-machine recovery

Next:
- M0.7 first controlled engine extension

Active work branch: `m0.6-player-state`. `main` remains the infrastructure checkpoint until M0.6 is ready to merge.

## Core architecture — CONFIRMED / HIGH CONFIDENCE

- `object+0x34`: entity↔entity interaction callback — HIGH CONFIDENCE.
- `object+0x38`: entity↔world/structure collision callback — HIGH CONFIDENCE.
- `object+0x50`: 8-way facing `0..7` — CONFIRMED.
- Player initialization near `0x0081C0` installs `+0x34 = 0x00356C`, `+0x38 = 0x003750`, `+0x50 = 4`.
- Generic `+0x34` invocation loop near `0x00EBC2`.
- Generic `+0x38` invocation loop near `0x010FF2`.
- Object traversal uses low-RAM 16-bit pointers into `FFxxxx`; a circular/sentinel list is rooted around `F9F4` — HIGH CONFIDENCE.

## Controller/input pipeline — CONFIRMED

Controller history is maintained in `FFFFF6EA..FFFFF6F0` by the routine region `0x012B60..0x012BC8`:

- `F6EA`: previous controller word — CONFIRMED.
- `F6EC`: current controller word — CONFIRMED.
- `F6EE`: newly activated / rising-edge bits — CONFIRMED.
- `F6F0`: bits active across consecutive samples — HIGH CONFIDENCE.

The implementation copies old `F6EC` to `F6EA`, stores the new pad word in `F6EC`, computes `(old XOR new) AND new` into `F6EE`, and computes `old AND new` into `F6F0`.

Directional input is the low nibble of `F6EC`; the direction→facing table near `0x0147C4` maps bits 0/1/2/3 to Up/Down/Left/Right at HIGH CONFIDENCE. `F6EC` bit 4 is Fire, bit 6 is Lock, and `F6EE` bit 7 is Start/pause at HIGH CONFIDENCE.

The weapon-cycle path around `0x008448` consumes edge bits 5/12 as next-weapon inputs and bit 14 as previous-weapon input — HIGH CONFIDENCE.

## Gameplay state words — ACTIVE RESEARCH

Previous documentation incorrectly grouped `FB7C..FB7F` as physical input. Static proof now shows:

- `FB7C` is a gameplay action/state bitfield word.
- `FB7D` is merely its low byte.
- `FB7E` is a broader player/gameplay status bitfield word.
- `FB7F` is merely its low byte.

Observed direct whole-word `FB7C` values: `0,1,2,4,8,0x0C,0x28,0x48`.

`FB7E` is modified with masks extending from low bits through `0x4000`, proving that it is not a simple control-mode enum. Exact bit semantics are the current M0.6b target.

Reproducible probe: `tools/rom_probe/player_state_probe.py`.

## Weapons — CONFIRMED

Weapon selector `FFFFFB8C` uses even offsets `0,2,4,6,8,10`; ownership mask is `FFFFFB8E`.

| FB8C | Weapon | Ownership bit | Ammo | Primary handler |
|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | `0x008E1C` |

## Asset pipeline — CONFIRMED

- Beam LZ compression is decoded successfully from this ROM.
- Strict scan found 101 structurally valid tile-aligned LZBeam candidates.
- Full-screen cutscenes use `LZ tiles + LZ 32×28 tilemap + raw 128-byte CRAM + auxiliary/caption pointer`.
- Cutscene sequence table begins at `0x00AC3A`; frame descriptors are 16 bytes.
- Fourteen full-color cutscene frames have been reconstructed without emulator screenshots.

## Gameplay map format — CONFIRMED

Package 01:
- graphics `0x014898` → 780 tiles
- layer A `0x01C8FC` → `107×45×2 = 9630` bytes
- layer B `0x01D4EE` → same

Package 02:
- graphics `0x02667A` → 672 tiles
- layer A `0x01EACA` → `50×39×2 = 3900` bytes
- layer B `0x01F0B8` → same

Both reconstruct coherent gameplay maps. Auxiliary/raw resources and collision/spawn/object layers remain unresolved.

## Player control — ACTIVE RESEARCH

- `0x009780–0x0098BA` belongs to player control dispatch.
- The retail ROM contains `Arnie says: Illegal player control mode` near `0x009892`.
- `object+0x54` is deliberately unnamed; it receives multiple bit-pattern values and must not be called a control mode until dynamic proof exists.

## Highest-value next work

1. Assign exact per-bit semantics to `FB7C` and `FB7E` and split the dispatcher into named states.
2. Trace roll, lock/strafe, fire, post-roll kneel, hit/invulnerability and death transitions.
3. Determine object allocator, record size, pool/list linkage and lifetime rules.
4. Parse every gameplay resource package automatically.
5. Identify collision, spawn, object and objective/script data for levels.
6. Implement LZBeam inverse encoding and prove a byte-stable no-op rebuild.
7. Extend the regression probe set before the first engine modification.
