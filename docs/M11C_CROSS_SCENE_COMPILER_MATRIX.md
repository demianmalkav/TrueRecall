# M0.11C — Cross-Scene Unified Compiler Matrix

M11C broadens the M11B reusable scene compiler beyond a single fixture. Four canonical regression cases exercise different structural edge cases of the retail scene format through the same `tools/build/scene_compiler.py` implementation.

Probe:

`tools/rom_probe/unified_scene_matrix_probe.py`

Metadata:

`extracted_metadata/m11c_unified_scene_matrix.json`

Runtime validation is pending in the current container.

## Case 1 — scene 18 / full three-domain transaction

Purpose: prove simultaneous map + placement + world authoring, including creation of collision geometry in a retail-empty world layer.

```text
scene                 18
C000 dimensions       18×40
map edits             1 word
objects               40 → 41
stride runs           8×2 / 6×1 / 8×38
world records         0 → 1
world payload source  next_world_base
output SHA-1          fac81fdc87b76a75c9b590d58707b16fcd6a5f04
checksum              0x3E9A
```

This is the allocator-driven equivalent of the earlier M11A hardcoded transaction proof.

## Case 2 — scene 5 / unequal C000 and E000 dimensions

Purpose: prove both plane blocks can be compiled independently when their dimensions differ.

Retail geometry:

```text
C000  104×48
E000   80×48
```

M11C changes exactly one word in each plane and allocates two independent map descriptors + LZBeam streams.

```text
output SHA-1  b11173030e8a587e2e7d4633f8aba0e65d0116b9
checksum      0x8EF4
```

This guards against the incorrect assumption that the two gameplay planes always share dimensions.

## Case 3 — scene 0 / highly mixed placement stream

Purpose: stress object-descriptor regeneration without changing placement count.

Scene 0 has 168 placements and **61 stride runs** alternating between six- and eight-byte records. M11C performs a single coordinate replacement on base placement 0 and rebuilds the full descriptor/stream.

```text
placements    168 → 168
stride runs   61
output SHA-1  c57a73e8f6ea8967a3f45b9d40b200ba8f9404c9
checksum      0x575A
```

This proves the unified compiler is not limited to simple single-stride scenes.

## Case 4 — scene 6 / factorized broadphase dimensions

Purpose: exercise the one retail world-collision scene whose broadphase dimensions cannot be derived directly from the gameplay-map dimensions.

Recovered world layout:

```text
grid                  26×55
world records         375
payload bytes         0x2958
payload boundary      next_world_base
```

The regression changes `retail_000` material type from 9 to 11 and recompiles the full dense grid + remote deduplicated list pool through the same scene compiler.

```text
remote pool bytes  2746
output SHA-1       f0c146a285a7c065045179f6ea22d93d3c91ab4e
checksum           0xA53C
```

This proves the compiler respects the scene-6 dimension exception already recovered by the all-scene world-collision probe.

## What M11C establishes

The unified scene compiler now has deterministic static coverage for:

```text
both gameplay planes
unequal plane dimensions
simple and highly mixed placement streams
empty and non-empty world layers
normal and factorized broadphase dimensions
semantic add and replace operations
expanded-ROM allocation
scene-record containment
post-build structural reparsing
```

The remaining gap is not binary-format understanding. It is turning a patch-oriented manifest into a fuller source representation that can be exported, edited and rebuilt as a coherent scene asset.

## Next gate — M11D

Create a canonical scene-source exporter that emits one editable representation containing:

- scene metadata and palette references;
- both plane dimensions and tile-word data or external source references;
- all persistent placements with stable source IDs;
- all world records with stable IDs;
- explicit preservation policy for unresolved/opaque scene fields.

Then require export→rebuild semantic equivalence on representative scenes before permitting large original Total Recall level construction.
