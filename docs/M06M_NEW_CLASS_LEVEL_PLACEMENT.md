# M0.6M — New Scripted Class Placed Directly in a Level

M0.6M combines two previously independent static authoring capabilities:

- M0.6F: create a new independently addressable scripted object class in an unused engine type slot;
- M0.6L: rebuild and relocate persistent scene placement streams from declarative source data.

The result is the first build in which a **new TrueRecall-defined class is inserted directly into a retail level placement stream**.

It remains runtime-unvalidated until executed in a Genesis emulator or hardware.

## New type

Unused retail `type_id 1` is converted from direct-code mode to VM-scripted mode.

A source-level clone of the proven type-69 shotgun pickup is assembled at:

```text
0x1FB000
```

Its controlled behavior change remains:

```text
initial shotgun shell grant 5 → 6
```

Type 1 receives an independent table entry while deliberately reusing the known-safe archetype/stat profile of type 69 for this laboratory proof.

The original type 69 script and pointer remain untouched.

## Direct level placement

The scene-object compiler then adds one persistent placement to scene 1:

```text
type_id       = 1
stride        = 6
status_flags  = 0x7800
x             = 256
y             = 7984
```

Memory reservations are explicitly separated:

```text
new type-1 VM script:     0x1FB000...
scene descriptor/resource: from 0x1FC000...
```

This prevents the newly-authored object class from colliding with the relocated scene data.

## Structural validation — CONFIRMED

`tools/build/m06m_new_type_scene.py` starts from the canonical ROM and proves in the generated ROM that:

- type 1 switches to scripted mode;
- type 1 points to the new VM script at `0x1FB000`;
- archetype/stat metadata for type 1 is explicitly populated;
- donor type 69 remains at its retail pointer;
- scene 1 is reparsed after compilation;
- exactly one placement exists with `type_id=1, x=256, y=7984`;
- the placement is a six-byte record;
- scene data is relocated independently at/after `0x1FC000`;
- the Genesis checksum is regenerated and validated.

Audited build:

```text
scene descriptor = 0x1FC000
object LZ stream = 0x1FC00C
placements       = 72 → 73
checksum         = 0x3CF5
SHA-1            = dc672e205686957c0c17655a387e7ea211eb9ef6
```

The generated ROM is not committed.

## What M0.6M proves

The complete static entity-authoring path now exists:

```text
unused engine type slot
→ new VM source
→ independent type pointer/table entry
→ archetype/stat profile
→ semantic scene manifest
→ persistent level placement
→ regenerated object stream/descriptor
→ LZBeam encoding
→ safe ROM relocation
→ checksum repair
→ full structural reparse
```

This is the point at which a future Total Recall level author no longer needs to think in terms of patching an existing True Lies placement class. A new class can be introduced and placed as source-controlled content.

## Remaining M0.7 gate

The proof is still static. Runtime validation in a Genesis emulator/hardware is required, and M0.7 still targets a genuinely new mechanic/state/animation or an equivalently meaningful behavior beyond the deliberately simple cloned pickup used here as a safe integration test.
