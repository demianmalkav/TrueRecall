# M1.1B — Gameplay graphics authoring and runtime proof

Status: **COMPLETE / CONFIRMED for the scene0 primary gameplay graphics resource**.

This milestone establishes a reproducible authoring boundary for the primary Genesis tile resource used by scene0 and proves one authored environment tile reaches actual VDP VRAM and presentation without regressing the closed player, object, collision or palette gates.

## Authority and scope

Canonical base:

- True Lies (World), 2,097,152 bytes
- SHA-1 `d39174bed46ede85531b86df7ba49123ce2f8411`

Closed logical parent for environment/palette comparison:

- M110A SHA-1 `270e1d633db7883c9170bb1e4eb367abdf97a2bd`
- checksum `0x6B9E`

Frozen gameplay parent for behavioral regression:

- M09D SHA-1 `49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021`

The result does **not** claim complete semantics for every graphics pointer in every scene. It confirms the primary scene0 resource and preserves unresolved secondary/auxiliary identity unchanged.

## Primary graphics descriptor — CONFIRMED authoring boundary

For a scene with a non-zero primary graphics descriptor, the descriptor is treated as three 32-bit values:

```text
+0x00  primary LZBeam graphics pointer
+0x04  secondary pointer
+0x08  auxiliary pointer
```

For scene0:

```text
retail descriptor:    0x00FFAA
primary LZBeam:       0x014898
secondary pointer:    0x800178DA
auxiliary pointer:    0x01BF7A
secondary-plane desc: 0x00000000
```

`tools/build/scene_graphics.py` deliberately authors only the primary LZBeam payload. Secondary and auxiliary pointer identity remain byte-for-byte preserved until independently reconstructed.

Decoded primary payload:

```text
bytes:        24,960
tile size:    32 bytes
tile count:   780
decoded SHA256: 0f73aff41d28f9cae5b17368f78979f720474ce342c85e53f9a46174e3bbb171
```

Map-reference validation confirms scene0 C000/E000 tile indices remain inside that 780-tile set.

## Exact no-op gate — CONFIRMED

Canonical export followed by unedited compile returns the original ROM exactly.

A forced relocation also decodes back to the exact same 24,960 bytes:

```text
new descriptor: 0x304000
new primary LZ:  0x304010
encoded bytes:   12,084
output SHA-1:    b61ae28d9ead8928f4dbe94f2ecd7eaa057e90d5
checksum:        0xF6E0
```

Evidence: `extracted_metadata/m111b_scene_graphics_primary.json`.

## Authored environment tile — CONFIRMED

The production proof modifies only primary tile index `2`.

Retail tile 2 fingerprint:

```text
SHA256 e0e77a507412b120f6ede61f62295b1a7b2ff19d3dcc8f7253e51663470c888e
```

Authored tile 2 is an 8x8 diagnostic X using palette index `0xE`:

```text
e000000e
0e0000e0
00e00e00
000ee000
000ee000
00e00e00
0e0000e0
e000000e
```

E000 references tile 2 repeatedly; C000 does not. This provides a visible environment-only diagnostic target rather than modifying Quaid or HUD graphics.

Scene-only graphics parent:

```text
SHA-1:    a26f74937233e155e025bcd45a220660c75e110f
checksum: 0xED13
changed primary tiles: [2]
```

## Integrated scene0 candidate — CONFIRMED build

Builder: `tools/build/m111c_graphics_vertical_slice.py`.

The builder reconstructs the closed M110A parent, authors tile 2 through `scene_graphics.py`, verifies allocation non-overlap, then composes the scene graphics delta with M110A using the existing conflict-detecting compositor.

Combined expanded-ROM ledger:

```text
0x300000  object_desc                  132
0x300090  object_lz                  1217
0x300600  world_resource            10880
0x303080  scene_palette               128
0x304000  primary_graphics_descriptor  12
0x304010  primary_graphics_lz       12105
```

All allocations are non-overlapping. The six frozen Quaid phase banks and the M110A palette bytes are preserved.

Integrated candidate:

```text
SHA-1:    b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0
checksum: 0xFAD7
size:     4 MiB
```

The CI-published builder snapshot rebuilt this candidate byte-for-byte.

Evidence: `extracted_metadata/m111c_graphics_vertical_slice.json`.

## Actual VDP VRAM + presentation proof — CONFIRMED

Runner: `tools/runtime/m111d_graphics_runtime.py`.

Correct logical comparison: M110A parent vs M1.1B candidate under the same deterministic scene0 navigation.

Observed actual VDP state:

```text
VRAM changed range: [0x0040, 0x0060)
changed bytes:      32
```

That range is exactly tile index 2 (`2 * 32` bytes). Parent VRAM contains the fingerprinted retail tile; candidate VRAM contains the authored X bytes exactly.

CRAM is identical between M110A and M1.1B, proving this graphics gate does not perturb the already-closed palette state.

BlastEm internal screenshots at the same deterministic scene0 stage:

```text
size:            256x240
changed pixels:  1440
change bbox:     [15, 9, 199, 45]
```

The visual delta is confined to the upper environment region targeted by the repeated E000 tile. This is runtime presentation evidence, not only ROM or decoded-resource evidence.

Evidence: `extracted_metadata/m111d_graphics_runtime.json`.

## Closed-gate regression — CONFIRMED

Runner: `tools/runtime/m111e_graphics_regression.py`.

Against the frozen M09D gameplay parent:

- M100B behavioral/control suite: **14/14 PASS**;
- authored world wall behavior remains correct;
- shotgun pickup behavior remains candidate-only as expected;
- canonical player/proxy semantics remain preserved.

M110B palette regression remains exact:

```text
CRAM difference count: 1
index:  8
parent: 0x0464
candidate: 0x0648
player palette line 32..47: exact
```

Thus M1.1B does not reopen M09D, M1.0 or M1.1A.

Evidence: `extracted_metadata/m111e_graphics_regression.json`.

## CI checkpoint

The verified source snapshot used for final reproduction:

```text
commit:          79c1e485441f92b536baa00d5401caa5c24076f8
Actions run:     38073075203
artifact id:     11677736118
artifact SHA256: be0b0a2cdc1016f33cb9828b7c970fc50f9898d7dea3e79d77564b38ff862c58
static:          PASS
BlastEm harness: PASS
```

The artifact-published M111C builder rebuilt the pinned candidate exactly; artifact-published M111D and M111E then reproduced the runtime evidence above.

## Remaining limitation / next architectural consequence

Primary gameplay graphics are now sufficiently recovered to enter canonical source-level scene authoring. They are **not yet represented inside the versioned `scene_source` schema/transaction**; M111C currently composes the independently built graphics resource with M110A after proving allocation non-overlap.

The next stabilization step should therefore migrate the confirmed primary-graphics model into a new versioned scene-source transaction while keeping `scene_source.v1` and v2 regression anchors unchanged. This follows the existing project rule that source schemas evolve only after the underlying graphics semantics are recovered.
