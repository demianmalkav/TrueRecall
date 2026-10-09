# M0.10 — World Collision Authoring

M0.10 turns the recovered world spatial/collision resource into a writable level layer. It follows the same progression already proven for maps and persistent placements: relocation, material/type edits, broadphase reconstruction, geometry edits, then new authored records.

## M10A — byte-identical resource relocation — RUNTIME CONFIRMED

Scene 0 stores its world spatial resource pointer at `scene+0x0E`.

```text
scene record  0x013B9A
retail base   0x07A42E
next base     0x07C7EC
length        0x23BE = 9,150 bytes
relocated to  0x230000
```

Build tool: `tools/build/m10a_world_collision_relocation.py`.

Audited build:

```text
output SHA-1 38f586b8478487a1662326054764bbe6f3631ce7
ROM size     4,194,304
checksum     0x16C5
```

A deterministic BlastEm run compared retail and M10A at the same scene-0 path. Thirteen screenshots at frames `2098..2144` were pixel-identical. This proves `scene+0x0E` is a safe runtime relocation seam.

## World record layout — CONFIRMED

Each base record is ten bytes:

```text
+0x00 word world_type
+0x02 word x_min
+0x04 word y_min
+0x06 word x_max
+0x08 word y_max
```

Coordinates are world pixels and are interpreted as half-open rectangles for broadphase membership.

## M10B — targeted material/type edits — RUNTIME CONFIRMED

M10B changes one existing world record while preserving its geometry and broadphase membership.

Build tool: `tools/build/m10b_targeted_collision.py`.

### M10B-P — player pass-through

```text
record offset 0x1C46
geometry      (736,544) .. (752,800)
type          9 -> 11
build SHA-1   80d9f2fc07d222af5d68f078de15271d27c8d66a
```

Holding Left in the deterministic scene-0 path leaves Harry blocked in M10A and lets him cross in M10B-P.

### M10B-R — projectile pass-through

```text
record offset 0x1C6E
geometry      (464,496) .. (784,544)
type          9 -> 10
build SHA-1   b64de77121fc80fd6e4c3389f27d26bfb0843b58
```

The projectile path diverges only after firing/impact while player collision remains standard.

M10B proves local material behavior is independently authorable per world record.

## M10C — broadphase/list serializer — STATIC CONFIRMED / RUNTIME PENDING

The earlier hypothesis that scene 0 used a hidden overlap-priority policy was incorrect. The complete index format is now recovered exactly.

### Resource prefix

```text
0x0000..0x09B3  54×23 grid of 16-bit list pointers
0x09B4..0x1059  deduplicated list pool
0x105A          0xFFFF sentinel
0x105C..0x1F01  375 ten-byte world records
```

The grid contains 1242 cells. Each cell represents a 64×64-pixel world region. This matches the 107×45 scene-0 world-metatile extent grouped as 2×2 metatiles:

```text
ceil(107/2) × ceil(45/2) = 54 × 23
```

### List encoding

Every non-zero grid entry points to the first word of a cell list.

- bit15 on the first reference marks a list start;
- low 15 bits are a resource-relative world-record offset;
- continuation references have bit15 clear;
- the next bit15-marked word begins the next unique list;
- cells may share list pointers.

Retail scene 0 contains:

```text
985 non-empty cells
373 unique non-zero list pointers
373 bit15 list starts
851 list words
list length 1..8 records
1702 list-pool bytes
```

All 851 references resolve to the 375 records.

### Exact membership rule

For all 1242 cells, the retail membership list is exactly the set of records satisfying:

```text
record.x_min < cell.x_max
record.x_max > cell.x_min
record.y_min < cell.y_max
record.y_max > cell.y_min
```

Lists are ordered by record offset descending. Unique membership tuples are emitted on first encounter while scanning cells row-major; repeated tuples reuse the first list pointer.

`tools/build/world_collision_codec.py` reproduces both the retail grid and the complete 1702-byte list pool byte-for-byte.

### M10C geometry edit proof

Target:

```text
record offset   0x1C46
world_type      9
before          (736,544) .. (752,800)
after           (800,544) .. (816,800)
```

The wall is moved exactly 64 pixels east. Five old cells lose the record and five new cells gain it, for ten changed membership tuples total:

```text
(11,8)  <-> (12,8)
(11,9)  <-> (12,9)
(11,10) <-> (12,10)
(11,11) <-> (12,11)
(11,12) <-> (12,12)
```

The regenerated pool is 1698 bytes, fitting inside the existing fixed pool region while preserving the record table at `0x105C`.

Audited static build:

```text
output SHA-1 5bf78090cbc54acbed1bc70211666f5f1d1645bf
ROM size     4,194,304
checksum     0xDAE9
resource     0x230000
```

Tool/evidence:

```text
tools/build/world_collision_codec.py
tools/build/m10c_broadphase_geometry.py
extracted_metadata/m10c_broadphase_geometry.json
docs/M10C_BROADPHASE_SERIALIZER.md
```

The build reparses the authored record table and regenerates the index again to prove self-consistency.

Runtime validation is still required before M10C is marked complete because the current execution container no longer has the debug BlastEm binary used by M0.7–M0.10B.

## Current M0.10 boundary

Confirmed and runtime-authorized:

- relocate a world resource;
- edit an existing record's `world_type`;
- select local player/projectile collision behavior.

Statically authorable with an exact recovered serializer:

- regenerate scene-0 64×64 broadphase cell membership;
- move existing rectangle geometry across broadphase cells;
- deduplicate and encode multi-record cell lists.

Remaining gates:

1. runtime-validate the M10C cross-cell geometry edit;
2. generalize layout discovery/serialization to all 19 scenes;
3. add new world records rather than only moving existing ones;
4. integrate typed world rectangles into the declarative scene compiler;
5. classify special world types only where they advance Total Recall mechanics.

The next immediate M0.10 step is the runtime validation of the `0x1C46` east-shift build. Once that passes, arbitrary existing-record geometry becomes production-authorized.
