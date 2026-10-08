# ROM Map

Working map of important ROM offsets. Confidence is recorded explicitly.

| Offset / range | Working interpretation | Status |
|---|---|---|
| `0x00000200` | Reset entry | CONFIRMED |
| `0x00001AC2` | `PlayFAnim13: Invalid direction` diagnostic | CONFIRMED |
| `0x00001B40` | 8-way facing to movement helper | HIGH CONFIDENCE |
| `0x00001E1A` | `Homer routine in HOMING.A` diagnostic | CONFIRMED |
| `0x000027EE` | Projectile actor/entity interaction | HIGH CONFIDENCE |
| `0x00002C10` | Projectile world collision dispatch | HIGH CONFIDENCE |
| `0x0000356C` | Player actor/entity interaction callback | HIGH CONFIDENCE |
| `0x00003750` | Player world collision callback | HIGH CONFIDENCE |
| `0x00003F0A` | repeated `Homer routine in HOMING.A` | CONFIRMED |
| `0x00003F28` | `HOM_Angle routine in HOMING.A` | CONFIRMED |
| `0x00005C00–0x00005EB8` | Weapon selection / HUD region | HIGH CONFIDENCE |
| `0x000081C0` | Player object initialization | CONFIRMED |
| `0x0000845E` | Weapon fire dispatch region | HIGH CONFIDENCE |
| `0x00009714` | Start post-hit invulnerability | HIGH CONFIDENCE |
| `0x00009780–0x000098BA` | Player control/input dispatcher | HIGH CONFIDENCE |
| `0x00009892` | `Arnie says: Illegal player control mode` | CONFIRMED |
| `0x0000A918` | Storyboard/caption text area | HIGH CONFIDENCE |
| `0x0000AC3A` | Cutscene sequence descriptor table | CONFIRMED |
| `0x0000EBC2` | Generic entity/entity callback invocation | HIGH CONFIDENCE |
| `0x0000FFA8` area | Gameplay resource-package descriptors | HIGH CONFIDENCE |
| `0x00010FF2` | Generic world-collision callback invocation | HIGH CONFIDENCE |
| `0x000134A2` | Maxmus driver signature | CONFIRMED |
| `0x00014898` | Gameplay tileset package 01 | CONFIRMED |
| `0x0001C8FC` | Gameplay map package 01 layer A | CONFIRMED |
| `0x0001D4EE` | Gameplay map package 01 layer B | CONFIRMED |
| `0x0002667A` | Gameplay tileset package 02 | CONFIRMED |
| `0x0001EACA` | Gameplay map package 02 layer A | CONFIRMED |
| `0x0001F0B8` | Gameplay map package 02 layer B | CONFIRMED |

## Rule

No offset becomes a stable symbol merely because a cheat or static pattern suggests it. Stable labels require direct static proof, independent cross-evidence or dynamic confirmation.
