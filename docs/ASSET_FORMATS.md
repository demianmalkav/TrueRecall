# Asset Formats

## LZBeam — CONFIRMED

Beam Software's LZ format has been validated directly against the canonical True Lies ROM.

Header:

- word `+0`: uncompressed size
- word `+2`: command-bitstream offset basis
- payload begins at `+4`

The stream alternates literal runs and absolute-output backreferences with Elias-like variable-length counts.

A strict structural scan found 101 tile-aligned candidates in the current ROM.

## Genesis graphics

- 8×8 tiles are 32 bytes each in 4bpp format.
- `0x014898` decompresses to 24,960 bytes = 780 tiles.
- `0x1AAE30` decompresses to 3,488 bytes = 109 tiles.
- `0x1B0000` decompresses to 3,200 bytes = 100 tiles.

## Cutscene tilemaps — CONFIRMED

A full-screen cutscene tilemap is exactly 1,792 bytes:

`32 columns × 28 rows × 2 bytes = 1,792`

Entries use the standard Genesis 16-bit tile attribute structure: tile index, H/V flip, palette bank and priority.

## Cutscene palettes — CONFIRMED

Each cutscene frame points to a raw 128-byte CRAM image:

`4 palettes × 16 colors × 2 bytes = 128 bytes`

## Cutscene sequence table — CONFIRMED

Starts at `0x00AC3A`:

```text
word frame_count
repeat frame_count times:
    long gfx_lzbeam_ptr
    long tilemap_lzbeam_ptr
    long cram_128_ptr
    long caption_or_aux_ptr
```

Fourteen full-color frames across ten groups have been reconstructed from the ROM without emulator screenshots.

## Next pipeline step

Implement the inverse path:

`source asset → Genesis tiles/map/CRAM → LZBeam encode → relocation/reinsertion → ROM rebuild`

No-op rebuilds must be verified before edited assets are trusted.
