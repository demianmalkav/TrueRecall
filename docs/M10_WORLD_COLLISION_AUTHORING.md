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

## Static validation

The build asserts:

- canonical input ROM size/hash;
- expected scene-0 record and resource address;
- expected next resource boundary;
- target expanded-ROM range is pristine `0xFF`;
- all 9,150 copied bytes are byte-identical;
- the scene pointer resolves to `0x230000`;
- Genesis checksum is regenerated.

## Runtime validation

A deterministic BlastEm run compares retail and M10A at the same scene-0 gameplay path. Thirteen screenshots were taken at frames:

```text
2098, 2102, 2106, 2110, 2114, 2118, 2122,
2126, 2130, 2134, 2138, 2140, 2144
```

Every screenshot is pixel-identical:

```text
different pixels = 0 / frame
13 of 13 frames identical
```

Persisted result:

`extracted_metadata/m10a_world_collision_runtime.json`

This proves that `scene+0x0E` is a safe relocation seam for the world spatial resource and that expanded-ROM addressing works for this layer at runtime.

## Axis normalization — CONFIRMED

The ten-byte world-record base structure can now be named editor-facing as:

```text
+0x00 word world_type
+0x02 word x_min
+0x04 word y_min
+0x06 word x_max
+0x08 word y_max
```

The values are in world-pixel coordinates and align with the plane-E nominal world extents.

## Important index-authoring constraint

The dense 64×64 broadphase grid is **not** simply a mechanical rasterization of each record bounding box. Most retail record memberships form rectangular cell regions, but overlap/priority cases are deliberately pruned. Retail uses at most one record reference per cell even though the engine supports multi-entry lists.

Therefore TrueRecall must not regenerate the complete retail grid from rectangle overlap alone until that priority/partition policy is recovered or replaced by a runtime-validated authoring policy.

This is a deliberate failure-containment rule: record geometry is understood, but the original grid-authoring priority semantics are not yet claimed.

## M10B target

The next proof changes one world record while preserving its existing grid membership. Preferred isolation edit:

```text
world_type 9 -> 10
```

Both types use normal player collision, while projectiles differ:

- type 9: normal projectile collision
- type 10: projectile no-op/pass-through

That makes it possible to prove a new material/behavior property without changing player locomotion or spatial indexing.

After type editing is runtime validated, geometry edits that stay within the existing cell assignment can be tested separately. Full grid/list regeneration remains a later M0.10 sub-milestone.
