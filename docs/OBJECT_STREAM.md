# Scene Object / Placement Stream

This document describes the scene `+0x0A` spatial object-streaming subsystem. Evidence is from the canonical `True Lies (World)` ROM and the runtime consumer around `0x010764–0x010CFA`.

## Descriptor — CONFIRMED

Each of the 19 scene records points at an object-stream descriptor with this layout:

```text
+0x00  word placement_count
+0x02  word placement_start
+0x04  word placement_end
+0x06  long placement_source_lzbeam
+0x0A  byte-pair run table: (record_stride, quantity) ...
```

The run table continues until the quantities sum to `placement_count`.

For every retail scene:

`placement_end == placement_start + Σ(record_stride × quantity)`

Only record strides `6` and `8` occur in the retail data.

## Placement records — CONFIRMED

After LZBeam decoding, both record classes share this prefix:

```text
+0x00  word status_type
+0x02  word world_x
+0x04  word world_y
```

The 8-byte form additionally contains:

```text
+0x06  word instance_parameter
```

`type_id = status_type & 0x03FF`.

The 8-byte field is a per-instance parameter. Its type-specific meaning is not yet generalized and must not be given one universal label.

## Materialization marker — CONFIRMED

Bit 15 of `status_type` is the materialized marker.

The creation path skips negative source words and ORs `0x8000` into the source record after successful materialization. The allocated generic entity stores a low-RAM pointer back to its placement record in `object+0x32`.

This is important for editing: the source stream is persistent scene state, not merely immutable spawn coordinates.

## Streaming filter — CONFIRMED structurally

Before normal creation, the source `status_type` word is ANDed with `F9C0`. Retail object-stream setup uses `0x3800` for this filter.

The exact gameplay names of the individual filter bits remain unresolved. Do not turn `0x3800` into speculative difficulty/mission labels without consumer-backed evidence.

## Spatial organization — CONFIRMED

The subsystem buckets placements on a 32-pixel spatial grid.

The activation traversal around `0x010764` computes a viewport-adjacent region whose largest observed footprint is 11 columns × 9 rows of 32-pixel cells.

Ordinary-object cleanup around `0x0107D0` retains objects while approximately:

```text
-97 <= dx < 353
-97 <= dy < 257
```

There are class-specific exceptions, so this rectangle is not a universal lifetime rule.

## Retail inventory — CONFIRMED

Running the corrected structural probe over all 19 scenes gives:

- total placements: **2,449**
- 6-byte placement records: **1,689**
- 8-byte placement records: **760**
- unique retail `type_id` values: **128**
- pre-marked bit-15 placements: **10**
- maximum retail `type_id`: **138**

All observed retail placement type IDs remain below `0x00E6`, consistent with the generic allocation path examined so far.

## Per-scene pressure — STATIC UPPER BOUNDS, NOT RUNTIME OCCUPANCY

The current probe computes two purely spatial bounds:

1. `activation_11x9_cell_upper_bound`: placements in the largest activation footprint.
2. `keep_alive_rectangle_upper_bound`: placements geometrically inside the ordinary cleanup rectangle.

These ignore camera reachability, stream filter bits, already-consumed records, class-specific lifetime rules and destruction timing. They must not be reported as actual simultaneous entity counts.

| Scene | Placements | Unique types | Activation bound | Keep-alive bound |
|---:|---:|---:|---:|---:|
| 0 | 168 | 32 | 13 | 20 |
| 1 | 72 | 10 | 6 | 9 |
| 2 | 116 | 28 | 14 | 18 |
| 3 | 3 | 2 | 3 | 3 |
| 4 | 182 | 29 | 12 | 19 |
| 5 | 139 | 33 | 13 | 18 |
| 6 | 206 | 27 | 20 | 25 |
| 7 | 190 | 33 | 16 | 22 |
| 8 | 30 | 13 | 11 | 14 |
| 9 | 161 | 34 | 15 | 20 |
| 10 | 157 | 25 | 13 | 19 |
| 11 | 131 | 28 | 15 | 19 |
| 12 | 212 | 23 | 16 | 21 |
| 13 | 296 | 42 | 16 | 22 |
| 14 | 44 | 7 | 3 | 4 |
| 15 | 98 | 24 | 13 | 22 |
| 16 | 139 | 22 | 21 | **35** |
| 17 | 65 | 22 | 11 | 14 |
| 18 | 40 | 2 | 22 | 25 |

Scene 16 reaches a static keep-alive upper bound of 35, exactly the capacity of the confirmed generic entity pool. This is a design-relevant warning, but **does not prove** that 35 generic entities coexist at runtime.

## Most common retail type IDs

These counts are structural placement counts, not class names:

| type_id | placements |
|---:|---:|
| 71 | 154 |
| 123 | 148 |
| 44 | 137 |
| 54 | 125 |
| 38 | 125 |
| 112 | 100 |
| 68 | 99 |
| 124 | 97 |
| 29 | 86 |
| 31 | 82 |
| 116 | 81 |
| 126 | 77 |
| 7 | 61 |
| 82 | 53 |
| 37 | 49 |
| 43 | 45 |
| 39 | 43 |
| 113 | 42 |
| 53 | 36 |
| 24 | 34 |

Naming these IDs is the next major reverse-engineering step.

## Probe defect discovered during verification

The `main` version of `tools/rom_probe/level_objects_probe.py` contains a test-only off-by-two slice in its first safety signature:

```python
rom[0x010BB8:0x010BFE]
```

is compared against a 72-byte signature. The canonical signature actually spans:

```python
rom[0x010BB8:0x010C00]
```

The parser succeeds across all 19 scenes after correcting only that assertion boundary. This is a probe bug, not a ROM/data-model discrepancy.

## Next objectives

1. Map `type_id` values to constructor/type-table entries and then to behavioral classes.
2. Determine which placement classes consume one generic 0x72-byte pool slot and which immediately spawn/redirect specialized structures.
3. Refine scene-pool pressure using class semantics and actual lifecycle rules.
4. Generalize the 8-byte instance parameter per class.
5. Build deterministic export/import while preserving materialization/status semantics.
6. Prove a byte-stable no-op scene object-stream round trip before authoring Total Recall placements.
