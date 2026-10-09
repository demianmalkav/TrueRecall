# M0.11E — All-Scene Source Matrix

Status: **PREPARED / EXECUTION PENDING**

M11E extends the canonical scene-source proof from the four structural representatives used by M11D to the complete 19-scene retail corpus.

The implementation lives in:

```text
tools/rom_probe/scene_source_matrix_probe.py
```

The probe is deliberately ROM-gated. It refuses to run unless the input is the immutable canonical base:

```text
size   2,097,152 bytes
SHA-1  d39174bed46ede85531b86df7ba49123ce2f8411
```

No retail-derived scene-source JSON is committed.

## Gate A — all 19 canonical exports

For every scene index `0..18`, the probe requires:

```text
canonical ROM
→ export_scene_source(scene)
→ schema/shape invariants
→ source_to_patch(source, deepcopy(source)) == zero operations
→ compile_source(source) == exact original ROM bytes
```

The structural checks include:

- both `C000` and `E000` plane word counts equal `width * height`;
- persistent placement IDs are unique and canonical (`retail_0000`, ...);
- world-record IDs are unique and canonical (`retail_000`, ...);
- broadphase dimensions are positive;
- the source compiler reports an explicit no-op build;
- the returned ROM is byte-for-byte identical to the 2 MiB base.

The resulting report stores per-scene canonical JSON size/SHA-256 fingerprints plus map dimensions, object counts, world dimensions and world-record counts. These fingerprints are evidence only; the retail-derived source payloads themselves remain local.

## Gate B — source-level semantic edits

M11E exercises the three authoring operations through editable scene sources rather than manually authored binary patches.

### Add — scene 18

The M11D source-level edit remains the deterministic add regression anchor:

- set `C000[0,0] = 0x0001`;
- add object `new_health_0`, type 54, at `(128,120)`;
- add world record `new_wall_0`, type 9, rectangle `(64,64)..(80,256)`.

Expected output retained from M11D:

```text
SHA-1    fac81fdc87b76a75c9b590d58707b16fcd6a5f04
checksum 0x3E9A
```

### Replace — scene 0 persistent object

M11E changes the first retail placement through stable source ID `retail_0000` by moving its X coordinate one pixel. The generated patch must contain exactly one object `replace` operation for `base_index = 0`.

Expected output retained from the M11C compiler matrix:

```text
SHA-1    c57a73e8f6ea8967a3f45b9d40b200ba8f9404c9
checksum 0x575A
```

This case also exercises a mixed-stride retail placement stream.

### Remove — scene 0 persistent object

M11E removes source record `retail_0000`. The differ must emit exactly:

```text
object remove base_index 0
```

The rebuilt placement count must decrease by exactly one while the object-stream compiler regenerates legal stride runs and relocation data.

### Replace — scene 6 world record

Scene 6 is retained as the non-trivial broadphase-layout case recovered as `26×55`. M11E changes `retail_000` to world type 11 through the source representation.

Expected output retained from M11C:

```text
SHA-1    f0c146a285a7c065045179f6ea22d93d3c91ab4e
checksum 0xA53C
```

The generated patch must be exactly one world `replace` operation and record count must remain unchanged.

### Remove — scene 6 world record

M11E removes `retail_000` and requires the rebuilt world record count to decrease by exactly one. The dense grid and deduplicated list pool remain compiler output, not editable source data.

## Regression anchors

M11E intentionally reuses known M11C/M11D output fingerprints for the add and replace cases. This prevents the broader matrix from silently accepting a compiler behavior change merely because the new probe and compiler changed together.

The two remove cases do not yet have persisted output fingerprints. Their first successful canonical execution will establish them in `extracted_metadata/m11e_scene_source_matrix.json`.

## Current execution blocker

The canonical ROM is still registered in the project Library as `True Lies (World).md`, with the exact expected 2,097,152-byte size, but the current chat runtime cannot materialize its raw bytes into the execution container. The Library text reader correctly reports no readable text because the file is binary despite the historical `.md` suffix.

Therefore M11E is **not CONFIRMED yet**. The probe and documentation are source-controlled, but no all-scene success claim is permitted until the probe actually runs against the SHA-1-verified base ROM.

## BlastEm recovery

The repository contains `.github/workflows/fetch-blastem.yml`, which downloads a fixed BlastEm release and checks its SHA-256 before publishing it as a workflow artifact. The M11E branch enables that workflow on the branch as well, so runtime tooling can be regenerated independently of the current container once GitHub Actions execution is available.

This does not replace the ROM gate: runtime validation still requires a locally accessible verified base ROM plus generated builds.

## Completion criteria

M11E is complete only when all of the following are true:

1. canonical input size and SHA-1 pass;
2. all 19 scene exports satisfy source-shape invariants;
3. all 19 source no-ops compile to the exact original ROM bytes;
4. scene-18 add reproduces the M11D SHA-1/checksum;
5. scene-0 object replace reproduces the M11C SHA-1/checksum;
6. scene-0 object remove compiles and reparses with count `N-1`;
7. scene-6 world replace reproduces the M11C SHA-1/checksum;
8. scene-6 world remove compiles with world-record count `N-1` and valid regenerated memberships;
9. `extracted_metadata/m11e_scene_source_matrix.json` is generated from that execution;
10. `TECHNICAL_STATE.md` and Drive project-control documents are updated only after the evidence exists.

## Next after M11E

Once this matrix passes, normal level editing can treat the canonical scene source as the stable authoring boundary across the complete retail scene corpus. The next production-facing gaps are tile/graphics-source authoring, palette authoring, script/objective authoring, M0.9C native player sequence integration and restored runtime regression for newly authored M10/M11 geometry.
