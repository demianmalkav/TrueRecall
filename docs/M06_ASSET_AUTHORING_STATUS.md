# M0.6 Asset Authoring Status

By the branch-integration point, TrueRecall has static, reproducible inverse pipelines for both object behavior and gameplay map data.

## Object behavior

See `VM_AUTHORING.md`, `M06E_VM_RELOCATION.md` and `M06F_NEW_SCRIPTED_TYPE.md`.

The project can export eligible retail VM scripts, edit symbolic source, assemble/relocate them, redirect type pointers, and create a previously unused engine type as a new independently addressable scripted class.

## Compressed resources

See `LZBEAM_ENCODER.md`.

The project can encode Beam-compatible LZBeam data. 102 known scene/cutscene resources pass decode→encode→decode with byte-identical decompressed content; 78 of those 102 fit their retail compressed footprint with the current deterministic greedy encoder.

## Gameplay map data

See `M06G_MAP_RELOCATION.md`.

Scene 0 C000 map data has been re-encoded, relocated and pointer-patched as a semantic no-op. A second build edits exactly one 16-bit tilemap word and proves exactly one decoded map word differs afterward.

## Current limitation

These are static ROM-construction proofs. Runtime execution/rendering remains an explicit gate because the current environment has no Genesis emulator. No generated ROM should be described as runtime-validated until it has been run in an emulator or on hardware.
