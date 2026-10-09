# M0.10F — Declarative World-Collision Manifest Authoring

M10F moves world-collision editing from scene-specific proof scripts to a production-facing declarative layer. It builds on the exact all-scene serializer recovered in M10C/E and on the new-record proof from M10D.

## Global format coverage — CONFIRMED

`tools/rom_probe/world_collision_all_scenes_probe.py` proves that all **19 retail scenes** round-trip their dense broadphase grid, deduplicated list pool and memberships exactly through `world_collision_codec.py`.

Eighteen scenes derive broadphase dimensions directly from gameplay map dimensions. Scene 6 is the one retail exception: its `26×55` broadphase layout is recovered by record-extent factorization. Scene 18 is a valid empty world layer with a `9×20` grid, zero list-pool bytes and zero retail records.

## Manifest model

`tools/build/world_collision_manifest.py` exposes a world layer as:

```text
scene
  grid [width,height]
  records[]
    id
    offset
    type
    rect [x_min,y_min,x_max,y_max]
```

The authoring layer supports three semantic operations:

```text
add
remove
replace
```

`replace` can alter material/type, rectangle geometry or both. `add` accepts a new resource-relative record offset so authored records can live outside preserved retail payloads, as already demonstrated by M10D.

Compilation regenerates:

- the dense 64×64-cell broadphase grid;
- the deduplicated membership-list pool;
- each ten-byte world record;
- exact resource-relative references.

## 19-scene no-op proof — CONFIRMED

`tools/rom_probe/world_collision_manifest_probe.py` exports each retail scene to the declarative model and recompiles it without edits.

For all 19 scenes it requires exact equality against retail for:

- dense grid bytes;
- list-pool bytes;
- semantic cell memberships.

Result:

```text
noop_roundtrip_scenes = 19
```

This proves that the manifest layer does not lose information required by the recovered world index.

## Empty-scene new-record proof — STATIC CONFIRMED

Scene 18 contains no retail world records. M10F therefore uses it as a clean test that does not depend on mutating or reusing an existing rectangle.

The manifest adds:

```text
id      authored_wall_0
offset  0x0200
type    9
rect    (64,64) .. (80,256)
```

Using a new list pool starting at `0x0180`, compilation changes exactly three 64×64 broadphase cells:

```text
(1,1)
(1,2)
(1,3)
```

Because each cell has the same one-record membership tuple, deduplication emits only one two-byte list entry and all three grid cells point to it.

The generated record bytes are exactly:

```text
0009 0040 0040 0050 0100
```

corresponding to `type=9`, `x_min=64`, `y_min=64`, `x_max=80`, `y_max=256`.

Metadata:

`extracted_metadata/m10f_world_manifest.json`

## What M10F proves

The project can now express world collision/material geometry as authoring data rather than ROM offsets:

```text
retail scene
→ export world manifest
→ semantic add/remove/replace operations
→ rectangle records
→ exact broadphase rasterization
→ list deduplication
→ binary grid/pool/records
```

This is the production-facing bridge required to integrate collision into a unified Total Recall scene compiler.

## Runtime boundary

The serializer itself is grounded by M10A/B runtime proofs and exact 19-scene retail reconstruction. The specific new scene-18 rectangle produced by M10F is **runtime-unvalidated** in the current environment, because the BlastEm executable used by earlier deterministic tests is not present in the current container.

M10D and M10F therefore remain static authoring proofs for genuinely new rectangles until the runtime harness is available again.

## Next step

Integrate world manifests with the existing scene-object compiler and gameplay-map authoring layer so a single scene source can define, at minimum:

```text
map layers
persistent object placements
world collision/material rectangles
```

That unified scene representation is the next architectural step toward authoring original Total Recall levels rather than isolated True Lies resource edits.
