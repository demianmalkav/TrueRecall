# M0.11A — Unified Scene Transaction Proof

M11A is the first build that edits three independent scene-resource families in one deterministic transaction:

1. gameplay tilemap;
2. persistent object placements;
3. world collision/material geometry.

The proof deliberately targets retail scene 18 because it contains normal tilemaps and object placements but an empty world-collision layer. This makes a newly authored world rectangle unambiguous: no retail collision record is reused or replaced.

Runtime validation is pending in the current execution environment.

## Base scene

Scene 18 record:

```text
scene record = 0x013ED6
C000 map     = 18×40
objects      = 40 placements, all stride 8
world        = 9×20 broadphase grid, 0 retail records
```

The canonical 2 MiB ROM is expanded to 4 MiB for the proof.

## Transaction 1 — gameplay map

The C000 map descriptor is relocated to:

```text
new map descriptor = 0x300000
new LZBeam stream  = 0x300010
```

Exactly one decoded tile word changes:

```text
(x=0,y=0): 0x00CD → 0x0001
```

The rebuilt map remains `18×40`; post-build decoding proves exactly one differing 16-bit map word.

Encoded map size in the audited build: **266 bytes**.

## Transaction 2 — persistent placement stream

A known `health_pickup` (`type_id 54`) is inserted at:

```text
x      = 128
y      = 120
stride = 6
flags  = 0x7800
```

Retail scene 18 starts as:

```text
40 placements
stride runs = 8×40
```

After insertion and Y-sort:

```text
41 placements
stride runs = 8×2 / 6×1 / 8×38
```

The descriptor and LZBeam stream are relocated to:

```text
new object descriptor = 0x310000
new object LZ stream  = 0x310020
```

The generated scene reparses through the normal object-stream codec and the inserted health pickup is recovered at the requested coordinates.

Encoded object stream size: **229 bytes**.

## Transaction 3 — new world collision

Scene 18 has no retail world records, so M11A creates one from scratch through the M10F manifest layer:

```text
record offset = 0x0200
world_type    = 9
rect          = (64,64) .. (80,256)
```

New world resource base:

```text
0x320000
```

Its broadphase grid changes exactly three cells:

```text
(1,1)
(1,2)
(1,3)
```

All three cells share the same one-record membership tuple, so the deduplicated list pool is only **2 bytes**.

The authored record bytes are:

```text
0009 0040 0040 0050 0100
```

## Scene-record containment — CONFIRMED

Inside the 46-byte scene record, M11A permits changes only to the resource-pointer fields required by this transaction:

```text
+0x0A object-stream descriptor pointer
+0x0E world-collision pointer
+0x1A C000 map-descriptor pointer
```

Post-build comparison asserts that no other scene-record byte changes.

The original retail map descriptor, placement descriptor/stream and world resource remain untouched.

## Audited build

Build tool:

`tools/build/m11a_unified_scene_transaction.py`

Metadata:

`extracted_metadata/m11a_unified_scene_transaction.json`

Audited output:

```text
ROM size      4,194,304 bytes
checksum      0x39F4
output SHA-1  c16829235a57d9e88cfe51936b2b4b04f7188f49
```

The generated ROM is not committed.

## What M11A proves

The project can now execute this static authoring chain as one coherent scene transaction:

```text
canonical scene
├─ map decode → tile edit → LZBeam encode → new map descriptor
├─ placement decode → semantic insert → stride-run rebuild → LZBeam encode
└─ world manifest → new rectangle → broadphase/list compilation
        ↓
expanded ROM allocations
        ↓
three scene-pointer patches
        ↓
checksum repair
        ↓
post-build reparse of all edited domains
```

This is the first proof that the previously independent map, object and collision authoring systems can be composed without overwriting each other's state.

## Boundary

M11A is a proof builder with fixed safe allocations and one controlled scene. It is not yet the final production scene compiler.

The next step is M11B: replace proof-specific constants with one declarative scene source plus allocator, support arbitrary scene selection and both gameplay planes, and emit a build manifest describing every relocation and semantic edit.
