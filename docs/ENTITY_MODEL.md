# Entity Model

## Shared object interface

Current field map:

| Offset | Interpretation | Status |
|---|---|---|
| `+0x00` | active-list next pointer; free-list next pointer when unused | CONFIRMED |
| `+0x02` | active-list previous pointer | CONFIRMED |
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
| `+0x6C` | health word on the `F9F8` world/avatar player object | CONFIRMED for player avatar |

## Generic entity pool — CONFIRMED, pointer semantics corrected

The main gameplay entity allocator is statically reconstructed and guarded by `tools/rom_probe/entity_pool_probe.py`.

Pool geometry:

- record size: `0x72` bytes = **114 bytes**
- record count: **35**
- total heap allocation: `0x0F96` bytes = `35 × 0x72`
- `FFFFF9FE`: **pool-base pointer variable** — contains the low-RAM address returned by heap allocator `0x00012A2A`
- `FFFFF9FC`: **free-list-head pointer variable**
- `FFFFF9F2`: active object count
- `FFFFF9F4`: fixed active-list sentinel

### Important correction

Earlier documentation incorrectly described `FFFFF9FE` as if the pool physically began at that RAM address. The initialization code proves otherwise:

```text
MOVE.W  #0x0F96,D0
JSR     0x00012A2A        ; heap allocation
MOVE.W  A0,$F9FE          ; store returned pool pointer
MOVE.W  A0,$F9FC          ; initialize free-head pointer
```

Teardown later reads the pointer stored in `F9FE` and passes it to the heap free routine. Therefore `F9FE/F9FC` are metadata variables, not the pool storage itself.

The physical pool address is a runtime heap result and must not be hard-coded into new tools or patches.

### List structure

Unused records form a singly linked free list through `object+0x00`; `F9FC` stores the current head pointer.

Active records form a doubly linked circular list around the fixed sentinel at `F9F4`:

- `object+0x00` = next
- `object+0x02` = previous

`0x00FA40` inserts an active object into that list. `0x00F8F8` unlinks an object, decrements `F9F2`, and pushes the freed record back onto the free list.

### Allocator entries

- `0x00F732`: generic allocator from the free-list head
- `0x00F7CC`: linked/clone-style allocator that initializes geometry from another object
- `0x00F8F8`: destroy/free
- `0x00FA40`: active-list insertion
- `0x00012A2A`: underlying heap allocator used to reserve the pool block

This gives a hard upper bound of 35 records in this generic allocation. Practical gameplay capacity is lower whenever persistent objects—including the player's companion/proxy—consume records.

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

### Player health field — CONFIRMED

The scripted health pickup (`type_id 54`) independently resolves the low-RAM pointer stored in `F9F8`, adds object offset `0x6C`, reads that word, compares it against `0x17` and `0x0B`, and writes a replacement health value through the computed address.

Therefore the architectural health location is:

```text
world/avatar player object + 0x6C
```

The historically known absolute cheat address `FFC69E` is consistent with the retail allocator's deterministic runtime layout, but it should be treated as a concrete retail-build address rather than the engine-level identity of the field.

## Generic callback loops

- Around `0x00EBC2`, the engine indirect-calls `object+0x34` after overlap tests.
- Around `0x010FF2`, the engine indirect-calls `object+0x38` during world/structure collision processing.

## `object+0x54` correction from M0.6

Earlier notes deliberately left `+0x54` unnamed because it appeared in player-control code. Static cross-references show that it is **not a player control-mode field**.

Evidence:

1. An indexed collision-response table around `0x002D60` routes through eight small handlers around `0x003450–0x0034C8`.
2. Those handlers write `0x0700, 0x0F00, 0x1700, 0x1F00, 0x2700, 0x2F00, 0x3700, 0x3F00` into `object+0x54` while also setting collision-related flags.
3. Roll cleanup around `0x0086CA` reads `+0x54`, extracts/negates its signed high-byte component, clears the field and passes the resulting correction into a collision/position helper.
4. Player synchronization helpers around `0x009C60–0x009D40` copy `+0x54` together with geometry fields such as `+0x10/+0x12/+0x14/+0x16`.
5. Kneeling/roll-fire temporarily writes `0xFC00` to the same field and waits for generic update processing to return it to zero.

Conclusion: `+0x54` belongs to **spatial/collision response or positional correction**, possibly a fixed-point elevation/penetration/displacement quantity. The exact physical unit and axis remain unresolved.

## Remaining allocator/entity questions

The generic allocator geometry is no longer unknown. Remaining questions are narrower:

- physical heap address returned for the pool in each initialization path
- practical per-level slot budget after persistent/system entities are counted
- allocation ordering for every object class
- whether specialized auxiliary pools coexist alongside the 35-record generic pool
- lifetime ordering of the `F9F8`/`FB6E` player pair
- exact semantics of `object+0x30`
- exact physical meaning/unit of `+0x54`

These should be resolved before adding many new persistent entity classes, but they no longer block a single isolated M0.7 player-state experiment.
