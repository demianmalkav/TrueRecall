# M0.6F — New Scripted Object Class Proof

M0.6F is the first static build that introduces a new independently addressable scripted object class instead of only modifying or relocating an existing retail class.

It remains **runtime-unvalidated** because no Genesis emulator is installed in the current execution environment. Therefore it is not promoted to M0.7.

## Chosen engine slot

`type_id 1` exists in the retail engine tables but has zero recovered retail placements.

Retail state:

```text
selector[1] = 0             ; direct-code mode
pointer[1]  = 0x009732
retail placements = 0
```

M0.6F repurposes this unused slot for an isolated laboratory class.

## Synthetic type behavior

A proven retail VM source (type 69, shotgun weapon pickup) is exported and edited so that the new class grants the shotgun plus 6 shells instead of the retail 5-shell amount.

The new script is assembled at:

```text
0x1FB000
```

Properties:

- 258 assembled bytes;
- 68 reachable VM instruction addresses;
- located entirely in the verified final-FF padding region;
- retail type-69 source remains untouched.

## Independent presentation/stat identity

Because generic placement allocation initializes `archetype_id = type_id`, M0.6F supplies archetype 1 with an explicit descriptor/stat profile cloned from the proven type-69 shotgun pickup:

- archetype descriptor pointer copied 69 → 1;
- HP Normal/Hard copied 69 → 1;
- damage Normal/Hard copied 69 → 1;
- type flag byte copied 69 → 1.

Thus type 1 is an independent engine class even though this laboratory proof deliberately reuses a known-safe presentation/stat profile.

## Crate wiring

Supply crate `type_id 113` is itself source-exported and relocated to:

```text
0x1FB200
```

The retail crate has a reachable branch that spawns `type 68` (shotgun-ammo pickup) through `SpawnLinkedObject`.

M0.6F changes exactly that source-level spawn argument:

```text
type 68  →  type 1
```

The relocated crate script remains 1,062 bytes and decodes to 341 reachable instruction addresses.

The original retail crate script at `0x17C84A` remains untouched.

## Engine-table modifications

The generated build performs these intentional structural changes:

```text
type selector 1: direct-code → scripted
pointer type 1:  0x009732 → 0x1FB000
archetype 1 descriptor/stats: cloned from type 69
pointer type 113: retail script → 0x1FB200
```

No original retail object script is overwritten.

## Static validation — CONFIRMED

`tools/build/m06f_synthetic_type1_crate.py` proves on every build:

- canonical input ROM hash and size;
- retail type-1 slot is still the expected unused direct-code slot before patching;
- both relocation regions are pristine `0xFF` padding;
- type 1 becomes scripted and points to `0x1FB000`;
- type 113 points to `0x1FB200`;
- archetype-1 descriptor equals the donor descriptor by explicit patch;
- type-1 script decodes to 68 instructions;
- relocated crate script decodes to 341 instructions;
- the crate source contains exactly one linked spawn of synthetic type 1;
- Genesis checksum is regenerated.

Audited laboratory build:

```text
checksum     = 0xB7EA
output SHA-1 = 38740c4ea3d3a578dd5b0e14fe61ef8e680c732c
```

The generated ROM itself is not committed.

## What M0.6F proves

The project can now perform this entire operation reproducibly:

```text
unused engine type slot
→ scripted representation
→ new VM source block
→ independent type pointer
→ explicit archetype/stat profile
→ spawn from another scripted object
→ relocation into free ROM space
→ checksum repair
→ static structural regression verification
```

This is the first direct proof that the retail type system can be extended into a Total Recall authoring model without replacing an existing placed class.

## Remaining M0.7 gate

Runtime execution still has to be observed in an emulator/on hardware. More importantly, the formal M0.7 target remains a genuinely new player state/mechanic plus animation or an equivalently meaningful new engine behavior, not merely a cloned object behavior in a new slot.
