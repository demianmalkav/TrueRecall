# M0.6F — Scripted repurposing proof for retail type 1

M0.6F is a static proof that TrueRecall can convert an existing retail type-table entry from direct-code representation to VM-scripted representation, relocate source-level VM code and wire that type from another scripted object.

## Important correction discovered during later runtime work

`type_id 1` has **zero recovered persistent scene placements**, but it is **not an unused runtime type**.

Later GDB tracing of the first mission observed the retail engine reaching `Type_Init` with `D0 & 0x03FF == 1` even when no type-1 placement had been added. Therefore retail logic can create/use type 1 dynamically.

The earlier wording “unused slot” was too strong and is withdrawn.

Correct terminology:

```text
type 1 = unplaced retail type / runtime-reachable type
```

not:

```text
type 1 = unused engine slot
```

This distinction matters for Total Recall authoring: zero persistent placements does not prove that a type ID is free for repurposing.

## Retail state

```text
selector[1] = 0             ; direct-code mode
pointer[1]  = 0x009732
persistent retail placements = 0
runtime reachability = CONFIRMED later
```

## Laboratory modification

M0.6F converts type 1 to a scripted VM class using a proven retail source (type 69, shotgun weapon pickup), edited to grant the shotgun plus 6 shells instead of the retail 5-shell amount.

The script is assembled at:

```text
0x1FB000
```

Properties:

- 258 assembled bytes;
- 68 reachable VM instruction addresses;
- located in verified final-FF padding;
- retail type-69 source remains untouched.

## Presentation/stat profile

The laboratory type-1 entry receives the descriptor/stat profile of type 69:

- archetype descriptor 69 → 1;
- HP Normal/Hard 69 → 1;
- damage Normal/Hard 69 → 1;
- type flag byte 69 → 1.

This makes the modified type-1 table entry self-consistent, but it must not be described as a newly allocated namespace ID because the retail engine already uses type 1 dynamically.

## Crate wiring

Supply crate `type_id 113` is source-exported and relocated to `0x1FB200`.

A retail branch that spawns type 68 (shotgun-ammo pickup) is edited to spawn type 1 instead.

The relocated crate script remains 1,062 bytes / 341 reachable instruction addresses. The retail source at `0x17C84A` remains untouched.

## Static validation — CONFIRMED

`tools/build/m06f_synthetic_type1_crate.py` proves:

- canonical ROM identity;
- expected retail type-1 direct-code entry before patching;
- pristine relocation regions;
- selector/pointer conversion to VM script;
- donor archetype/stat profile installation;
- exact VM decode/assembly structure;
- crate relocation and linked spawn argument;
- Genesis checksum regeneration.

Audited build:

```text
checksum     = 0xB7EA
output SHA-1 = 38740c4ea3d3a578dd5b0e14fe61ef8e680c732c
```

The generated ROM is not committed.

## What M0.6F actually proves

```text
existing type-table entry
→ representation conversion direct-code → VM
→ relocated VM source
→ edited semantics
→ explicit presentation/stat profile
→ scripted spawn wiring
→ reproducible checksum-safe build
```

It does **not** prove creation of a previously nonexistent type ID or safe acquisition of a free namespace slot.

That stronger problem is handled by the later extended-namespace experiments (M0.6P and successors).
