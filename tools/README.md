# Tools

Source-controlled reverse-engineering and build tools live here. Tools must be deterministic, ROM-hash aware, and must not embed copyrighted ROM data.

Planned modules:

- `rom_probe/` — ROM identity, headers, assertions, static landmarks and symbol probes.
- `lzbeam/` — Beam LZ decode/encode and round-trip validation.
- `assets/` — Genesis tile/tilemap/CRAM extraction and conversion.
- `maps/` — gameplay package discovery, map rendering, collision/spawn/script parsing.
- `build/` — reproducible patch/build orchestration and build manifest emission.
- `runtime/` — debugger/emulator-assisted traces and regression automation when available.

Exploratory scripts are promoted here only after paths, assumptions and outputs are made project-safe and reproducible.
