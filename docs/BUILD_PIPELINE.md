# Build Pipeline

The project must never depend on a hand-edited ROM.

Target model:

```text
verified True Lies (World) ROM
+ source-controlled code patches
+ source-controlled metadata
+ source-controlled original Total Recall assets
+ deterministic tools
= reproducible TrueRecall build
```

## Required invariants

1. Verify base ROM SHA-1 before any operation.
2. Never overwrite the base ROM.
3. Extracted copyrighted True Lies assets remain local/generated and are not committed.
4. Source-controlled metadata may record offsets, hashes, dimensions, symbols and transformation rules.
5. Every build emits its base-ROM hash, Git commit SHA and enabled feature set.
6. A baseline/no-op build must be byte-identical before structural patches are trusted.
7. Every extension receives a regression test or reproducible behavioral probe.

## Planned stages

1. `verify_rom`
2. `extract_metadata`
3. `apply_code_patches`
4. `build_assets`
5. `encode_lzbeam`
6. `insert_assets`
7. `fix_pointers/checksum as required`
8. `emit build manifest`
9. `run static regression assertions`
10. `run emulator/runtime regression suite` when automation is available

## Repository layout target

- `tools/rom_probe/`
- `tools/lzbeam/`
- `tools/asset_extractor/`
- `tools/map_extractor/`
- `tools/build/`
- `symbols/`
- `patches/`
- `tests/`
- `extracted_metadata/`

The original ROM path is always supplied locally by the developer/user and never stored in Git.
