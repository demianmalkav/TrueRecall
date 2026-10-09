# M0.11B — Reusable Unified Scene Compiler

M11B turns the M11A transaction proof into a reusable compiler driven by one declarative scene manifest.

Tool:

`tools/build/scene_compiler.py`

Example:

`tools/build/examples/m11b_scene18_unified.json`

Regression probe:

`tools/rom_probe/unified_scene_compiler_probe.py`

Metadata:

`extracted_metadata/m11b_unified_scene_compiler.json`

Runtime validation is pending in the current container.

## Manifest surface

Schema:

`truerecall.scene_patch.v1`

A manifest selects one retail scene and may independently provide:

```text
map_operations
object_operations
world_operations
```

Current map operation:

```text
set_tile { plane, x, y, value }
```

Both `C000` and `E000` are addressable.

Persistent-placement operations:

```text
add
remove
replace
```

The compiler preserves Y ordering, rebuilds mixed 6/8-byte stride runs and encodes a new object stream/descriptor.

World operations:

```text
add
remove
replace
```

New world records may omit their binary offset. The compiler assigns a safe resource-relative offset after the preserved retail payload, then places a new deduplicated broadphase list pool after the authored record set.

## Expanded-ROM allocator

The compiler defaults to a 4 MiB output and a monotonic allocation arena beginning at `0x300000`.

Each edited resource family receives its own allocation(s). The scene record is then patched only for families that were actually changed:

```text
+0x0A  object-stream descriptor
+0x0E  world-collision resource
+0x1A  C000 map descriptor
+0x26  E000 map descriptor
```

A post-build containment assertion fails if any scene-record byte outside the expected pointer fields changes.

## Conservative world-resource policy

For world collision, M11B preserves the retail payload rather than reconstructing only known fields.

When a higher-address world resource exists, its base defines the payload boundary. This preserves unknown retail bytes exactly before authored overlays are applied.

The highest-address retail world resource currently falls back to the structurally recovered end; future work may require an explicit payload-boundary override before production edits to that particular scene.

Existing records keep their retail resource-relative offsets. Removed records may remain physically present but become unreachable from the rebuilt broadphase. Added records receive new offsets and are referenced through the rebuilt remote pool.

## M11B regression

The canonical regression semantically reproduces M11A on scene 18, but all expanded addresses are allocator-selected rather than proof constants.

### Map

```text
plane       C000
size        18×40
edit        (0,0) 0x00CD → 0x0001
changed     exactly 1 word
map desc    0x300000
map LZ      0x300010
```

### Placements

```text
retail count  40
new count     41
insert         health_pickup type 54 @ (128,120), stride 6
runs           8×2 / 6×1 / 8×38
object desc    0x300120
object LZ      0x300130
```

### World collision

Retail scene 18 has zero world records. M11B auto-assigns the new wall instead of receiving a hardcoded offset:

```text
record offset  0x0180
world_type     9
rect           (64,64) .. (80,256)
pool start     0x0190
world base     0x300300
```

The retail world payload boundary is conservatively identified from the next higher world-resource base:

```text
retail payload bytes = 0x017E
boundary source       = next_world_base
```

## Audited static build

```text
ROM size      4,194,304 bytes
checksum      0x3E9A
output SHA-1  fac81fdc87b76a75c9b590d58707b16fcd6a5f04
```

The generated ROM is not committed.

The regression also asserts the scene record changes only inside the expected pointer fields.

## Production consequence

TrueRecall now has one compiler surface capable of coordinating three previously separate domains:

```text
scene source
├─ gameplay map edits
├─ persistent entity placements
└─ typed world collision/material rectangles
        ↓
expanded-ROM allocator
        ↓
resource encoding / descriptor regeneration
        ↓
contained scene-record pointer patches
        ↓
checksum + structural post-build verification
```

This is the first practical foundation for authoring an original Total Recall level as a scene rather than as a collection of independent ROM experiments.

## Next gate

M11C should expand the scene source from patch operations into a fuller export/edit/rebuild workflow and add regression coverage across representative scene classes:

- a scene with mixed placement strides;
- a scene with non-empty world collision;
- a scene where C000/E000 dimensions differ;
- scene 6, whose broadphase dimensions require record-extent factorization;
- scene 18, whose retail world layer is empty.

After those static cross-scene proofs, restore runtime validation and run the unified compiler output through the deterministic BlastEm harness before declaring the scene pipeline production-authorized.
