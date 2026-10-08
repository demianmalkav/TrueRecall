# Generic Object Behavior VM

Most retail scene objects are not initialized by unique hardcoded constructors. They use a compact data-driven interpreter shared across object types.

## Type initialization path — CONFIRMED

The scene materializer masks the placement word with `0x03FF` and calls the generic type initializer at `0x010102`.

That initializer indexes three type tables:

```text
0x07A24A + type_id      byte table → object+0x04
0x07A33C + type_id      byte selector
0x07953E + type_id*4    long per-type pointer
```

For retail placement IDs `0..138`, the first table is zero for every type used by the placement stream. It is nevertheless a real engine table; nonzero entries exist at higher engine type IDs and its exact semantic label remains unresolved.

## Scripted versus direct-code types — CONFIRMED

The selector byte at `0x07A33C` determines which execution representation is installed.

### selector = 1: scripted/data-driven type

The initializer stores:

- per-type long from `0x07953E` into `object+0x42`
- fixed generic interpreter address `0x00011934` into `object+0x3E`
- a low-RAM pointer to `object+0x3E` into `object+0x10`

Thus `object+0x42` is the type-specific script/data pointer while `0x11934` is the shared execution handler.

### selector = 0: direct-code type

The per-type long from `0x07953E` is stored in `object+0x42`, and `object+0x10` is pointed directly at `object+0x42` rather than at the generic interpreter slot.

For IDs `0..138`, selector 0 occurs only for:

| type_id | per-type pointer | retail placements |
|---:|---:|---:|
| 1 | `0x009732` | 0 |
| 10 | `0x0050F0` | 7 |
| 101 | `0x00505A` | 7 |

Types 10 and 101 occur only in scene 14. Type 1 exists in the engine tables but is absent from the recovered retail placement streams.

The direct-code routines for 10 and 101 are related but mirrored/symmetric positional control routines. A gameplay name is intentionally withheld pending behavioral correlation.

## Interpreter entry — CONFIRMED

The generic interpreter begins at `0x011934`.

Its central dispatch sequence reads a word from the type-specific stream and jumps through a table based at `0x011814`:

```text
read next script word
jump (0x011814 + script_word)
```

The table spans `0x011814..0x011933` and contains **72 entries**, each exactly four bytes and each a `BRA.W` stub to a unique handler.

Valid opcode offsets therefore occupy the table in 4-byte increments from `0x0000` through `0x011C`.

### 68000 branch-base correction

For these `BRA.W` stubs, the signed displacement is relative to the PC at the extension word (`stub+2`), not `stub+4`. An earlier exploratory calculation used `+4` and therefore produced handler labels two bytes late. The reproducible probe and the inventory below use the correct `stub + 2 + displacement` formula.

## VM jump-table inventory — CONFIRMED

The 72 dispatch offsets resolve to 72 distinct, instruction-aligned handlers:

```text
0000→11990  0004→1199C  0008→119A8  000C→119B4
0010→119C4  0014→11A5C  0018→11A4E  001C→11A6A
0020→11A72  0024→11BD6  0028→11BE2  002C→11BEC
0030→11BF8  0034→11C02  0038→11C10  003C→11C1C
0040→11C2A  0044→11A7A  0048→11A86  004C→11A90
0050→11A9C  0054→11C36  0058→11C40  005C→11C4A
0060→11C54  0064→11C5E  0068→11C6A  006C→11C76
0070→11ACC  0074→11AD6  0078→11AE0  007C→11AEA
0080→11AA6  0084→11AAE  0088→11AB6  008C→11AC2
0090→11AF4  0094→11AFA  0098→11B1A  009C→11B00
00A0→11B14  00A4→11B20  00A8→11B26  00AC→11B32
00B0→11B48  00B4→11B50  00B8→11B58  00BC→11B60
00C0→11B68  00C4→11B70  00C8→11B80  00CC→11B88
00D0→11B90  00D4→11B9E  00D8→11BAA  00DC→11BB2
00E0→11BBA  00E4→119EC  00E8→11BCE  00EC→11A06
00F0→11A0E  00F4→11A16  00F8→11A1E  00FC→11A26
0100→11A2E  0104→11A36  0108→11A3E  010C→11A46
0110→11944  0114→11964  0118→11988  011C→11B78
```

## VM register model — HIGH CONFIDENCE

Static handler structure shows:

