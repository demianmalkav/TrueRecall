# Entity Model

## Shared object interface

Current field map:

| Offset | Interpretation | Status |
|---|---|---|
| `+0x04` | flags/type word | PARTIAL |
| `+0x06` | flags word | PARTIAL |
| `+0x18` | X movement/displacement | CONFIRMED |
| `+0x1A` | Y movement/displacement | CONFIRMED |
| `+0x30` | owner/linked-object low-RAM pointer candidate | HYPOTHESIS |
| `+0x34` | entity↔entity interaction callback | HIGH CONFIDENCE |
| `+0x38` | entity↔world/structure collision callback | HIGH CONFIDENCE |
| `+0x4C` | state/cooldown field | UNRESOLVED |
| `+0x50` | facing 0..7 | CONFIRMED |
| `+0x54` | unknown bitfield/state value; do not name yet | UNRESOLVED |
| `+0x64` | animation-direction/state index used by `PlayFAnim13` | HIGH CONFIDENCE |

## Player constructor evidence

At approximately `0x0081C0`, player initialization installs:

- `+0x34 = 0x00356C`
- `+0x38 = 0x003750`
- `+0x50 = 4`

Projectile constructors write alternate functions into the same callback slots, proving that these slots belong to a generic entity interface rather than player-only code.

## Generic callback loops

- Around `0x00EBC2`, the engine indirect-calls `object+0x34` after overlap tests.
- Around `0x010FF2`, the engine indirect-calls `object+0x38` during world/structure collision processing.

## Lists / allocation

Object traversal uses 16-bit low-RAM pointers into the Genesis `FFxxxx` RAM region. A circular/sentinel list appears rooted around `F9F4`.

Still unresolved:

- exact object record size(s)
- allocator/free-list behavior
- pool count / maximum simultaneous entities
- linkage field offsets
- lifetime/destruction flags

These are M0.6/M0.7 prerequisites before adding persistent new entity classes.
