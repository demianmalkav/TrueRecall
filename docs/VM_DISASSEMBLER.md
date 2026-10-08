# Object VM Disassembler

`tools/rom_probe/vm_disasm.py` converts a scripted retail `type_id` (or a raw VM script address) into a control-flow-aware textual disassembly.

## Current scope

The tool verifies the canonical ROM SHA-1 before decoding and follows:

- conditional branches
- unconditional branches
- VM calls / returns
- switch tables
- native calls

It emits labels for reachable control-flow targets and uses symbolic names only where the underlying 68000 handler is understood well enough to support them.

Example usage:

```text
python tools/rom_probe/vm_disasm.py "True Lies (World).md" --type 69
python tools/rom_probe/vm_disasm.py "True Lies (World).md" --type 38 --out type38.vm.txt
```

Do not commit generated full script dumps; they are analysis outputs derived from the retail ROM. The source-controlled artifact is the decoder itself.

## Confirmed VM control opcodes

| VM opcode | Semantic |
|---:|---|
| `0x0000` | branch when `D2` is true/nonzero |
| `0x0004` | branch when `D2` is false/zero |
| `0x0008` | unconditional branch |
| `0x000C` | VM subroutine call to absolute address |
| `0x0010` | return from VM subroutine, or end/destroy at top-level |
| `0x00AC` | switch on `D2` |
| `0x00E4` | call native 68000 routine |

## Confirmed data/register families

The disassembler names the already-proven immediate loads, object-relative loads/stores, indirect loads/stores, comparisons, boolean/logical operations, stack operations, event read and scheduler/wait operations. Unresolved arithmetic/shift handlers remain numerically named rather than guessed.

## Named native calls

The current native dictionary includes known presentation, movement, stats, spawn, archetype, message/UI and combat functions such as:

- `PlayAnimation`
- `PlayFacingAnimation`
- `PlayFacingAnimation13`
- `PlayDirection24Animation`
- `ApplyFacingMovement`
- `InitArchetypeStats`
- `SpawnLinkedObject`
- `SpawnLinkedOffsetObject`
- `SetArchetype`
- `GrantWeapon`
- `ShowMessage`
- `PlayerVisibilityTest`
- `FireSpreadProjectile`
- `FireStandardProjectile`

Unproven native addresses stay numeric.

## Validation examples

The decoder has been exercised against:

- type 69 (shotgun weapon pickup), where the output exposes ownership tests, ammo cap logic, ammo addition and `GrantWeapon`;
- type 38 (standard ranged actor), where the output exposes callback installation, visibility tests, movement, animation state, scheduler waits and the larger AI control flow.

## Authoring consequence

This is the first step from binary reverse engineering toward a source-like representation of object behavior. The next milestone is a lossless VM assembler/encoder: disassemble a known script, re-encode it byte-for-byte, and only then allow authored script changes.
