# M0.6D — Controlled Data Patch

M0.6D is a laboratory milestone proving that the project can generate a deterministic, minimal gameplay modification from the canonical ROM without hand-editing an authoritative binary.

It is **not** M0.7. It changes an existing data constant rather than adding a new state/mechanic.

## Experiment

Change the shotgun weapon pickup's initial shell grant from `5` to `6`.

Retail VM-script byte:

```text
ROM 0x1762C1: 0x05 → 0x06
```

The surrounding script belongs to `type_id 69`, the confirmed shotgun-weapon pickup.

## Sega checksum

The Mega Drive header checksum is stored at `0x018E..0x018F` and equals the 16-bit sum of big-endian words from ROM `0x0200` to end.

Canonical ROM:

```text
checksum = 0x5DDA
```

After the one-byte gameplay change:

```text
checksum = 0x5DDB
```

Therefore the generated ROM differs from the canonical base at exactly two byte positions:

```text
0x00018F: DA → DB   checksum low byte
0x1762C1: 05 → 06   shotgun pickup shell grant
```

## Reproducibility — CONFIRMED

`tools/build/m06d_shotgun_patch.py`:

1. requires the canonical ROM size and SHA-1;
2. asserts the expected retail byte at `0x1762C1`;
3. applies the requested amount;
4. recomputes the Sega checksum;
5. writes a new output file without touching the base ROM.

With `--amount 6` it reproduces the audited laboratory binary byte-for-byte:

```text
output SHA-1 = ff1f6fa5fe3815c6e3bf093ffd5e5431f2251469
```

The generated ROM itself is not committed to GitHub.

## What this proves

- Base-ROM identity enforcement works.
- A gameplay parameter can be changed deterministically.
- The output ROM can be reproduced exactly from source-controlled transformation logic.
- Header checksum repair is understood.
- The modification is reversible and has an exact two-byte diff including checksum.

## What this does not prove

- no new object type is added;
- no VM script is relocated in the generated ROM;
- no new player state exists;
- no runtime regression/playtest has yet been recorded as part of this document.

Those belong to later milestones.
