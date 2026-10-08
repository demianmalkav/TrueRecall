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

## VM jump-table inventory — CONFIRMED

The 72 dispatch offsets resolve to 72 distinct handlers:

```text
0000→11992  0004→1199E  0008→119AA  000C→119B6
0010→119C6  0014→11A5E  0018→11A50  001C→11A6C
0020→11A74  0024→11BD8  0028→11BE4  002C→11BEE
0030→11BFA  0034→11C04  0038→11C12  003C→11C1E
0040→11C2C  0044→11A7C  0048→11A88  004C→11A92
0050→11A9E  0054→11C38  0058→11C42  005C→11C4C
0060→11C56  0064→11C60  0068→11C6C  006C→11C78
0070→11ACE  0074→11AD8  0078→11AE2  007C→11AEC
0080→11AA8  0084→11AB0  0088→11AB8  008C→11AC4
0090→11AF6  0094→11AFC  0098→11B1C  009C→11B02
00A0→11B16  00A4→11B22  00A8→11B28  00AC→11B34
00B0→11B4A  00B4→11B52  00B8→11B5A  00BC→11B62
00C0→11B6A  00C4→11B72  00C8→11B82  00CC→11B8A
00D0→11B92  00D4→11BA0  00D8→11BAC  00DC→11BB4
00E0→11BBC  00E4→119EE  00E8→11BD0  00EC→11A08
00F0→11A10  00F4→11A18  00F8→11A20  00FC→11A28
0100→11A30  0104→11A38  0108→11A40  010C→11A48
0110→11946  0114→11966  0118→1198A  011C→11B7A
```

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

For example, opcode offset `0x00EC` targets `0x011A08`, consumes a word from the stream into an arithmetic operation, and returns directly to the script dispatcher. Many retail type scripts start with `0x00EC` followed by a signed-looking operand.

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
