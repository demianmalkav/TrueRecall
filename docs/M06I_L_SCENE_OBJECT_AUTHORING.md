# M0.6I–L — Scene Object Authoring Proofs

These static laboratory builds close the inverse authoring path for the persistent scene-object stream. They build on the recovered placement format, LZBeam encoder and scene descriptor layout.

They remain **runtime-unvalidated** until executed in a Genesis emulator or hardware.

## M0.6I — in-place semantic replacement

Target: scene 0, placement index 2.

Retail anchor:

```text
type_id = 68  (shotgun ammo pickup)
x = 240
y = 75
stride = 6
status flags = 0x7800
```

M0.6I changes only the low 10-bit type field:

```text
68 shotgun ammo -> 54 health pickup
```

The decoded object stream differs at exactly one 16-bit word. X/Y, flags, stride layout and all other placements remain unchanged. The edited stream is re-encoded, relocated and re-pointed.

Audited output:

```text
checksum = 0xE005
SHA-1   = b1754bb986e3450456a30c17a54a3ccb4633783b
```

Regression tool: `tools/build/m06i_object_placement_edit.py`.

## M0.6J — append a new placement

Target: scene 1.

Retail scene 1 contains 72 six-byte placements in a single descriptor run:

```text
(6,72)
```

M0.6J adds a new health pickup:

```text
type_id = 54
x = 256
y = 7984
status_flags = 0x7800
stride = 6
```

The compiler expands the decoded object stream from `0x1C0` to `0x1C6`, increments placement count `72 -> 73`, updates the existing run to `(6,73)`, relocates/re-encodes the LZBeam stream and repairs the checksum.

Audited output:

```text
checksum = 0x98F8
SHA-1   = de11dbcec3517d754fcadb253e45348b6362a318
```

Regression tool: `tools/build/m06j_object_placement_insert.py`.

## M0.6K — descriptor regeneration / mixed stride

M0.6K proves that authoring is not limited to preserving the retail run structure.

Scene 1 receives one 8-byte placement:

```text
type_id = 123
x = 256
y = 8000
param = 0
status_flags = 0x7800
stride = 8
```

The retail descriptor:

```text
placements = 72
runs = [(6,72)]
```

is rebuilt as:

```text
placements = 73
runs = [(6,72),(8,1)]
```

Because the descriptor grows, both the descriptor and compressed object stream are relocated into verified FF padding and the scene record's descriptor pointer is patched.

Audited output:

```text
checksum = 0xBC10
SHA-1   = db2031b93c987cb77ca5b3dc67e9d4e0cbe81327
```

Regression tool: `tools/build/m06k_relocated_descriptor_mixed_stride.py`.

## M0.6L — declarative scene-object compiler

The individual proofs were then generalized into:

```text
tools/build/scene_object_compiler.py
```

Input is a JSON manifest with schema:

```text
truerecall.scene_object_patch.v1
```

Supported operations:

- `replace` an existing placement by stable retail `base_index`;
- `remove` an existing placement;
- `add` a 6-byte placement;
- `add` an 8-byte placement with instance parameter.

The compiler:

1. verifies the canonical base ROM;
2. parses the selected scene object stream;
3. applies semantic operations;
4. stable-sorts placements by Y as required by the retail stream;
5. rebuilds 6/8-byte records;
6. regenerates stride runs;
7. rebuilds the descriptor;
8. LZBeam-encodes the stream;
9. allocates descriptor + resource in verified FF space;
10. patches the scene descriptor pointer;
11. repairs the Genesis checksum;
12. reparses the generated ROM and compares every placement structurally against the intended source model.

The compound example `tools/build/examples/scene1_compound.json` performs all four edit modes in one build:

```text
replace placement 4 -> type 54
remove placement 5
add type 54 / stride 6
add type 123 / stride 8 / param 0
```

Result:

```text
base placements = 72
new placements  = 73
runs             = [(6,72),(8,1)]
decoded bytes    = 456
encoded bytes    = 391
checksum         = 0x272B
SHA-1            = 19db3bb96b8462f282ebbb48472cfee3a0c680ac
```

## What this proves

The project now has a reproducible static authoring path for scene entities:

```text
semantic placement manifest
→ retail scene/object parse
→ replace / remove / add
→ regenerated mixed-stride stream
→ regenerated descriptor
→ LZBeam encoding
→ safe ROM relocation
→ scene-pointer patch
→ checksum repair
→ full structural reparse/verification
```

This is materially different from manual ROM hacking. The persistent object layer can now be treated as source data.

## Remaining gate

Runtime validation is still required before these tools are promoted from statically proven authoring to runtime-complete production tooling. No generated ROM is committed to the repository.
