# M0.10 — World Collision Authoring

M0.10 turns the recovered world spatial/collision resource into a writable level layer. It follows the same progression already proven for visual tilemaps and persistent placements: first prove safe relocation with no semantic change, then introduce controlled edits.

## M10A — byte-identical resource relocation — RUNTIME CONFIRMED

Scene 0 stores its world spatial resource pointer at:

```text
scene record  = 0x013B9A
field         = scene+0x0E
retail base   = 0x07A42E
```

For the relocation proof, TrueRecall copies the complete retail byte interval from the scene-0 resource base up to the next world-resource base:

```text
0x07A42E .. 0x07C7EB
length = 0x23BE = 9,150 bytes
```

The copied bytes are placed in expanded-ROM space at:

```text
0x230000
```

Only `scene+0x0E` is redirected. The original resource remains untouched.

Build tool:

`tools/build/m10a_world_collision_relocation.py`

Audited build:

```text
base SHA-1   d39174bed46ede85531b86df7ba49123ce2f8411
output SHA-1 38f586b8478487a1662326054764bbe6f3631ce7
ROM size     4,194,304 bytes
checksum     0x16C5
```

### Static validation

The build asserts canonical input ROM identity, expected scene/resource boundaries, pristine expanded-ROM target space, byte-identical relocation, pointer redirection and a regenerated Genesis checksum.

### Runtime validation

A deterministic BlastEm run compares retail and M10A at the same scene-0 gameplay path. Thirteen screenshots at frames `2098..2144` are pixel-identical (`0` different pixels at every sampled frame).

Persisted result:

`extracted_metadata/m10a_world_collision_runtime.json`

This proves that `scene+0x0E` is a safe relocation seam for the world spatial resource and that expanded-ROM addressing works for this layer at runtime.

## Axis normalization — CONFIRMED

The ten-byte world-record base structure is editor-facing:

```text
+0x00 word world_type
+0x02 word x_min
+0x04 word y_min
+0x06 word x_max
+0x08 word y_max
```

The values are world-pixel coordinates and align with the plane-E nominal world extents.

## Important index-authoring constraint

The dense 64×64 broadphase grid is **not** simply a mechanical rasterization of each record bounding box. Most retail record memberships form rectangular cell regions, but overlap/priority cases are deliberately pruned. Retail uses at most one record reference per cell even though the engine supports multi-entry lists.

Therefore TrueRecall must not regenerate the complete retail grid from rectangle overlap alone until that priority/partition policy is recovered or replaced by a runtime-validated authoring policy.

This remains a failure-containment rule: record geometry and type editing are authorable, but full grid/list regeneration is not yet authorized.

## M10B — targeted material/type edits — RUNTIME CONFIRMED

M10B isolates the behavioral meaning of the world-type dispatch without changing geometry or grid membership. Both builds use the exact M10A 4 MiB relocation and alter one existing scene-0 world record.

Build tool:

`tools/build/m10b_targeted_collision.py`

Persisted runtime measurements:

`extracted_metadata/m10b_targeted_collision_runtime.json`

### M10B-P — player pass-through record

Exact record:

```text
resource-relative offset  0x1C46
expanded-ROM address      0x231C46
geometry                  (736,544) .. (752,800)
world type                9 -> 11
```

Dispatch semantics are independently known:

```text
type 9  player -> 0x002E18 standard collision
 type11 player -> 0x002E16 RTS / no response
```

Audited build:

```text
output SHA-1 80d9f2fc07d222af5d68f078de15271d27c8d66a
checksum     0x16C7
```

Compared byte-for-byte against M10A, the entire 4 MiB ROM differs at only two byte positions:

```text
0x00018F  checksum low byte
0x231C47  world_type low byte: 0x09 -> 0x0B
```

Runtime test: hold Left from frame 2100 through 2280. M10A keeps Harry blocked by the record; the M10B-P build allows him to cross and finish on the west side. A single `type 9 -> 11` edit therefore disables player collision for that existing geometry at runtime.

### M10B-R — projectile pass-through record

Exact record:

```text
resource-relative offset  0x1C6E
expanded-ROM address      0x231C6E
geometry                  (464,496) .. (784,544)
world type                9 -> 10
```

Dispatch semantics:

```text
type 9  player     -> standard collision
 type9  projectile -> standard collision
 type10 player     -> standard collision
 type10 projectile -> 0x002E16 RTS / no response
```

Audited build:

```text
output SHA-1 b64de77121fc80fd6e4c3389f27d26bfb0843b58
checksum     0x16C6
```

Again, compared against M10A, only two bytes differ:

```text
0x00018F  checksum low byte
0x231C6F  world_type low byte: 0x09 -> 0x0A
```

Runtime test: briefly face north, then fire B. At frame 2130 baseline and patch are pixel-identical; from frame 2134 onward the impact/projectile presentation diverges exactly where expected, with the retail impact flash absent/changed in the type-10 build. The player dispatch remains the standard collision path for type 10.

### What M10B proves

M10B establishes a production-grade authoring seam:

```text
existing world geometry
+ unchanged broadphase membership
+ authored world_type
= independently selectable player/projectile collision behavior
```

This is stronger than the old global walk/shoot-through-walls cheats: the behavior can be assigned to one specific world rectangle without disabling collision globally.

## Current M0.10 boundary

Confirmed authorable now:

- relocate an existing world resource;
- edit a record's behavior type;
- preserve its geometry and current broadphase membership;
- produce player-blocking/projectile-pass-through material behavior;
- produce player-pass-through behavior for a selected record;
- validate the semantic result at runtime.

Still unresolved before arbitrary collision-shape authoring:

1. recover or replace the retail broadphase priority/partition policy;
2. prove geometry edits that cross cell boundaries;
3. generate cell reference lists and dense-grid entries safely;
4. classify special world types that carry semantics beyond simple block/no-op dispatch;
5. integrate world-material records into the declarative scene compiler.

The next high-value M0.10 step is therefore **grid/list regeneration**, not further single-record type mutation.
