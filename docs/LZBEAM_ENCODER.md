# LZBeam Encoder / Reinsertion Capability

TrueRecall now has both directions of Beam's main compressed-resource format:

```text
ROM LZBeam → decompressed asset data
asset data → deterministic compatible LZBeam
```

Tool: `tools/lzbeam/lzbeam_codec.py`.

## Format recap — CONFIRMED

A block begins with:

```text
+0x00 word decompressed length
+0x02 word command-stream offset basis
+0x04 ... literal payload bytes
... command bits
```

The command stream uses:

- Elias-like positive integer counts;
- an initial mandatory literal run;
- absolute output backreferences;
- copy length = encoded count + 2;
- a one-bit choice after a backreference between another backreference and a literal run;
- a dynamic absolute-source bit width based on bytes already written.

Backreferences may overlap their own output, allowing compact repeated patterns.

## Encoder — CONFIRMED compatible

The project encoder uses a deterministic greedy match finder over three-byte prefixes and emits the same command grammar expected by the retail decoder.

It intentionally does **not** promise byte-for-byte reproduction of Beam's historical compressor. The invariant is instead:

```text
decode(encode(decoded_retail_resource)) == decoded_retail_resource
```

## Mass validation — CONFIRMED

`tools/rom_probe/lzbeam_encode_probe.py` derives compressed-resource pointers directly from:

- all 19 gameplay scene records;
- gameplay plane graphics/map descriptors;
- gameplay object-stream descriptors;
- the cutscene sequence table at `0x00AC3A`.

This produces 102 unique known retail LZBeam blocks.

All 102 pass:

```text
retail block
→ decode
→ TrueRecall encode
→ TrueRecall decode
→ byte-identical decompressed data
```

## Compression quality

Against the exact number of retail compressed bytes consumed by the decoder:

- 78 / 102 newly encoded resources are the same size or smaller than retail;
- 24 / 102 are larger;
- mean `new_size / retail_size ≈ 0.9983`.

Thus the current greedy encoder is already near the original compressor's aggregate efficiency despite not attempting to reproduce its exact parsing decisions.

Some extremely repetitive retail maps are compressed more aggressively by Beam and may need relocation if edited/re-encoded with the current encoder. This is an allocation/layout issue, not a decoding compatibility issue.

## Production consequence

The project can now compile edited/new:

- gameplay tilemaps;
- gameplay tilesets;
- object placement streams;
- cutscene graphics;
- cutscene tilemaps;
- other resources using the same LZBeam container.

A future resource builder should choose between:

1. **in-place rewrite** when encoded output fits the original footprint;
2. **relocation + pointer update** when it grows;
3. optional compressor optimization if ROM-space pressure later justifies it.

## Next reinsertion proof

The strongest next no-op/insertion test is:

```text
extract one gameplay map layer
→ decode
→ re-encode with TrueRecall
→ relocate if needed
→ patch its descriptor pointer
→ rebuild checksum
→ decode from generated ROM and compare against original map bytes
```

After that, edit a deliberately harmless tile entry and verify the generated ROM structurally before runtime playtest.
