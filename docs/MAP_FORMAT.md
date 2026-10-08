# Gameplay Map Format

The gameplay scene/map system is now enumerated from the consumer-backed master table rather than inferred from isolated packages.

## Master scene table — CONFIRMED

A pointer table at `0x013B4A` contains **19 non-null scene records** followed by a null pointer. The records begin at `0x013B9A` and are spaced exactly `0x2E` bytes (46 bytes) apart.

`FC42` is the current scene index. The loader multiplies it by four, indexes `0x013B4A`, and caches the selected record pointer in `FA1E`.

The retail record layout is:

```text
+0x00  word scene_flags              ; current retail records = 0x0003
+0x02  long palette_0_ptr
+0x06  long palette_1_ptr
+0x0A  long object_stream_desc_ptr   ; spatial object activation system
+0x0E  long world_collision_ptr      ; CONFIRMED
+0x12  word collision_resource_mode
+0x14  word primary_plane_state_ram  ; sign-extended low-RAM pointer

+0x16  first plane block (12 bytes)
       long graphics_desc_ptr
       long map_desc_ptr
       word vram_offset
       word name_table_base          ; 0xC000

+0x22  second plane block (12 bytes)
       long graphics_desc_ptr        ; zero in current retail table => share first graphics
       long map_desc_ptr
       word vram_offset
       word name_table_base          ; 0xE000
```

The low two bits of `scene_flags` are consumed separately during setup; all current retail records use `0x0003`, enabling both current plane contexts.

Reproducible probe: `tools/rom_probe/level_master_probe.py`.

## Palette fields — CONFIRMED

`+0x02` and `+0x06` are identical in all 19 current records and point to 128-byte Genesis CRAM images:

`4 palettes × 16 colors × 2 bytes = 128 bytes`

The first scene uses `0x09AC20`, the next `0x09ACA0`, then `0x09AD20`, etc. Every sampled color obeys the Genesis CRAM mask `0x0EEE`. These resources successfully reconstruct all 19 scene maps in native color.

The exact historical reason for having two palette fields remains unresolved because the current retail table gives them identical values.

## Graphics descriptor — CONFIRMED structure and direct/raw flag

A nonzero plane graphics pointer refers to a three-long descriptor:

```text
long graphics_lzbeam_ptr
long graphics_secondary_ptr
long graphics_aux_ptr
```

The first pointer is LZBeam-compressed Genesis tile data. Across all 19 scene records it decodes to a multiple of 32 bytes, i.e. complete 8×8 4bpp tiles.

### Secondary graphics pointer bit 31 — CONFIRMED

The loader around `0x00F4E4–0x00F518` proves the high-bit convention:

- if `graphics_secondary_ptr` is non-negative, the resource follows the decoded/copied path
- if bit 31 is set, the loader clears bit 31 and keeps the remaining pointer directly rather than decompressing it

Therefore values such as `0x800178DA`, `0x800239FA` and `0x80050000` are **direct/raw pointer references**, not LZBeam resources.

The third pointer is optional. Other code iterates entries from it when present, but exact entry semantics remain unresolved.

## Plane blocks and map descriptors — CONFIRMED

The scene record contains two 12-byte plane blocks. The first targets the Genesis name table at `0xC000`, the second `0xE000`.

The second plane's graphics descriptor is zero in all current retail records, and the loader explicitly reuses the first plane's graphics resource when this field is zero.

Each `map_desc_ptr` points to:

```text
long map_lzbeam_ptr
word width_tiles
word height_tiles
```

The decoded map size always satisfies:

`width × height × 2 bytes`

The two planes have independent dimensions. Examples:

- scene 5: C000 `104×48`, E000 `80×48`
- scene 6: C000 `71×110`, E000 `52×110`

A level editor must therefore preserve each plane's width and height independently.

## Scene dimension inventory — CONFIRMED

| Scene | C000 plane | E000 plane |
|---:|---:|---:|
| 0 | 107×45 | 107×45 |
| 1 | 20×253 | 20×253 |
| 2 | 50×39 | 50×39 |
| 3 | 9×13 | 9×13 |
| 4 | 50×78 | 50×78 |
| 5 | 104×48 | 80×48 |
| 6 | 71×110 | 52×110 |
| 7 | 74×60 | 74×60 |
| 8 | 45×16 | 45×16 |
| 9 | 70×69 | 70×69 |
| 10 | 95×54 | 95×54 |
| 11 | 60×58 | 60×58 |
| 12 | 45×80 | 45×80 |
| 13 | 78×66 | 78×66 |
| 14 | 13×400 | 13×400 |
| 15 | 32×43 | 32×43 |
| 16 | 36×44 | 36×44 |
| 17 | 46×31 | 46×31 |
| 18 | 18×40 | 18×40 |

