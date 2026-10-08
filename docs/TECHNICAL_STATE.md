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

Active:
- M0.6 player state machine recovery
  - **M0.6A static control architecture recovered**
  - runtime/playtest validation and remaining special phases pending

Next:
- M0.7 first controlled engine extension

## Core architecture — CONFIRMED / HIGH CONFIDENCE

- `object+0x34`: entity↔entity interaction callback — HIGH CONFIDENCE.
- `object+0x38`: entity↔world/structure collision callback — HIGH CONFIDENCE.
- `object+0x50`: 8-way facing `0..7` — CONFIRMED.
- Player initialization near `0x0081C0` installs `+0x34 = 0x00356C`, `+0x38 = 0x003750`, `+0x50 = 4`.
- Generic `+0x34` invocation loop near `0x00EBC2`.
- Generic `+0x38` invocation loop near `0x010FF2`.
- Object traversal uses low-RAM 16-bit pointers into `FFxxxx`; a circular/sentinel list is rooted around `F9F4` — HIGH CONFIDENCE.

## Player control — M0.6A

The player-control system is layered, not a single enum:

```text
normalized input
+ FB7C action/state bitfield
+ FB7E overlay/context flags
+ per-frame D7 event bits
```

### Normalized input

- `F6EA`: previous input word — CONFIRMED
- `F6EC`: current input word — CONFIRMED
- `F6EE`: pressed edges — CONFIRMED
- `F6EE = current & (current XOR previous)` — CONFIRMED
- D-pad mask `0x000F` — CONFIRMED
- Fire edge bit 4 — CONFIRMED
- Roll edge bit 5 — CONFIRMED
- weapon cycle edge bits 12/14 — CONFIRMED
- Lock held bit 6 in current word — HIGH CONFIDENCE

### Action word

`FB7C` is a 16-bit action bitfield; `FB7D` is its low byte.

Confirmed structural values include:

- `0x0000` idle
- `0x0002` walking
- `0x0004` normal weapon fire
- `0x0008/0x000C/0x0028/0x0048` special-weapon/action combinations

### Overlay flags

`FB7E` is a separate 16-bit context/overlay word; `FB7F` is its low byte.

- bit `0x0001`: roll active phase — HIGH CONFIDENCE
- bit `0x0002`: post-roll transition — HIGH CONFIDENCE
- bit `0x0004`: roll-fire/kneeling-fire context — CONFIRMED
- bit `0x0080`: lock/fire pose latch — HIGH CONFIDENCE

### Roll-fire

Roll begins at `0x008600`, uses animation `0x0142`, and tests current Fire held near `0x0086B0`. If held, control enters the secondary weapon dispatcher at `0x0084BA`; supported weapons set the kneeling-fire overlay and reuse their firing handlers. Mine intentionally returns to normal control.

### Lock/strafe

Lock is an overlay, not a separate state. The synchronization region around `0x009BC0–0x009BE8` skips aim/display-facing resynchronization while `F6EC bit 6` is held, allowing locomotion facing to change independently.

### Nonfatal hit/invulnerability

`0x009714` begins temporary protection: `FB90=24`, `FB92=1`, `object+0x06 |= 0x0020`. `0x009CA0` maintains the timer/blink overlay. Normal action loops invoke this on `D7 bit 13` after terminal events are excluded.

### Terminal events / deaths

At least 27 active player-action sites converge on `0x009244` when `D7 & 0x63 != 0`.

- D7 bit 1 / external FC47 bit 5 → non-life-loss terminal/transition path at `0x0096B6` — HIGH CONFIDENCE
- D7 bit 5 → life-loss variant `0x00944E`
- D7 bit 0 → life-loss variant `0x00960C`
- remaining masked case, normally D7 bit 6 → default life-loss path

Therefore the `0x63` mask is a **terminal-event mask**, not a pure death mask.

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

## M0.6 remaining work

1. Runtime/playtest validation of action and overlay transitions.
2. Resolve exact semantics for `object+0x54`.
3. Name special weapon phases without overclaiming.
4. Determine higher `FB7E` bits and `F6F0`.
5. Produce regression probes for idle/walk/fire/roll/roll-fire/Lock/invulnerability/terminal routing.

## Parallel high-value work after M0.6

1. Determine object allocator, record size, pool/list linkage and lifetime rules.
2. Parse every gameplay resource package automatically.
3. Identify collision, spawn, object and objective/script data for levels.
4. Find gameplay palettes and player/enemy sprite descriptors.
5. Implement LZBeam inverse encoding and prove a byte-stable no-op rebuild.
