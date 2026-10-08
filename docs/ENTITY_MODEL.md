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
| `+0x54` | spatial/collision-response value; exact physical semantic/unit unresolved | HIGH CONFIDENCE classification |
| `+0x64` | animation-direction/state index used by `PlayFAnim13` | HIGH CONFIDENCE |

## Player constructor evidence

At approximately `0x0081C0`, player initialization installs:

- `+0x34 = 0x00356C`
- `+0x38 = 0x003750`
- `+0x50 = 4`

Projectile constructors write alternate functions into the same callback slots, proving that these slots belong to a generic entity interface rather than player-only code.

## Linked player entities — M0.6B

The playable character is implemented as two synchronized engine objects.

Evidence chain:

1. stage/world creation stores an object pointer in `F9F8` at `0x0109D0`
2. the player-control constructor allocates a second object; helper `0x00F8E8` makes the newly allocated `A0` object current as `A5`
3. that second object is stored in `FB6E` at `0x008284`
4. player callbacks and control state are installed on the `A5` companion
5. callback `0x00356C` explicitly returns when the other entity is `F9F8`, suppressing self-collision between the pair
6. `0x009B60` loads `F9F8→A1` and `FB6E→A5`
7. `0x009BE8` synchronizes motion fields from `FB6E` to `F9F8`
8. `0x009C7A` synchronizes geometry/position fields back from `F9F8` to `FB6E` when allowed

Working labels:

- `F9F8`: linked **world/render avatar entity** — HIGH CONFIDENCE
- `FB6E`: **player control/collision proxy/companion entity** — HIGH CONFIDENCE

The labels describe observed responsibility, not recovered Beam source names. Exact ownership/lifetime ordering is still unresolved.

## Generic callback loops

- Around `0x00EBC2`, the engine indirect-calls `object+0x34` after overlap tests.
- Around `0x010FF2`, the engine indirect-calls `object+0x38` during world/structure collision processing.

## `object+0x54` correction from M0.6

Earlier notes deliberately left `+0x54` unnamed because it appeared in player-control code. Static cross-references now show that it is **not a player control-mode field**.

Evidence:

1. An indexed collision-response table around `0x002D60` routes through eight small handlers around `0x003450–0x0034C8`.
2. Those handlers write `0x0700, 0x0F00, 0x1700, 0x1F00, 0x2700, 0x2F00, 0x3700, 0x3F00` into `object+0x54` while also setting collision-related flags.
3. Roll cleanup around `0x0086CA` reads `+0x54`, extracts/negates its signed high-byte component, clears the field and passes the resulting correction into a collision/position helper.
4. Player synchronization helpers around `0x009C60–0x009D40` copy `+0x54` together with geometry fields such as `+0x10/+0x12/+0x14/+0x16`.
5. Kneeling/roll-fire temporarily writes `0xFC00` to the same field and waits for generic update processing to return it to zero.

Conclusion: `+0x54` belongs to **spatial/collision response or positional correction**, possibly a fixed-point elevation/penetration/displacement quantity. The exact physical unit and axis remain unresolved. It must no longer be described as a control state.

## Lists / allocation

Object traversal uses 16-bit low-RAM pointers into the Genesis `FFxxxx` RAM region. A circular/sentinel list appears rooted around `F9F4`.

Still unresolved:

- exact object record size(s)
- allocator/free-list behavior
- pool count / maximum simultaneous entities
- linkage field offsets
- lifetime/destruction flags
- exact physical meaning/unit of `+0x54`
- exact ownership/lifetime ordering of the `F9F8`/`FB6E` player pair

These remain prerequisites before adding persistent new entity classes.
