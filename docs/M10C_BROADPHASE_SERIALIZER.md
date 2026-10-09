# M0.10C — World Broadphase Serializer

M0.10C recovers the scene-0 world collision broadphase as a deterministic authoring format rather than an opaque index.

## Resource layout — CONFIRMED

Scene 0 world resource begins at retail `0x07A42E` and is `0x23BE` bytes long.

The broadphase prefix is:

```text
0x0000..0x09B3  dense cell grid: 54×23 words
0x09B4..0x1059  deduplicated cell-list pool
0x105A          0xFFFF sentinel
0x105C..0x1F01  375 fixed 10-byte world records
```

The 54×23 grid follows directly from the scene-0 world dimensions: the 107×45 world-metatile space is grouped in 2×2 metatile broadphase cells. Each broadphase cell is therefore 64×64 world pixels.

## Grid/list encoding — CONFIRMED

Every non-zero grid word is a resource-relative pointer to a list in the pool.

There are:

- 1242 cells total;
- 985 non-empty cells;
- 373 unique non-zero list pointers;
- 373 list starts marked with bit 15;
- list lengths from 1 to 8 record references;
- 1702 bytes in the retail list pool.

The first record reference in each list is encoded as:

```text
0x8000 | record_offset
```

Additional references are plain 15-bit record offsets. The next bit-15-marked word starts the next list. Grid cells may share the same list pointer.

All 851 pool words resolve to one of the 375 ten-byte world records.

## Exact membership rule — CONFIRMED

The earlier working hypothesis that retail applied a hidden priority/pruning policy was wrong.

For every one of the 1242 cells, the retail list matches exactly the set of world records whose half-open rectangles intersect the 64×64 cell:

```text
record.x_min < cell.x_max
record.x_max > cell.x_min
record.y_min < cell.y_max
record.y_max > cell.y_min
```

No scene-0 exception exists.

List references are ordered by record offset descending.

Unique lists are emitted on first encounter while scanning cells row-major. Identical membership tuples reuse the first emitted list pointer.

Using those rules, `tools/build/world_collision_codec.py` reproduces both the retail grid and the entire 1702-byte list pool byte-for-byte.

## M10C authored geometry proof — STATIC CONFIRMED / RUNTIME PENDING

Target retail record:

```text
resource-relative offset 0x1C46
world type               9
geometry before          (736,544) .. (752,800)
```

M10C moves the rectangle 64 pixels east without changing its dimensions:

```text
geometry after           (800,544) .. (816,800)
```

The change moves membership from column 11 to column 12 across rows 8..12. Exactly ten cell membership tuples change: five remove the record from the old column and five add it to the new column.

The regenerated list pool shrinks from 1702 to 1698 bytes. The fixed record table remains at `0x105C`; unused pool tail bytes are filled with bit-15 sentinel words and are unreachable from the new grid.

Audited static build:

```text
ROM size      4,194,304
resource base 0x230000
checksum      0xDAE9
output SHA-1  5bf78090cbc54acbed1bc70211666f5f1d1645bf
```

Tool:

`tools/build/m10c_broadphase_geometry.py`

Metadata:

`extracted_metadata/m10c_broadphase_geometry.json`

The build reparses its authored record table, regenerates the broadphase again and asserts that generated grid/list membership is self-consistent.

## Production consequence

World collision geometry can now be represented declaratively as typed half-open rectangles and compiled into the engine's real broadphase format.

The remaining M10C gate is runtime validation of a geometry edit that crosses broadphase cells. Once validated, arbitrary authored rectangles can be integrated into the scene compiler with a record/list budget check.

## Next work

1. Runtime-test the `0x1C46` 64-pixel east shift against M10A using the deterministic BlastEm harness.
2. Generalize world-record export/import beyond scene 0.
3. Add pool-capacity and record-count assertions to the declarative compiler.
4. Integrate typed world rectangles into the scene authoring manifest.
5. Then move to creating new records, not merely editing existing record geometry.