The unusual `20×253` and `13×400` descriptors are real: their LZBeam streams decode to exactly the advertised sizes.

## World collision geometry — CONFIRMED

The long at scene-record `+0x0E` is the world's collision-geometry resource.

The setup path around `0x010E2A` selects the current scene record and consumes this field. It builds spatial lookup structures in `F974/F976`. The collision traversal around `0x010F92–0x01100A` reads geometry bounds and tests object overlap; when a shape overlaps the queried object, it invokes that object's `+0x38` world-collision callback.

This directly connects the scene descriptor to the generic entity/world collision interface recovered earlier.

### Collision resource mode `+0x12`

The word at `+0x12` controls whether the `+0x0E` resource is materialized/copied or used directly. All current retail scene records use value `1`, and the direct pointer is retained in `F976`.

## Primary plane-state pointer `+0x14` — HIGH CONFIDENCE

The word at scene-record `+0x14` is sign-extended as a low-RAM pointer. Most scenes use `FA62`; at least one uses `FA2A`. It is consumed by scene/plane setup and collision dimension logic, so `primary plane-state pointer` is the current working label.

## Object streaming descriptor `+0x0A` — PARTIALLY RECOVERED

The resource at scene-record `+0x0A` is **not LZBeam data**. Earlier LZ-looking headers were false positives; consumer code resolves the structure.

The setup path around `0x010CFA` treats it as a descriptor with at least:

```text
+0x00 word count
+0x02 word offset/index parameter
+0x04 word unresolved parameter
+0x06 long object/placement source pointer
+0x0A ... byte-pair encoded spatial indexing/control data
```

The subsystem allocates/maintains:

- `F9B8`: scene object/placement record data
- `F9C2`: `0x200`-byte spatial bucket/hash table
- `F9C4`: per-index 4-byte nodes when descriptor count > 0

Visible-region routines walk 32-pixel grid areas and eventually reach the object creation path around `0x0109EE`, which calls the generic entity allocator. This establishes `+0x0A` as the entry point for the **spatial object activation/streaming system**.

Exact placement-record field meanings, type coding and deactivation/reuse rules are still being recovered; do not yet reduce the descriptor to a simple “spawn list.”

## Previously isolated packages, now placed in the master table

### Scene 0

- palette: `0x09AC20`
- object-stream descriptor: record `+0x0A`
- world collision: record `+0x0E`
- first graphics descriptor: `0x00FFAA`
- graphics LZBeam: `0x014898` → `24,960` bytes = 780 tiles
- C000 map descriptor: `0x00FFBE` → map `0x01D4EE`, `107×45`
- E000 map descriptor: `0x00FFB6` → map `0x01C8FC`, `107×45`
- graphics secondary direct/raw pointer: `0x800178DA`
- graphics aux: `0x01BF7A`

### Scene 2

- palette: `0x09AD20`
- first graphics descriptor: `0x00FFE2`
- graphics LZBeam: `0x02667A` → `21,504` bytes = 672 tiles
- C000 map descriptor: `0x00FFF6` → map `0x01F0B8`, `50×39`
- E000 map descriptor: `0x00FFEE` → map `0x01EACA`, `50×39`
- graphics secondary direct/raw pointer: `0x80029418`
- graphics aux: `0x01E7D0`

## Tilemap entries

Gameplay planes use standard 16-bit Genesis name-table entries: tile index plus palette/flip/priority attributes. Applying each scene record's own CRAM image produces coherent full-map renders in native colors.

## Remaining high-value unknowns

The scene container is now mostly mapped. The principal unresolved areas are:

- exact record format and type semantics behind the `+0x0A` spatial object-streaming subsystem
- active/deactivation rules and per-scene simultaneous entity pressure against the 35-slot generic pool
- exact semantics of `graphics_aux`
- historical distinction between the two currently-identical palette fields
- meaning of the nonzero `FA2A` versus usual `FA62` primary plane-state choice

## Required proof before level editor work

1. Finish the object/placement record format and spatial streaming consumer.
2. Enumerate placed object types and measure active-pool headroom per scene.
3. Implement deterministic export/import for scene record, graphics descriptors, collision geometry, object-stream descriptor and both plane descriptors.
4. Implement LZBeam encoding.
5. Prove a byte-stable no-op extract→rebuild cycle before authoring new maps.
