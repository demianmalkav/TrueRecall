# M0.11D — Canonical Scene Source

M11D changes the authoring abstraction again: a designer/tool no longer has to write patch operations directly.

`tools/build/scene_source.py` exports a retail scene into one editable source representation, diffs an edited source against the canonical export and automatically produces the `truerecall.scene_patch.v1` operations consumed by M11B.

Retail-derived exported source files are local working artifacts and are **not committed**.

Probe:

`tools/rom_probe/scene_source_probe.py`

Metadata/fingerprints:

`extracted_metadata/m11d_scene_source.json`

## Source schema

`truerecall.scene_source.v1`

The source contains:

```text
scene_index
immutable scene metadata
  scene_flags
  palette pointers
  collision resource mode
  primary plane-state RAM selector

planes
  C000
    graphics_descriptor
    width / height
    tile_words[]
  E000
    graphics_descriptor
    width / height
    tile_words[]

objects
  opaque prefix as hex
  records[]
    stable source id
    type_id
    status_flags
    stride
    x / y
    optional param

world
  broadphase dimensions
  records[]
    stable source id
    type
    rectangle
```

The broadphase grid/list pool itself is deliberately not source-authorable. It is derived output regenerated from the world rectangles by the M10 serializer.

Likewise, object stride runs are not source data. They are regenerated from the edited placement sequence.

## Stable source IDs

Retail placements export as:

```text
retail_0000
retail_0001
...
```

Retail world records retain the `retail_###` IDs already used by the M10 manifest layer.

New source records use author-chosen IDs. The differ converts them to `add` operations; deleting retail IDs becomes `remove`; field changes on retail IDs become `replace`.

This keeps binary offsets and placement indices out of normal scene editing.

## Immutable boundaries in v1

M11D refuses edits to fields that the current scene compiler does not yet rebuild safely:

- scene flags;
- palette pointer identity;
- collision resource mode;
- primary plane-state selector;
- plane graphics-descriptor identity;
- plane dimensions;
- object-stream opaque prefix;
- world broadphase dimensions.

These are explicit schema constraints rather than silent unsupported behavior.

## Exact no-op proof

Representative scenes 0, 5, 6 and 18 are exported and immediately compiled without edits.

M11D requires:

```text
source → diff = zero operations
compile_source(source) → exact original 2 MiB ROM bytes
```

All four pass.

Canonical source fingerprints:

| Scene | Canonical JSON bytes | C000 words | E000 words | Objects | World records |
|---:|---:|---:|---:|---:|---:|
| 0 | 62,331 | 4,815 | 4,815 | 168 | 375 |
| 5 | 51,584 | 4,992 | 3,840 | 139 | 314 |
| 6 | 72,949 | 7,810 | 5,720 | 206 | 375 |
| 18 | 8,186 | 720 | 720 | 40 | 0 |

The corresponding SHA-256 fingerprints are stored in the M11D metadata file instead of committing the retail-derived source JSON.

## Source-level authored edit proof

The scene-18 source is edited directly:

1. C000 `tile_words[0] = 0x0001`;
2. append source object `new_health_0`, type 54, at `(128,120)`, stride 6;
3. append world record `new_wall_0`, type 9, rectangle `(64,64)..(80,256)`.

No patch operations are manually written.

The differ generates exactly:

```text
map:    set_tile C000 (0,0) = 0x0001
object: add type 54 @ (128,120), stride 6
world:  add new_wall_0 type 9 rect (64,64)..(80,256)
```

Compiling that source produces the exact M11B audited build:

```text
output SHA-1  fac81fdc87b76a75c9b590d58707b16fcd6a5f04
checksum      0x3E9A
```

Therefore:

```text
editable scene source
→ semantic diff
→ unified scene patch
→ expanded-ROM compiler
```

is deterministic.

## Production consequence

This is the first point where a future editor, agent or human author can work on a scene as scene data rather than as a ROM patch.

The binary layers are now compiler output:

```text
LZBeam map streams
object stride runs / descriptor
world broadphase grid / list pool
resource relocation addresses
scene-record pointers
Genesis checksum
```

That separation is essential for Total Recall production: design changes should occur in scene sources, while the toolchain owns binary layout.

## Next gate

M11E should run canonical export/no-op verification across **all 19 scenes**, not only the four structural representatives, and add source-level edit cases for remove/replace as well as add.

After M11E, the main missing level-authoring layers will be graphics/tile-set source authoring, palette authoring, scripts/objectives and runtime regression of M10/M11 new geometry under the restored BlastEm harness.
