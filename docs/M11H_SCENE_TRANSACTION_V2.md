# M0.11H — Transactional Scene Compiler v2

Status: **IMPLEMENTED / SYNTHETIC ALLOCATION LOGIC VALIDATED / CANONICAL EXECUTION PENDING**

M11H closes the architectural gap left deliberately open by M11G: palette data can now participate in the same top-level scene build as gameplay maps, persistent placements and world collision without using an independent fixed allocation that could overlap M11B resources.

## Input contract

M11H consumes:

```text
truerecall.scene_patch.v2
```

with:

```text
scene_index
scene_patch        # embedded truerecall.scene_patch.v1
palette_operation  # null or replace_palette
```

The compiler entrypoint is:

```text
tools/build/scene_compiler_v2.py
```

It also exposes `compile_source_v2(...)`, which accepts a complete `truerecall.scene_source.v2`, exports the canonical base source, diffs it through M11G and builds the resulting v2 patch.

## Canonical-base gate

M11H verifies the immutable base before every build, including semantic no-ops:

```text
size   2,097,152 bytes
SHA-1  d39174bed46ede85531b86df7ba49123ce2f8411
```

This check was added explicitly after review found that an early no-op return could otherwise bypass the canonical ROM gate.

## Transaction strategy

M11B remains authoritative for existing scene-resource compilation.

M11H performs:

```text
canonical 2 MiB ROM
→ M11B embedded scene_patch.v1
→ M11B expanded-ROM allocation ledger
→ choose next aligned free address
→ write authored 128-byte palette
→ patch both scene palette pointers
→ audit combined scene-record containment
→ audit allocation non-overlap
→ repair final Genesis checksum
```

The palette is not assigned a blind fixed address once other resources exist. Its address is derived from the highest end address in the M11B allocation report and aligned to `0x10`.

This keeps M11B as the allocator for maps/objects/world while M11H safely extends its ledger.

## Palette integrity

For `replace_palette`, M11H requires:

- canonical retail `palette_0 == palette_1`;
- operation `retail_pointer` equals the canonical pointer;
- exactly 64 valid Genesis CRAM words;
- declared `changed_indices` exactly match the actual retail→authored differences;
- at least one real color change.

After writing the new CRAM image, the compiler reparses all 64 words and both scene pointers.

## Scene-record containment

M11B reports the scene-record byte offsets changed by map/object/world compilation.

M11H forms the allowed union:

```text
M11B changed offsets
+ palette pointer fields +0x02..+0x09 when palette changes
```

The final authored 0x2E-byte scene record is compared directly against retail. Any changed byte outside that union fails the build.

## Allocation containment

The final report carries one allocation ledger containing both M11B resources and the M11H palette allocation.

After sorting by address, every adjacent pair must satisfy:

```text
left.address + left.size <= right.address
```

Any overlap is a hard assertion failure.

## Checksum ownership

M11B repairs a checksum at the end of its stage. M11H may subsequently add palette data and pointers, so the v2 transaction zeros and recomputes the checksum after all v2 edits.

The checksum in the M11H report is therefore the authoritative final checksum for the combined build. The nested M11B checksum describes only the intermediate scene stage.

## Synthetic transaction test

`tests/test_scene_compiler_v2_static.py` defines four cases:

1. exact no-op after base validation;
2. wrong base rejected even for no-op;
3. forged/mismatched palette `changed_indices` rejected;
4. combined C000 map edit + palette edit in one build.

The combined fixture creates a minimal 2 MiB scene with:

```text
scene record   0x001000
retail palette 0x002000
map descriptor 0x003000
map LZBeam     0x004000
```

The real LZBeam encoder is used for a two-word C000 map fixture.

The expected transaction properties are:

- M11B changes exactly one map word;
- ROM expands to 4 MiB;
- palette has exactly one changed color;
- map and palette reparsing reproduce authored values;
- all allocations are non-overlapping;
- `scene_palette` is allocated after M11B resources;
- final scene changes stay within map pointer + palette pointer fields;
- stored Genesis checksum equals a fresh recomputation;
- reported SHA-1 equals the generated ROM.

In an equivalent allocation-ledger harness, a representative M11B ledger occupying `0x300000..0x30001B` placed the 128-byte palette at `0x300020`, with both palette pointers and the final checksum validating. This is synthetic evidence only, not canonical-ROM confirmation.

## Canonical probe

`tools/rom_probe/scene_source_v2_transaction_probe.py` is the canonical M11H gate.

Against scene 18 it will prove:

```text
scene_source.v2 exact no-op
+
one authored C000 tile
+
one authored palette color
→ one 4 MiB transaction
```

The probe reparses the relocated C000 map, relocated palette, both palette pointers, allocation ledger and final checksum.

No expected output SHA-1 is hard-coded before the first successful canonical execution; that fingerprint will become evidence only after the SHA-1-locked probe runs.

## Current limitation

The current chat runtime still cannot materialize the Library copy of `True Lies (World)` as raw bytes. Therefore M11H is not canonical-confirmed and has no runtime claim.

## Completion criteria

M11H is complete only when:

1. static/synthetic tests execute cleanly;
2. canonical v2 source no-op returns the exact retail ROM;
3. canonical scene-18 map + palette transaction succeeds;
4. map and palette both reparse to authored values;
5. combined allocations are non-overlapping;
6. scene-record containment passes;
7. final checksum passes;
8. `extracted_metadata/m11h_scene_source_v2_transaction.json` is generated from that execution;
9. BlastEm visually confirms the authored palette and preserves unrelated gameplay behavior.
