# M0.6G/H — Gameplay Map Reinsertion and Edit Proofs

These laboratory builds prove that the recovered gameplay-map format and the TrueRecall LZBeam encoder can be used in the inverse direction to rebuild and edit a real level resource.

## M0.6G — semantic no-op relocation

Target: scene 0, C000 gameplay plane.

Retail map:

- dimensions: `107×45` tile words
- decoded size: `9,630` bytes
- retail LZBeam pointer: `0x01D4EE`
- map descriptor: `0x00FFBE`

TrueRecall decodes the retail resource, re-encodes the same 9,630 bytes to a deterministic 647-byte LZBeam stream, writes it to verified final-ROM FF padding at `0x1FB000`, redirects the descriptor and repairs the Genesis checksum.

The generated ROM re-decodes to the exact original 9,630-byte tilemap. The retail compressed block remains untouched.

Audited build:

```text
checksum = 0x10C7
SHA-1   = 0c3c04b4312fb714d2ee5f0c4c30bff6c6b0422a
```

Build tool: `tools/build/m06g_map_relocation_noop.py`.

## M0.6H — one-tile authoring edit

Using the same scene/plane, M0.6H changes exactly one decoded map word:

```text
(x=0, y=0): 0x0000 → 0x020C
```

The edited 9,630-byte tilemap is encoded by TrueRecall, relocated to `0x1FB000`, redirected through the map descriptor and checksummed.

Post-build validation decodes the resource from the generated ROM and compares every 16-bit map word against retail. Exactly one word differs: the authored `(0,0)` entry.

The new compressed stream is 648 bytes.

Audited build:

```text
checksum = 0x5F46
SHA-1   = 7135e65bcf44dbe84b428d8aea2b0eddcc238d63
```

Build tool: `tools/build/m06h_one_tile_map_edit.py`.

## Significance

Together M0.6G/H prove the complete static map-authoring path:

```text
retail map descriptor
→ LZBeam decode
→ editable 16-bit tilemap
→ controlled source edit
→ TrueRecall LZBeam encode
→ safe-space relocation
→ descriptor pointer patch
→ checksum repair
→ decode from generated ROM
→ exact structural regression comparison
```

Runtime rendering is still pending emulator/hardware validation, so these remain static authoring proofs rather than runtime-complete milestones.
