# Patches

Versioned engine modifications and patch metadata belong here.

The original ROM is never stored here. Prefer source-level patches, assembler hooks, relocation manifests or reproducible binary-diff formats generated from the canonical ROM.

Each patch must record:

- purpose
- base-ROM SHA-1
- affected ROM ranges
- required relocated data/code
- rollback path
- regression probes
- feature flag or milestone when applicable

The first patch milestone is M0.7: one isolated new player state/mechanic with a new animation and preserved original behavior.
