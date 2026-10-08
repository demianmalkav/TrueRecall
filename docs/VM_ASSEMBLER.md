# Object VM Source / Assembler Toolchain

The True Recall reverse-engineering toolchain can now export selected retail object-VM programs to symbolic source, assemble that source back to bytecode, and relocate programs within a compatible 64 KiB VM branch bank.

## Components

- `tools/rom_probe/vm_disasm.py` — control-flow-aware VM disassembler.
- `tools/rom_probe/vm_source_export.py` — exports a contiguous reachable retail script as symbolic source.
- `tools/rom_probe/vm_asm.py` — assembler for symbolic source.
- `tools/rom_probe/vm_roundtrip_probe.py` — proves byte-level grammar for all reachable retail VM instructions.
- `tools/rom_probe/vm_assembler_probe.py` — validates full script source→assembly and relocation.

## Grammar gate — CONFIRMED

Across the 136 scripted retail `type_id` entries, the byte-roundtrip probe visited 29,745 reachable instructions (27,818 unique ROM addresses). Retail content exercises 53 of the VM's 72 opcode slots. Every reachable instruction used by retail re-encodes byte-for-byte to the canonical ROM.

The remaining 19 opcode slots are present in the interpreter but are not exercised by reachable retail object programs in `type_id 0..138`; they are therefore outside the current authoring guarantee.

## Whole-script roundtrip — CONFIRMED

The assembler regression probe exports and reassembles these contiguous retail scripts byte-identically:

| type_id | original base | bytes | reachable instruction addresses |
|---:|---:|---:|---:|
| 51 | `0x1763CA` | 148 | 38 |
| 54 | `0x1768B6` | 268 | 86 |
| 61 | `0x1769C2` | 174 | 47 |
| 69 | `0x1761F0` | 258 | 68 |
| 70 | `0x1762F2` | 216 | 57 |
| 5 | `0x179698` | 1,166 | 330 |
| 12 | `0x17DE3C` | 176 | 47 |
| 46 | `0x174CE4` | 1,282 | 371 |

This covers pickups, an enemy/combat actor, a mission interactable and a large vehicle/prop script rather than only trivial examples.

## Relocation — CONFIRMED

`type_id 69` was exported from its retail base `0x1761F0` and assembled at `0x177000`.

- output size remained 258 bytes;
- all seven symbolic labels moved by the exact relocation delta;
- the reachable instruction count remained 68;
- normalized opcode/size topology matched the original program;
- local branch targets were rewritten to the relocated labels.

VM conditional/unconditional branches and switch targets are bank-local 16-bit addresses, so relocation must remain within a compatible 64 KiB bank unless the source program is transformed. VM `CALL` targets are absolute 32-bit addresses and do not share that restriction.

## Current safety restriction

The source exporter deliberately rejects scripts whose reachable instructions contain gaps. Those gaps may represent embedded tables, unreachable data, alternate entry points or other structures. The assembler will not silently invent bytes for them.

Therefore the current toolchain is safe for scripts whose reachable program is contiguous. Scripts such as `type_id 38`, which contain at least one gap, remain read-only until the source format gains explicit raw-data / origin / secondary-entry directives.

## Next authoring step

Add lossless representation for mixed code/data scripts, for example explicit directives such as:

```text
.org <address-or-relative-offset>
.raw <hex bytes>
.word <value-or-label>
.long <value-or-label>
```

The exact syntax is not frozen yet. The requirement is stronger than convenience: export→assemble must remain byte-identical before any edited program is allowed into a ROM build.

## Production consequence

This is the first proven source-level authoring seam in the retail engine. We can now represent, inspect, reproduce and relocate a nontrivial subset of Beam's object behavior bytecode. The next gate is complete mixed code/data roundtrip; after that, controlled VM-script modification can begin under regression testing.
