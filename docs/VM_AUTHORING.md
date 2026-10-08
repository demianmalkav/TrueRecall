# Object VM Authoring Toolchain

This document records the point at which the retail True Lies object VM became not only readable but source-authorable and relocatable.

## Status

The project now has:

- `tools/rom_probe/vm_disasm.py` — control-flow-aware VM disassembler.
- `tools/rom_probe/vm_asm.py` — two-pass symbolic assembler.
- `tools/rom_probe/vm_source_export.py` — exports eligible retail type scripts as editable source.
- `tools/rom_probe/vm_roundtrip_probe.py` — proves instruction-level decode→encode identity.
- `tools/rom_probe/vm_assembler_probe.py` — proves full-script source→assemble identity and relocation.

All tools reject a ROM whose SHA-1 is not the canonical `d39174bed46ede85531b86df7ba49123ce2f8411`.

## Instruction round-trip — CONFIRMED

`vm_roundtrip_probe.py` traverses all 136 scripted `type_id` entries in the retail 0..138 range and re-encodes every reachable instruction.

Validated result:

- 136 scripted type IDs.
- 29,745 per-root reachable-instruction visits.
- 27,818 unique reachable VM instruction addresses.
- 53 of the 72 VM opcode slots are exercised by retail scripts.
- every decoded reachable instruction re-encodes byte-for-byte to the original ROM.

The remaining 19 opcode slots are therefore engine capacity not observed on reachable retail paths; they are not assumed unused in every possible hidden/debug context.

## Source-level round-trip — CONFIRMED

The source exporter currently accepts scripts whose reachable code region is contiguous. Eight representative scripts were exported to symbolic source and reassembled byte-identically:

| type_id | original base | bytes | reachable instruction addresses |
|---:|---:|---:|---:|
| 51 | `0x1763CA` | 148 | 38 |
| 54 | `0x1768B6` | 268 | 86 |
| 61 | `0x1769C2` | 174 | 47 |
| 69 | `0x1761F0` | 258 | 68 |
| 70 | `0x1762F2` | 216 | 57 |
| 5 | `0x179698` | 1166 | 330 |
| 12 | `0x17DE3C` | 176 | 47 |
| 46 | `0x174CE4` | 1282 | 371 |

The conservative contiguous-region requirement is deliberate. Scripts with embedded data/gaps remain rejected until the source format has explicit directives for those structures.

## Relocation — CONFIRMED

Retail type 69 was exported from `0x1761F0` and assembled at `0x177000`.

The relocated script:

- remains exactly 258 bytes;
- preserves all symbolic labels with the relocation delta applied;
- decodes to the same normalized 68-instruction shape;
- rewrites bank-local branch/switch targets consistently;
- preserves absolute native-call semantics.

This proves the VM assembler can support relocated/new object scripts rather than being restricted to same-address patches.

## Source syntax

The assembler supports symbolic labels and names for recovered opcodes/natives. Examples:

```text
L_1761F0:
  MOVI_W_D2 0x0005
  PUSH_D2_W
  NATIVE GrantWeapon
  BR_FALSE L_176240
```

Control-flow mnemonics include:

- `BR_TRUE`
- `BR_FALSE`
- `JMP`
- `CALL`
- `RET_OR_END`
- `SWITCH_D2`
- `NATIVE`

Unknown-but-sized VM opcodes may remain representable as `OP_xxxx` until semantics are proven.

## Production consequence

The preferred path for new Total Recall object behavior is now:

```text
human-readable VM source
→ symbolic VM assembler
→ relocated script block if needed
→ type pointer/table update
→ reproducible ROM build
→ regression probes
```

68000 code should be reserved for behavior that cannot be expressed cleanly through the retail VM/native API.

## Remaining work before production scripts

1. Add explicit data directives for scripts containing embedded tables/gaps.
2. Build a relocation allocator rather than choosing free-space addresses manually.
3. Emit a relocation manifest and pointer-table patch automatically.
4. Add static validation for native-call ABI/stack balance.
5. Create one new synthetic object script and run it in emulator as the first end-to-end authoring proof.
