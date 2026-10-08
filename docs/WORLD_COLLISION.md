# World Spatial Collision / Structure Grid

The per-scene long at `scene_record+0x0E` is no longer an unidentified auxiliary resource. Static loader and broadphase analysis proves that it is the base of the scene's **world spatial structure/collision index**.

Reproducible probe: `tools/rom_probe/world_collision_probe.py`.

## Scene loader — CONFIRMED

The loader around `0x010E2A`:

1. resolves the current scene through `FC42` and table `0x013B4A`;
2. reads `scene_record+0x0E`;
3. stores or expands that resource into base pointer `FFFFF976`;
4. derives spatial dimensions from the scene-local RAM structure referenced by `scene_record+0x14`;
5. allocates a long-pointer row table at `FFFFF974`.

Relevant RAM fields:

```text
F976  world-structure resource base
F974  row-pointer table
F986  row stride in bytes
F988  row count
F98A/F98C  rounded world extents used during indexing
```

## Grid geometry — CONFIRMED

The index is organized in **64×64-pixel spatial cells**.

For a map of `W×H` pixels:

```text
columns = ceil(W / 64)
rows    = ceil(H / 64)
```

Each grid cell occupies one 16-bit word. The loader's arithmetic matches this exactly:

- the X dimension is rounded to 64 pixels and converted to `columns × 2` bytes per row;
- the Y dimension is rounded to 64 pixels and converted to row count;
- the row table contains long pointers, so Y row indexing uses four-byte entries.

Across all 19 retail scenes the map dimensions and resource grids agree structurally.

## Cell entry format — CONFIRMED

A non-zero grid word is an offset from `F976` to a small list of world-record references.

Each reference is a 16-bit offset from the same base. Bit 15 marks the final entry in the list; the remaining 15 bits form the record offset.

The engine loop supports multiple records in a cell, even though current retail data reaches a maximum of one referenced record per cell list.

This extra indirection is useful: many cells can share the same world record without duplicating the record itself.

## World record header — PARTIALLY RECOVERED

A referenced world record begins with:

```text
+0x00  word  world_type
+0x02  word  overlap/geometry field A
+0x04  word  overlap/geometry field B
+0x06  word  overlap/geometry field C
+0x08  word  overlap/geometry field D
...          type-specific payload may follow
```

The four geometry words are consumed by the broadphase overlap routine before any entity callback is invoked. Their exact axis/order/world-origin labels are intentionally left unresolved; the engine's coordinate system includes offsets/conventions that should be decoded before naming them `left/right/top/bottom`.

## Entity callback bridge — CONFIRMED

The broadphase region `0x010F50–0x011018`:

1. converts the entity's bounds into spatial-grid ranges;
2. fetches candidate cells through `F974`;
3. resolves list offsets through `F976`;
4. performs record/entity overlap tests;
5. loads `object+0x38`;
6. calls it indirectly with the current world record available to the callback.

This proves the architecture:

```text
scene world resource
  ↓ 64×64 cell grid
candidate world record(s)
  ↓ overlap test
object+0x38
  ↓ entity-specific world response
player / projectile / other entity behavior
```

It directly explains why replacing the player's `+0x38` routine at `0x003750` with `RTS` produces the old community "walk through walls" cheat, and why bypassing projectile callback `0x002C10` produces "shoot through walls".

## World type dispatch — CONFIRMED

`world_record+0x00` is a behavior type, not merely a visual/material number.

The player callback at `0x003750` multiplies the type by six and jumps through a table of absolute `JMP` entries beginning at `0x003760`.

The projectile callback at `0x002C10` multiplies the type by four and dispatches through a table of `BRA.W` entries beginning at `0x002C1C`.

Two important common handlers are already clear:

```text
0x002E16  RTS                         -> no response
0x002E18  standard physical response  -> shared collision-resolution routine
```

The retail world resource uses only twelve world types:

```text
1, 2, 3, 4, 6, 9, 10, 11, 12, 18, 31, 33
```

Mechanical classification from dispatch behavior:

| world type | player | projectile | retail records |
|---:|---|---|---:|
| 1 | standard resolution | special | 3 |
| 2 | standard resolution | special | 4 |
| 3 | standard resolution | special | 5 |
| 4 | standard resolution | special | 11 |
| 6 | standard resolution | special | 5 |
| 9 | standard resolution | standard resolution | 105 |
| 10 | standard resolution | ignored / RTS | 15 |
| 11 | ignored / RTS | special | 17 |
| 12 | standard resolution | special | 2 |
| 18 | ignored / RTS | ignored / RTS | 2 |
| 31 | standard resolution | ignored / RTS | 2 |
| 33 | special | special | 1 |

These are deliberately mechanical labels. For example, type 10 can already be described as **player-blocking / projectile-pass-through**, but should not yet be named "fence", "glass", or another material without independent scene/handler evidence.

## Retail structural totals

Across the 19 scenes:

```text
grid words                1,157
non-empty grid cells        851
unique world records sum    172
cell→record references      314
used world types             12
```

Type 9 dominates with 105 world records and uses the standard response for both player and projectile, making it the primary generic solid class mechanically.

Scene 18's spatial grid is empty, which is also represented validly by this format.

## Production consequence for Total Recall

The level format is now separated into at least three authorable layers:

```text
visual tile planes
persistent entity placements
world spatial structures / collision types
```

The third layer is not a tile collision bitmap. It is a coarse 64×64 spatial index pointing to shared typed geometry records. This is favorable for Total Recall because world collision/interactions can be authored as geometry records independent of visual tiles.

Before inverse authoring is attempted, the remaining work is:

1. decode exact coordinate semantics of the four geometry words;
2. recover variable payload formats for the special world types;
3. label special dispatch handlers by behavior;
4. build a serializer that regenerates grid references after geometry edits;
5. prove a no-op round trip, then a one-record controlled edit, before integrating it into the scene compiler.
