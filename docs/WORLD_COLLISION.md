# World Spatial Collision / Structure Grid

The per-scene long at `scene_record+0x0E` is the base of the scene's **world spatial structure/collision index**. Static loader, broadphase and dispatch analysis now prove the main runtime path.

Reproducible probe: `tools/rom_probe/world_collision_probe.py`.

## Scene loader — CONFIRMED

The loader around `0x010E2A`:

1. resolves the current scene through `FC42` and table `0x013B4A`;
2. reads `scene_record+0x0E`;
3. stores/expands that resource into base pointer `FFFFF976`;
4. reads a packed mode/state reference from `scene_record+0x12/+0x14`;
5. derives spatial dimensions from the selected plane/state structure;
6. allocates a long-pointer row table at `FFFFF974`.

All 19 retail scenes use:

```text
scene+0x12 = 1       ; direct-ROM resource mode
scene+0x14 = FA62    ; 18 scenes
             FA2A    ; scene 3
```

The engine contains an alternate `mode=0` copy/expansion path, but retail scene records do not use it for this layer.

Relevant RAM fields:

```text
F976  world-structure resource base
F974  row-pointer table
F986  row stride in bytes
F988  row count
F98A/F98C  rounded world extents used during indexing
```

## Plane E and metatile scale — CONFIRMED

A key correction to the earlier static map visualization is that gameplay map dimensions are **metatile dimensions**, not 8×8 world-pixel dimensions.

The spatial layer follows the **plane-E descriptor at `scene_record+0x26`**.

One gameplay map entry occupies **32×32 world pixels**. Therefore one collision broadphase cell covers exactly **2×2 metatiles = 64×64 world pixels**.

For plane-E dimensions `W×H` in metatiles:

```text
world_width  = W * 32 pixels
world_height = H * 32 pixels
columns      = ceil(W / 2)
rows         = ceil(H / 2)
grid_bytes   = columns * rows * 2
```

This is independently validated by the resource boundary: in every non-empty retail scene, the smallest referenced cell-list offset is **exactly `grid_bytes`**.

Scenes 5 and 6 are especially useful proofs because plane C and plane E have different widths:

```text
scene 5 plane E = 80×48  -> 40×24 cells -> 0x780 grid bytes
scene 6 plane E = 52×110 -> 26×55 cells -> 0xB2C grid bytes
```

The first list offset in those resources is exactly `0x780` and `0xB2C`, respectively. Using plane C would fail.

## Cell entry format — CONFIRMED

Each dense-grid entry is one 16-bit word.

- `0` = no candidate world record for that cell.
- non-zero = offset from `F976` to a list of world-record references.

Each list element is itself a 16-bit offset from `F976`:

```text
bit15      terminal-entry flag
bits14..0  world-record offset
```

The broadphase supports multiple references per list. Retail data currently reaches a maximum list length of one, but the runtime loop explicitly increments through further words until the high-bit terminal reference is consumed.

Multiple grid cells may share the same world record, avoiding geometry duplication.

## World record base format — CONFIRMED structure

Every referenced world record has at least the following ten-byte base structure:

```text
+0x00  word  world_type
+0x02  word  axis-A minimum
+0x04  word  axis-B minimum
+0x06  word  axis-A maximum
+0x08  word  axis-B maximum
```

The ordering follows directly from the overlap test around `0x010FB0`.

The temporary entity shape uses two min/max pairs as well. The broadphase tests the world-record pairs against the entity pairs before invoking callbacks. Exact editor-facing X/Y naming and camera/world-origin conventions are still being normalized, so the repository intentionally records the axes neutrally for now.

Most retail records appear consecutively in ten-byte units. Special handlers may interpret the base geometry differently; no extra payload should be assumed absent until each special type is checked.

## Entity callback bridge — CONFIRMED

The broadphase region `0x010ED0–0x011043`:

1. clamps the entity shape to scene extents;
2. converts its bounds to 64×64 cell ranges;
3. resolves row pointers through `F974`;
4. reads cell-list offsets through `F976`;
5. resolves world-record offsets;
6. performs min/max overlap tests;
7. loads `object+0x38`;
8. calls that callback indirectly with the current world record.

Architecture:

```text
scene world resource
  ↓ dense 64×64 spatial grid
cell reference list
  ↓ shared typed world record
min/max overlap test
  ↓ object+0x38
entity-specific world response
```

This is the engine path behind the known community effects of bypassing `0x003750` (player walks through walls) and `0x002C10` (projectiles shoot through walls).

## World-type dispatch — CONFIRMED

`world_record+0x00` is a behavior type.

Player callback `0x003750` dispatches by `type × 6` through absolute JMP entries at `0x003760`.

Projectile callback `0x002C10` dispatches by `type × 4` through BRA.W entries at `0x002C1C`.

Two shared endpoints provide useful mechanical anchors:

```text
0x002E16  RTS                          no response
0x002E18  standard collision resolver standard physical response
```

Retail uses **29** world types:

```text
1,2,3,4,5,6,8,9,10,11,12,
18,19,20,21,22,23,24,25,
27,28,31,32,33,34,35,36,37,38
```

### Mechanical groups

Player standard-resolution types:

```text
1,2,3,4,5,6,8,9,10,12,31
```

Player ignored/no-op types:

```text
11,18,23,24,25
```

Player special-handler types:

```text
19,20,21,22,27,28,32,33,34,35,36,37,38
```

Projectile standard-resolution type:

```text
9
```

Projectile ignored/no-op types:

```text
10,18,19,20,21,22,23,24,25,27,28,31,32
```

Projectile special-handler types:

```text
1,2,3,4,5,6,8,11,12,33,34,35,36,37,38
```

These are behavior labels only. For example, type 10 is mechanically **player-blocking / projectile-pass-through**, but it is not yet called fence/glass/etc. without independent scene/handler evidence.

## Retail structural totals — CORRECTED

Across all 19 scenes:

```text
dense grid words          16,000
non-empty grid cells      12,632
unique world records sum   3,035
cell→record references     5,686
used world types              29
```

Most common record types:

```text
type 9   1266
type 10   543
type 3    214
type 11   201
type 2    187
type 4    149
type 12   114
type 6    109
type 31    98
```

Type 9 is the primary generic solid class mechanically because both player and projectile use the standard collision resolver.

Scene 18 contains a valid all-zero spatial grid.

## Production consequence for Total Recall

The level format is now separated into at least three authorable layers:

```text
visual metatile planes
persistent entity placements
world spatial structures / collision behavior
```

The third layer is not a tile collision bitmap. It is a **64×64 broadphase index over typed shared min/max geometry records**. This is favorable for Total Recall because collision and special world behavior can be authored independently from visual art.

Remaining work before inverse authoring:

1. normalize axis-A/B to editor-facing X/Y and document world/camera origin conventions;
2. decode the semantics of special world-type handlers;
3. determine whether any used type requires data beyond the ten-byte base record;
4. build a serializer that regenerates cell reference lists from geometry;
5. prove a byte-stable/no-op rebuild and then one controlled geometry/type edit;
6. integrate this layer into the existing scene compiler only after those proofs pass.
