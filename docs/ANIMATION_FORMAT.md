# Animation Descriptor Format

The archetype table does not point directly at sprite pixels. It points at a compact animation/mapping descriptor consumed by the common animation code.

## Descriptor indirection — CONFIRMED

`object+0x2C` holds the descriptor base. Routine `0x00FDDC` receives an animation selector in `D0` and resolves it in two stages:

```text
encoded = word(descriptor + animation_selector)
object+0x24 = encoded
alias_offset = encoded & 0x0FFE
record_offset = word(descriptor + alias_offset)
object+0x20 = record_offset
```

Thus an animation selector does not directly point at a frame record. It selects an encoded/flagged entry, which in turn aliases another word containing the current mapping-record offset.

The low bit and upper flag bits of `encoded` have independent behavior. Bit 0 is consumed by `0xFDDC` for linked-object flag propagation; other encoded bits are used by update logic and remain only partially labeled.

Reproducible probe: `tools/rom_probe/animation_descriptor_probe.py`.

## Mapping/frame record — CONFIRMED structure

A resolved record begins at:

```text
descriptor + object+0x20
```

The record has:

```text
+0x00  word  unresolved sequencing/timing field
+0x02  word  unresolved sequencing/timing field
+0x04  word  unresolved sequencing/timing field
+0x06  word  geometry field A
+0x08  word  geometry field B
+0x0A  word  geometry field C
+0x0C  word  geometry field D
+0x0E  byte  record/render flags
+0x0F  byte  piece_count
+0x10  piece[0]   4 bytes
+0x14  piece[1]   4 bytes
...
```

Record size is therefore:

```text
0x10 + piece_count * 4
```

### Independent boundary proofs

Using animation selector `2` in four unrelated descriptors:

| Archetype | descriptor | record offset | pieces | computed size | next record |
|---:|---:|---:|---:|---:|---:|
| player 191 | `0x0E51FE` | `0x0168` | 2 | `0x18` | `0x0180` |
| 176 | `0x1008CE` | `0x015E` | 1 | `0x14` | `0x0172` |
| 166 | `0x12E720` | `0x0114` | 7 | `0x2C` | `0x0140` |
| 8 | `0x0DFD48` | `0x00EA` | 11 | `0x3C` | `0x0126` |

In every case the next known record begins exactly at `record + 0x10 + 4*N`, making the low byte at `+0x0F` a structurally confirmed piece count.

## Geometry fields — CONFIRMED role, exact names pending

Routine around `0x00194A` resolves `object+0x20`, adds it to `object+0x2C`, and reads record words `+0x06/+0x08/+0x0A/+0x0C` while applying object flip/orientation flags.

This proves the four words are record geometry/bounds data. Exact labels such as `min_x`, `origin_y`, `width` or `max_y` are intentionally withheld until the coordinate math is fully reconstructed.

## Piece entries — PARTIALLY RECOVERED

Each piece is four bytes. Repeated records strongly show a compact position/shape word followed by a second word associated with the piece's graphic/mapping identity. Examples form regular 16-pixel grids such as:

```text
180F 0022
290F 0023
0F1F 0024
1F1F 0025
2F1F 0026
0F2F 0027
1F2F 0028
```

The structure is real and deterministic, but the exact bit packing of the first word and whether the second word is a direct tile index versus an intermediate graphic index still require renderer-side proof. New asset tooling must preserve these fields opaquely until that consumer is recovered.

## Record flags

Byte `record+0x0E` is consumed by animation/render-state code; bits `0x20/0x40/0x60` visibly propagate into entity render flags. The exact full bitfield remains partially decoded.

## Production consequence

The current presentation chain is now:

```text
placement type_id
    ↓ object script
archetype ID (object+0x2A)
    ↓ table 0x079906
animation descriptor (object+0x2C)
    ↓ selector/alias indirection
mapping record (object+0x20)
    ↓ 16-byte header + N×4-byte pieces
sprite/mapping renderer   [next target]
```

The next reverse-engineering step is to follow the four-byte piece records into the sprite renderer and tile resource layer. Once that link is recovered, the project can build an actual sprite/animation exporter instead of treating animation descriptors as opaque binary blobs.