- `A4` is the VM script/program counter.
- `A2` is the opcode jump-table base (`0x11814`).
- `D1` and `D2` are heavily used as VM working registers/accumulators.
- the native 68000 stack is also exposed to the VM by explicit push/pop opcodes.
- engine object/current-context address registers are used by memory-access opcodes; exact stable labels for all of them are still being normalized.

## First opcode semantics — CONFIRMED where stated

The following handlers are instruction-level unambiguous:

| VM offset | Handler | Working semantic |
|---:|---:|---|
| `0x001C` | `0x11A6A` | load immediate word from script into `D2` |
| `0x0020` | `0x11A72` | load immediate long from script into `D2` |
| `0x0080` | `0x11AA6` | load immediate word from script into `D1` |
| `0x0084` | `0x11AAE` | load immediate long from script into `D1` |
| `0x00F0` | `0x11A0E` | push `D2` word |
| `0x00F4` | `0x11A16` | push `D2` long |
| `0x00F8` | `0x11A1E` | pop word into `D2` |
| `0x00FC` | `0x11A26` | pop long into `D2` |
| `0x0100` | `0x11A2E` | push `D1` word |
| `0x0104` | `0x11A36` | push `D1` long |
| `0x0108` | `0x11A3E` | pop word into `D1` |
| `0x010C` | `0x11A46` | pop long into `D1` |

Additional high-confidence opcode families are visible but will remain numerically named until the address-register context is fully proven:

- `0x0024..0x0030`: immediate-address loads into `D2` at byte/word/long widths.
- `0x0034..0x0040`: context/object-relative loads into `D2` using an immediate field offset.
- `0x0054..0x0060`: writes of `D2` through an immediate address.
- `0x0064..0x006C`: context/object-relative writes of `D2` using an immediate field offset.
- `0x0070..0x007C`: writes of `D2` through the address carried in `D1`.
- `0x00B0..0x00DC`: arithmetic/bitwise operations on `D1`/`D2`.
- `0x0090..0x00A4`: comparison/conditional-result control cluster.

## Nature of the VM — HIGH CONFIDENCE

The handlers form a compact general-purpose object scripting machine rather than a fixed enemy-action list. Static instruction patterns show handlers that:

- consume immediate words/longs from the script stream
- move values between VM/engine registers
- load/store through addresses
- perform arithmetic and bit operations
- compare values and produce conditional control flow
- manipulate the script pointer
- perform indirect/native calls
- dispatch immediately to the next script opcode

Opcode offset `0x00EC` targets `0x011A06`; it consumes a word from the script stream as an arithmetic operand and immediately returns to dispatch. Many retail type scripts begin with `0x00EC` followed by a signed-looking word.

Exact symbolic names for all 72 opcodes remain to be recovered. Naming should proceed from handler semantics, not from guesses based on individual enemy appearance.

## Retail type-family consequence

Among `type_id 0..138`, 136 entries select the scripted representation. The two direct-code IDs actually present in retail placements are confined to scene 14.

This means the majority of the game's placed enemies, civilians, pickups, props and interactive objects are likely differentiated primarily through data/scripts interpreted by the same VM, substantially reducing the amount of unique 68000 code that must be reconstructed before authoring new content.

## Common script prefixes

Representative high-frequency placement types show repeated opcode patterns, for example:

```text
type 7:   EC FFF8 84 0000 ... A8 6C 38 ...
type 38:  EC FFF8 84 0000 ... A8 6C 38 ...
type 124: EC FFF8 84 0000 ... A8 6C 38 ...

type 24:  EC FFFE 1C 0000 68 0018 1C 0000 68 001A ...
type 39:  EC FFFE 1C 0000 68 0018 1C 0000 68 001A ...
type 112: EC FFFA 1C 0000 68 0018 1C 0000 68 001A ...
```

These recurring prefixes provide a path to behavioral family clustering before every type has a final gameplay name.

## Next objectives

1. Build a script decoder that recognizes opcode boundaries and operands.
2. Recover exact semantics for the most common VM opcodes first.
3. Cluster the 128 retail placement type IDs by script structure.
4. Cross-correlate type families with animation/sprite descriptors and scene placement to assign gameplay identities.
5. Determine which VM operations install callbacks, AI routines, collision properties, health/damage behavior and spawned child entities.
6. Add an assembler/encoder only after the decoder can round-trip known scripts without ambiguity.
