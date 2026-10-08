# Gameplay Map Format

Two independent gameplay packages have been reconstructed statically, proving the core map representation.

## Package 01 — CONFIRMED

- Graphics LZBeam: `0x014898` → `24,960` bytes = 780 8×8 tiles.
- Raw/flagged resource: `0x800178DA` — exact role unresolved; high bit appears to indicate raw/non-LZ data.
- Auxiliary pointer: `0x0001BF7A`.
- Layer A: `0x0001C8FC` → `9,630` bytes.
- Dimensions: `107×45` tiles.
- Layer B: `0x0001D4EE` → `9,630` bytes.

Proof: `107 × 45 × 2 = 9,630` exactly. Both layers reconstruct a coherent 856×360 pixel gameplay map.

## Package 02 — CONFIRMED

- Graphics LZBeam: `0x02667A` → `21,504` bytes = 672 tiles.
- Raw/flagged resource: `0x80029418`.
- Auxiliary pointer: `0x0001E7D0`.
- Layer A: `0x0001EACA` → `3,900` bytes.
- Dimensions: `50×39` tiles.
- Layer B: `0x0001F0B8` → `3,900` bytes.

Proof: `50 × 39 × 2 = 3,900` exactly. The same renderer reconstructs a second coherent gameplay map.

## Tilemap entries

Gameplay layers use 16-bit tile entries indexing the package tileset. Exact gameplay-specific attribute semantics beyond standard Genesis tile attributes remain under study.

## Descriptor tables

Repeated bank-end descriptor areas, including the region around `0x00FFA8`, appear to describe gameplay resource packages — HIGH CONFIDENCE.

## Unresolved data

- gameplay palette pointer(s)
- collision layer / material properties
- object placements and enemy/civilian spawns
- doors and interactive structures
- triggers and mission-objective scripts
- exact meaning of high-bit raw resource pointers

## Required proof before editor work

1. Enumerate every mission package automatically.
2. Identify the collision/object/spawn resources.
3. Implement export + import.
4. Prove a byte-stable no-op round trip before designing new maps.
