# M0.11G — Versioned Scene Source v2

Status: **IMPLEMENTED / STATIC SUITE DEFINED / EXECUTION PENDING**

M11G integrates the M11F gameplay palette source into the unified authoring model without silently redefining the M11D `scene_source.v1` schema or invalidating its persisted canonical fingerprints.

## Design rule

`scene_source.v1` remains immutable as a historical/compiler contract.

M11G introduces:

```text
truerecall.scene_source.v2
```

The v2 source is intentionally a semantic authoring layer first. It does not yet claim a combined binary transaction for palette + maps + objects + world collision. Binary lowering remains separated until M11F canonical execution succeeds and the combined allocator/containment path is regression-protected.

## Schema migration

In v1, retail palette identity is stored inside immutable metadata:

```text
immutable.palette_0
immutable.palette_1
```

All 19 retail scenes have equal pointers, so v2 removes those duplicate immutable fields and introduces one explicit source section:

```text
palette
  retail_pointer
  colors[64]
```

`retail_pointer` remains immutable evidence/identity metadata. `colors[64]` is editable authoring data.

The transformation is designed to be lossless:

```text
scene_source.v1 + scene_palette.v1
→ scene_source.v2
→ scene_source.v1 + scene_palette.v1
```

The downgraded v1 reconstructs both `palette_0` and `palette_1` from the single v2 retail pointer.

## Implementation

`tools/build/scene_source_v2.py` provides:

- `upgrade_v1_source(...)`
- `validate_v2_source(...)`
- `downgrade_v2_source(...)`
- `palette_source_from_v2(...)`
- `export_scene_source_v2(...)`
- `source_v2_to_patch(...)`
- `patch_v2_is_noop(...)`

The module reuses the established M11D `source_to_patch` logic for maps, persistent placements and world collision rather than copying those differ semantics.

Palette validation is delegated to the M11F CRAM validator.

## Patch lowering

M11G introduces a semantic patch envelope:

```text
truerecall.scene_patch.v2
```

containing:

```text
scene_index
scene_patch        # existing truerecall.scene_patch.v1
palette_operation  # null or replace_palette
```

An unchanged v2 source is a no-op only if both conditions hold:

1. the embedded v1 scene patch has zero map/object/world operations;
2. `palette_operation` is null.

A palette edit lowers to:

```text
replace_palette
  retail_pointer
  changed_indices[]
  colors[64]
```

The full 64-word palette is carried so downstream compilation does not depend on reconstructing unchanged color words from a partially edited patch.

## Isolation invariant

Changing only palette colors must not generate:

- map operations;
- object operations;
- world operations.

Conversely, map/object/world edits must continue to lower exactly through the M11D v1 differ while leaving `palette_operation = null` when colors are unchanged.

This is the central compatibility guarantee of M11G.

## Static suite

`tests/test_scene_source_v2_static.py` defines seven checks:

1. v1 + palette → v2 → v1 + palette is lossless;
2. unchanged v2 source is a semantic no-op;
3. palette-only edit generates only `replace_palette`;
4. existing map/object/world edits pass through unchanged to `scene_patch.v1`;
5. retail palette pointer identity cannot change;
6. invalid CRAM data is rejected;
7. v2 rejects duplicated `palette_0` / `palette_1` fields in immutable metadata.

The suite is source-controlled but its execution is not yet persisted as evidence in this milestone document.

## Why binary compilation is not in M11G yet

The existing M11B transactional compiler owns one expanded-ROM allocation arena for maps, objects and world resources. M11F currently owns an isolated palette relocation path for proof purposes.

Simply running those compilers sequentially would be wrong because:

- both expect the canonical 2 MiB base as their input contract;
- each independently owns ROM expansion/header/checksum work;
- independent allocation bases could collide;
- scene-record containment must be audited once across the combined transaction.

Therefore M11G stops at deterministic semantic lowering. The next binary-integration gate must give palette allocation to the same M11B arena and repair the checksum once at the end.

## Completion criteria

M11G can be promoted to statically validated when:

1. `tests/test_scene_source_v2_static.py` executes cleanly;
2. v1↔v2 losslessness is demonstrated;
3. palette-only isolation is demonstrated;
4. v1 map/object/world passthrough is demonstrated.

Canonical promotion additionally requires M11F canonical palette execution.

The subsequent transaction milestone should compile v2 through one allocation arena and prove a combined edit containing at least one palette color plus one existing M11 scene resource family.
