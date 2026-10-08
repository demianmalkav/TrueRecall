# Object Spawn Graph

True Lies has two distinct object populations that must not be conflated in authoring tools:

1. **placement types** stored persistently in scene object streams;
2. **runtime-only types** created by scripts/native helpers as projectiles, effects, linked components or transient objects.

`tools/rom_probe/spawn_graph_probe_v2.py` recovers constant creation edges conservatively from reachable VM code.

## Generic spawn API — CONFIRMED

The object VM exposes six native wrappers around three allocators, with variants that optionally run type initialization:

| VM native | Working name | Native target |
|---:|---|---:|
| `0x00205C` | `alloc_generic` | `0x00F732` |
| `0x00206E` | `alloc_linked` | `0x00F7CC` |
| `0x002082` | `alloc_linked_offset` | `0x00F886` |
| `0x002096` | `spawn_generic_init` | allocator + `0x010102` |
| `0x0020D8` | `spawn_linked_init` | allocator + `0x010102` |
| `0x00211C` | `spawn_linked_offset_init` | allocator + `0x010102` |

For every reachable retail call classified by the probe, the child type is supplied through the canonical constant-word VM ABI. The probe asserts this rather than silently accepting dynamic arguments.

Two specialized projectile natives are added only because their child type is independently proven by their 68000 implementation:

- `0x00DB48` → runtime projectile type `170`;
- `0x00DAA4` → runtime projectile type `175`.

## Recovered graph — CONFIRMED structural coverage

On the canonical ROM:

- placed type IDs: **128**;
- retail placements: **2,449**;
- parent types with at least one proven constant child: **58**;
- unique constant parent→child edges: **79**;
- spawned children that are also ordinary placement types: only **54** and **68**;
- runtime-only child types: **42**.

The runtime-only set is:

```text
30, 85, 146, 152, 153, 154, 155, 156, 157, 158, 159, 160,
161, 163, 165, 167, 168, 169, 170, 175, 176, 177, 178, 179,
180, 185, 186, 192, 193, 201, 214, 215, 216, 217, 218, 219,
221, 222, 223, 225, 227, 229
```

This distinction is important for Total Recall tooling: a runtime component/projectile/effect must not automatically be offered in a level editor as a persistent placement class.

## Strong semantic anchors

The graph independently reinforces several already-recovered systems:

```text
type 113 supply crate → type 54 health pickup / type 68 shotgun ammo
type 46 truck         → type 227 shared destruction/effect child
type 104 boss class   → type 225 boss projectile
type 121 composite boss → type 170 standard projectile + type 186 component
type 5 / 7 shooters   → type 170
type 20 / 86 spread shooters → type 175
```

Other useful shared destruction/component families include:

```text
0, 6, 92 → 176
type 8, 33, 42, 46 → 227
type 96 → 169, 178
```

These are structural relationships only; they do not by themselves assign a visual/narrative name to an unresolved parent or child.

## Authoring consequence

The future scene/object compiler should model creation semantics separately:

```text
placed object class
    ↓ persistent scene placement
script / native behavior
    ↓ runtime spawn graph
transient projectile / component / effect / loot
```

This allows a Total Recall entity definition to specify both its persistent placement class and any runtime children without confusing the two namespaces.

## Evidence policy

An edge is emitted only when:

- the VM instruction is reachable by structural CFG traversal;
- the called native is a proven allocator/spawn wrapper;
- the child type is a constant argument at that call site; or
- a specialized native's fixed child is independently proven from its 68000 implementation.

No visual inference is used to create graph edges.
