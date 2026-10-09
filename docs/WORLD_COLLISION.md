# World Spatial Collision / Structure Grid

The per-scene long at `scene_record+0x0E` is the base of the scene's **world spatial structure/collision index**. Static loader, broadphase, dispatch analysis and M0.10 runtime authoring tests now prove the main path.

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

Relevant RAM fields:

```text
F976  world-structure resource base
F974  row-pointer table
F986  row stride in bytes
F988  row count
F98A/F98C  rounded world extents used during indexing
```

## Plane E and metatile scale — CONFIRMED

Gameplay map dimensions are **metatile dimensions**, not 8×8 world-pixel dimensions. The spatial layer follows the plane-E descriptor at `scene_record+0x26`.

One gameplay map entry occupies 32×32 world pixels. One collision broadphase cell covers 2×2 metatiles = 64×64 world pixels.

For plane-E dimensions `W×H`:

```text
world_width  = W * 32
world_height = H * 32
columns      = ceil(W / 2)
rows         = ceil(H / 2)
grid_bytes   = columns * rows * 2
```

The smallest referenced cell-list offset is exactly `grid_bytes` in every non-empty retail scene.

## Cell entry format — CONFIRMED

Each dense-grid entry is one 16-bit word.

- `0` = no candidate record.
- non-zero = offset from `F976` to a list of world-record references.

Each list element is a 16-bit offset from `F976`:

```text
bit15      terminal-entry flag
bits14..0  world-record offset
```

The engine supports multi-reference lists. Retail data currently reaches a maximum list length of one, but the runtime loop explicitly supports longer lists. Multiple cells may share one world record.

## World record base format — CONFIRMED

M0.10 runtime work resolves the ten-byte base structure to editor-facing world coordinates:

```text
+0x00  word  world_type
+0x02  word  x_min
+0x04  word  y_min
+0x06  word  x_max
+0x08  word  y_max
```

The four coordinates are world-pixel min/max bounds.

Most retail records appear in ten-byte units. Special handlers may interpret the geometry or associated state specially; no extra payload assumptions should be made until each type is checked.

## Entity callback bridge — CONFIRMED

The broadphase region `0x010ED0–0x011043`:

1. clamps entity shape to scene extents;
2. converts bounds to 64×64 cell ranges;
3. resolves row pointers through `F974`;
4. resolves cell-list offsets through `F976`;
5. resolves typed world records;
6. performs min/max overlap tests;
7. loads `object+0x38`;
8. calls that callback with the current record.

```text
scene world resource
  ↓ dense 64×64 spatial grid
cell reference list
  ↓ typed shared world record
min/max overlap
  ↓ object+0x38
entity-specific world response
```

## World-type dispatch — CONFIRMED

`world_record+0x00` is a behavior type.

Player callback `0x003750` dispatches by `type × 6` through absolute JMP entries at `0x003760`.

Projectile callback `0x002C10` dispatches by `type × 4` through BRA.W entries at `0x002C1C`.

Shared endpoints:

```text
0x002E16  RTS                          no response
0x002E18  standard collision resolver standard physical response
```

Retail uses 29 world types:

```text
1,2,3,4,5,6,8,9,10,11,12,
18,19,20,21,22,23,24,25,
27,28,31,32,33,34,35,36,37,38
```

### Mechanical groups

Player standard-resolution:

```text
1,2,3,4,5,6,8,9,10,12,31
```

Player no-op:

```text
11,18,23,24,25
```

Player special:

```text
19,20,21,22,27,28,32,33,34,35,36,37,38
```

Projectile standard-resolution:

```text
9
```

Projectile no-op:

```text
10,18,19,20,21,22,23,24,25,27,28,31,32
```

Projectile special:

```text
1,2,3,4,5,6,8,11,12,33,34,35,36,37,38
```

These remain mechanical labels unless independently tied to a visual/material identity.

## M0.10B targeted runtime proofs — CONFIRMED

The M10A relocation build is used as the logical parent. Each M10B build differs from M10A only at one `world_type` byte plus the checksum byte.

### Player collision isolation

Scene-0 record:

```text
offset     0x1C46
geometry   (736,544) .. (752,800)
type       9 -> 11
```

M10A blocks Harry while moving left. Changing only this record to type 11 allows Harry to cross the record and end on the west side. This is direct runtime confirmation that the selected record can have player collision disabled without globally bypassing `0x003750`.

Build SHA-1:

`80d9f2fc07d222af5d68f078de15271d27c8d66a`

### Projectile collision isolation

Scene-0 record:

```text
offset     0x1C6E
geometry   (464,496) .. (784,544)
type       9 -> 10
```

Type 10 retains the normal player handler but maps projectile handling to `0x002E16` no-op. A deterministic north-facing fire test is pixel-identical before the impact phase and diverges after firing: the retail impact presentation is absent/changed in the authored type-10 build.

Build SHA-1:

`b64de77121fc80fd6e4c3389f27d26bfb0843b58`

Tool/evidence:

```text
tools/build/m10b_targeted_collision.py
extracted_metadata/m10b_targeted_collision_runtime.json
```

These two records prove independent, local material behavior authoring for player and projectile collision.

## Retail structural totals — CONFIRMED

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

Type 9 is the primary generic solid class mechanically because both player and projectile use the standard resolver.

Scene 18 contains a valid all-zero spatial grid.

## Production consequence for Total Recall

The level format now has three independently authorable layers:

```text
visual metatile planes
persistent entity placements
world spatial structures / typed collision behavior
```

M10A/B prove that the third layer can be relocated and that an existing rectangle's material behavior can be changed locally at runtime.

### Authorized now

- inspect and label world records;
- relocate an existing complete world resource;
- change `world_type` while preserving geometry/grid membership;
- make one rectangle player-pass-through;
- make one rectangle projectile-pass-through while remaining player-blocking.

### Not authorized yet

- arbitrary geometry edits that cross broadphase cell membership;
- full cell/list regeneration;
- assuming rectangle-overlap rasterization reproduces retail priority choices;
- assigning visual material names to special world types without independent evidence.

## Next work

1. recover or replace the broadphase priority/partition policy;
2. implement a serializer for cell lists and dense-grid entries;
3. prove geometry expansion/movement across cell boundaries with runtime regression;
4. decode special world-type handlers where they matter for Total Recall mechanics;
5. integrate typed world records into the declarative scene compiler.
