# Object VM Source / Assembler Toolchain

The True Recall reverse-engineering toolchain can now disassemble Beam's object VM, export retail programs to symbolic source, reproduce them byte-for-byte and relocate fully understood contiguous programs within a compatible 64 KiB VM branch bank.

## Components

- `tools/rom_probe/vm_disasm.py` — control-flow-aware VM disassembler.
- `tools/rom_probe/vm_source_export.py` — exports a fully reachable contiguous VM program as symbolic source.
- `tools/rom_probe/vm_region_source_export.py` — exports the owned forward code hull and preserves unclassified internal bytes explicitly as `.raw`.
- `tools/rom_probe/vm_asm.py` — assembler for symbolic source plus explicit raw blocks.
- `tools/rom_probe/vm_roundtrip_probe.py` — proves the retail-used instruction grammar.
- `tools/rom_probe/vm_assembler_probe.py` — validates whole-script source→assembly and safe relocation.
- `tools/rom_probe/vm_region_roundtrip_probe.py` — validates mixed reachable-code/raw-region reconstruction.

## Grammar gate — CONFIRMED

Across the 136 scripted retail `type_id` entries, the byte-roundtrip probe visited 29,745 reachable instructions (27,818 unique ROM addresses). Retail content exercises 53 of the VM's 72 opcode slots. Every reachable instruction used by retail re-encodes byte-for-byte to the canonical ROM.

The remaining 19 opcode slots exist in the interpreter but are not exercised by reachable retail object programs in `type_id 0..138`; they are outside the current authoring guarantee until separately proven.

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

This covers pickups, a combat actor, a mission interactable and a large vehicle/prop script rather than only trivial examples.

## Relocation — CONFIRMED for fully decoded contiguous scripts

`type_id 69` was exported from its retail base `0x1761F0` and assembled at `0x177000`.

- output size remained 258 bytes;
- all seven symbolic labels moved by the exact relocation delta;
- the reachable instruction count remained 68;
- normalized opcode/size topology matched the original program;
- local branch targets were rewritten to relocated labels.

VM conditional/unconditional branches and switch targets are bank-local 16-bit addresses, so relocation must remain within a compatible 64 KiB bank unless the source is transformed. VM `CALL` targets are absolute 32-bit addresses and do not share that restriction.

## Mixed code/raw regions — CONFIRMED roundtrip

Some retail type programs contain bytes inside their local forward code hull that are not reachable from the type entry under the statically recovered CFG. The project does not silently classify these bytes as instructions or discard them.

`vm_region_source_export.py` therefore emits explicit `.raw` blocks for these gaps. The assembler preserves them verbatim.

The regression probe reconstructs the following difficult regions byte-identically:

| type_id | region bytes | raw blocks | raw bytes | note |
|---:|---:|---:|---:|---|
| 38 | 1,056 | 1 | 4 | one dead/unreferenced `JMP`-shaped block |
| 104 | 1,660 | 1 | 4 | local program plus large shared/external reachable code excluded from ownership |
| 105 | 1,094 | 1 | 4 | local program with external shared VM subroutine calls |
| 28 | 6,132 | 4 | 2,718 | substantial opaque internal regions preserved exactly |

### Ownership rule

A type's editable region begins at its per-type script entry and includes reachable instructions forward of that entry before the next per-type entry. Reachable code outside that owned region is treated as shared/external and remains referenced rather than copied into the type source.

The emitted hull ends at the last owned reachable instruction. Only gaps *inside* that hull are emitted as `.raw`.

This avoids the incorrect alternative of defining ownership simply as “until the next script pointer”, which can swallow unrelated ROM resources separated by tens or hundreds of kilobytes.

## Relocation safety for `.raw`

A mixed source containing `.raw` is round-trippable at its retail address but is **not automatically relocatable**. Opaque bytes may contain hidden low-word branch targets, embedded pointers, alternate VM entry points or data structures whose relocation semantics are not yet known.

Therefore:

- no `.raw` source may be relocated in production merely because it assembles;
- relocation becomes allowed only after each raw block is structurally classified or proven position-independent;
- the assembler deliberately treats `.raw` as literal bytes and does not rewrite embedded addresses.

## Why the `type 38` gap matters

The first four-byte gap recovered inside type 38 is `0008 9BDA`, which itself decodes as a VM `JMP` to `0x169BDA`, but no placed retail type entry or statically reachable retail edge targets that address. It is preserved as raw/unclassified instead of being promoted to live code without evidence.

This is the project's intended failure-containment behavior: unexplained bytes remain explicit rather than being normalized away.

## Production consequence

TrueRecall now has a first proven source-level authoring seam for Beam's object behavior VM:

```text
retail bytecode
→ CFG / symbolic source
→ editable source representation
→ assembler
→ byte-identical reproduction
```

For fully decoded contiguous programs, symbolic relocation is also proven.

The next gate is to eliminate or classify `.raw` blocks progressively and then perform a deliberately harmless VM-script edit in an isolated test build. Runtime regression validation remains required before this becomes an approved M0.7 gameplay-extension path.
