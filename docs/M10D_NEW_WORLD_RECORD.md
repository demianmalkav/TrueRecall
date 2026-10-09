# M0.10D — New World Record Authoring

M10D proves statically that TrueRecall can add a completely new collision/material rectangle without replacing an existing retail record and without shifting or overwriting the unknown retail data that follows the scene-0 record table.

Runtime validation remains pending.

## Conservative layout strategy

Scene 0 is relocated to expanded-ROM base `0x230000`, as already runtime-proven in M10A.

The original scene-0 resource occupies `0x0000..0x23BD` relative to that base. M10D preserves the complete retail payload after the dense grid byte-for-byte and allocates authored structures after it:

```text
retail payload          0x0000..0x23BD
new world record        0x2400..0x2409
new cell-list pool      0x2500..0x2BAF
new pool sentinel       0x2BB0
```

The dense 54×23 grid at `0x0000..0x09B3` is regenerated so its non-zero pointers target the new pool at `0x2500+`.

Old retail list pool, record table and trailing bytes remain present and untouched; the new grid simply no longer points to the old list pool.

## New record

The authored record is:

```text
resource-relative offset  0x2400
absolute ROM address      0x232400
world_type                9
geometry                  (800,544) .. (816,800)
```

This is a new standard player/projectile-blocking rectangle, positioned one 64-pixel broadphase column east of the retail wall used in M10B/C.

## Broadphase result

Only five scene-0 cells gain the new record:

```text
(12,8)
(12,9)
(12,10)
(12,11)
(12,12)
```

The new deduplicated list pool is 1712 bytes and remains comfortably below the 15-bit resource-relative pointer limit.

All list references resolve either to one of the 375 original retail records or to new record `0x2400`.

## Static safety proof

`tools/build/m10d_new_world_record.py` asserts:

- canonical base-ROM hash and size;
- exact retail broadphase round-trip before authoring;
- preserved full retail payload after the dense grid;
- new record address does not overlap retail data;
- new list pool does not overlap the new record;
- every non-zero grid pointer targets the authored pool;
- every decoded pool reference targets a known old/new record;
- exactly five semantic cell memberships change;
- Genesis checksum is regenerated.

Audited build:

```text
ROM size      4,194,304
checksum      0x3D11
output SHA-1  d7b6c4c75ee7d07898b15efdb623b164ea8e6cfc
```

Metadata:

`extracted_metadata/m10d_new_world_record.json`

## Why the pool is remote

Retail packs grid, list pool, sentinel and record table contiguously, but runtime pointers are resource-relative 16-bit values. M10D exploits that property rather than inserting bytes into the retail payload.

This is safer because the 1212 bytes following the retail scene-0 record table are clearly non-padding data whose semantics are not yet fully classified. M10D leaves those bytes at the exact original relative offsets.

## Production consequence

The collision authoring model can now represent:

```text
world_record {
    type
    x_min
    y_min
    x_max
    y_max
}
```

and compile an expanded set of records plus a separately placed deduplicated broadphase pool.

Once runtime validated, this removes the final structural dependency on the number and locations of retail collision records. Total Recall levels can then introduce their own walls, pass-through materials and projectile-specific materials instead of mutating only pre-existing rectangles.

## Remaining gate

The M10D build must be runtime-tested with the deterministic BlastEm harness. The expected observation is that the original wall at column 11 remains and the new authored wall at column 12 independently blocks Harry across rows 8..12.
