# M0.11F — Gameplay Scene Palette Authoring

Status: **STATICALLY VALIDATED / CANONICAL EXECUTION PENDING**

M11F isolates gameplay-scene palette authoring from the M11D canonical scene-source schema so M11D fingerprints remain stable while palette editing is proven independently.

## Confirmed retail format

The master scene table is at `0x013B4A`, with 19 records of size `0x2E`.

For every retail scene:

```text
scene +0x02  long palette_0
scene +0x06  long palette_1
```

The two pointers are equal in all 19 canonical records and point to one raw 128-byte Genesis CRAM image:

```text
4 palette banks
× 16 colors
× 2 bytes
= 128 bytes
= 64 words
```

Canonical gameplay CRAM words satisfy:

```text
color & ~0x0EEE == 0
```

This is direct evidence from the canonical ROM, not an inferred graphics convention.

## Authoring module

`tools/build/scene_palette.py` introduces source schema:

```text
truerecall.scene_palette.v1
```

with:

```text
scene_index
retail_pointer
colors[64]
```

`retail_pointer` is identity/evidence metadata and cannot be silently changed. `colors` is the editable source payload.

The compiler validates:

- canonical base size and SHA-1;
- scene index range;
- equality of retail `palette_0` and `palette_1` pointers;
- 64-word palette length;
- valid Genesis CRAM bit layout;
- source retail-pointer identity when present.

## No-op behavior

If all 64 source colors equal retail, compilation returns the original 2 MiB ROM bytes exactly. No expansion, pointer rewrite or checksum churn occurs.

This is intentional: a source export followed by compile must remain a semantic and binary no-op.

## Authored behavior

For an edited palette, the compiler:

1. expands from 2 MiB to 4 MiB;
2. updates the Genesis ROM-end header;
3. writes a new 128-byte CRAM image in expanded ROM;
4. patches both scene palette pointers to that same new image;
5. repairs the Genesis checksum;
6. reparses both pointers and all 64 colors;
7. verifies that scene-record changes are contained strictly within offsets `+0x02..+0x09`.

Default allocation is `0x300000`, aligned to `0x10`.

The original palette remains immutable in the retail half of the ROM.

## Static validation — COMPLETE

`tests/test_scene_palette_static.py` exercises the compiler without copyrighted ROM bytes.

The current static suite passes **7/7** checks:

- valid CRAM words accepted;
- invalid low-bit CRAM word rejected;
- invalid high-bit CRAM word rejected;
- exact 64-word length enforced;
- non-integer colors rejected;
- expanded-ROM alignment contract verified;
- synthetic 2 MiB ROM end-to-end test.

The synthetic end-to-end case constructs a minimal scene table and retail CRAM image, temporarily binds the compiler's canonical hash gate to that synthetic fixture, and verifies:

```text
export
→ exact no-op compile
→ one-color edit
→ 4 MiB expansion
→ CRAM relocation to 0x300000
→ both scene palette pointers patched
→ authored color reparsed
→ Genesis checksum repaired
```

`py_compile` also passes for the M11F compiler and static test module.

This is strong evidence for compiler mechanics, but it is deliberately classified as **static/synthetic**, not canonical-ROM or runtime confirmation.

## Regression probe

`tools/rom_probe/scene_palette_probe.py` defines the M11F canonical gate.

It requires for all 19 scenes:

```text
export palette
→ validate 64 canonical CRAM words
→ compile unchanged source
→ exact original ROM bytes
```

It then performs one authored edit in scene 18 by changing exactly one valid CRAM word and requires:

- 4 MiB output;
- exactly one changed palette index;
- new palette allocation in expanded ROM;
- both scene palette pointers target the new CRAM image;
- scene-record containment to `+0x02..+0x09`;
- output SHA-1 in the generated report.

The probe also injects an invalid low-bit CRAM word (`0x0001`) and requires the compiler to reject it.

## Why this is separate from `scene_source.v1`

M11D persisted canonical JSON fingerprints for scene-source v1. Adding 64 palette words directly to that schema would intentionally change every source fingerprint and erase a useful regression anchor.

M11F therefore proves palette authoring independently first.

After canonical execution, the correct integration path is a versioned scene source (`scene_source.v2` or equivalent) whose source-level palette data lowers into the already-proven M11F palette compiler. M11D/v1 remains readable and regression-testable rather than being silently redefined.

## Canonical execution status

Canonical execution remains pending because the current runtime cannot materialize the canonical `True Lies (World)` ROM bytes from Library. The ROM registration remains visible at exactly 2,097,152 bytes, but raw-byte access is denied in this session.

No output SHA-1, checksum or all-scene palette fingerprints should be promoted until `scene_palette_probe.py` actually runs against SHA-1:

```text
d39174bed46ede85531b86df7ba49123ce2f8411
```

## Completion criteria

M11F is complete when:

1. 19/19 palette exports validate;
2. 19/19 unchanged palette sources compile to exact retail ROM bytes;
3. scene-18 single-color edit compiles to a deterministic 4 MiB build;
4. edited output reparses to the exact authored 64 colors;
5. invalid CRAM words are rejected;
6. `extracted_metadata/m11f_scene_palette.json` is generated from the successful probe;
7. runtime loading of the authored palette is visually confirmed once the BlastEm harness is restored;
8. only then is palette source integrated into the canonical unified scene-source schema.
