# M0.9C — Native Player Sequence Integration Seam

Status: **INVESTIGATION GATE IMPLEMENTED / CANONICAL EXECUTION PENDING**

M09C replaces the diagnostic four-phase M09B2 presentation with authored player animation that advances through the retail animation-selection machinery rather than through a global VBlank phase counter.

The milestone is deliberately constrained by the failure mode observed in the earlier native-sequence experiment: replacing the controlled player's animation descriptor wholesale caused the controlled avatar to become tiny or visually absent while input still worked. M09C therefore treats player descriptor identity and linked-avatar/proxy semantics as invariants, not as disposable implementation details.

## Proven foundations

The player is represented by a synchronized pair:

```text
FFFFF9F8  world/render avatar     HIGH CONFIDENCE
FFFFFB6E  control/collision proxy HIGH CONFIDENCE
```

M08 runtime descriptor sweeping established that renderer/cache substitution scoped to:

```text
object+0x2C == 0x0F0000
```

produces only an avatar-sized visual difference while Y is held and converges exactly after Y release.

That makes `0x0F0000` the **runtime-proven visual-avatar descriptor identity** for the M08/M09B2 path.

Separately, the archetype table entry for archetype `191 / 0xBF` is structurally confirmed as:

```text
0x0E51FE
```

and M09A's historical four-frame retail compiler round-trip used that descriptor.

These two addresses must not be conflated. Until canonical M09C probes reconcile their ownership within the linked player pair, the project treats them as two distinct proven facts:

```text
0x0E51FE  archetype-191 descriptor from static archetype table
0x0F0000  visual-avatar descriptor isolated by runtime renderer sweep
```

## Native resolver — CONFIRMED

The resolver around `0x00FDDC` uses the current object's `+0x2C` descriptor and an animation selector in `D0`.

The confirmed core at `0x00FDEC` performs the equivalent of:

```text
descriptor = object+0x2C
encoded    = word(descriptor + selector)
object+0x24 = encoded
alias       = encoded & 0x0FFE
object+0x20 = word(descriptor + alias)
```

Therefore `object+0x24` retains the encoded animation entry and `object+0x20` becomes the current mapping-record offset consumed by the renderer.

M09C must preserve this state flow wherever possible.

## Presentation-family layer

The object VM already exposes multiple presentation natives:

```text
0x001F9A  direct
0x001FF6  facing_family_set
0x00200C  facing_family_clear
0x002022  direction24_family
0x002448  direction24_family_alt
```

The facing-family natives use the direction table at `0x013F32` and were sufficient to classify initial presentation for 2,427 of 2,449 retail placements.

For the player, established family bases include:

```text
walk:   0x0002 0x0012 0x0022 0x0032 0x0042
idle:   0x0052 0x0062 0x0072 0x0082 0x0092
JLLBFR: 0x00F2
roll:   0x0142
kneel:  0x0172
loss:   0x0262
```

M07C already proved that the retail player control path can select a new direction-table row (`0x1FF0`) while Y is held and then resume the standard caller path. The proof row copied JLLBFR data byte-identically.

## Why M09B2 is not M09C

M09B2 proves authored pixels and stable cache isolation, but its frame progression is external to the actor animation state:

```text
phase = (FFFFF712 >> 2) & 3
```

The VBlank counter selects one of four raw banks and four cache namespaces.

This proves renderer/cache/VRAM/SAT authorability but does not prove authored frames advancing through the actor's native animation state.

M09C must remove that dependency for the authored sequence path.

## Gate 1 — descriptor/family reconciliation

`tools/rom_probe/m09c_native_sequence_seam_probe.py` performs the first canonical gate.

It:

1. verifies the known FDDC resolver signature;
2. verifies archetype 191 resolves to `0x0E51FE`;
3. expands every established player family base through all eight facing entries in the direction table;
4. resolves those selectors independently against `0x0F0000` and `0x0E51FE`;
5. records valid mapping records, header control words, piece counts and record sizes;
6. finds static callers of FDDC, including the presentation-helper region;
7. inventories `0xFF` runs in the `0x0F0000..0x0FFFFF` relative-record window;
8. records absolute long references to `0x0F0000`.

`0xFF` runs are **candidates only**. No gap becomes authoring space merely because it contains filler bytes. Selector-table overlap, group-table overlap, record reachability and reference containment must be checked before allocation.

## Gate 2 — visual-avatar compiler round-trip

`tools/rom_probe/m09c_visual_avatar_roundtrip_probe.py` repeats the M09A compiler proof against the runtime-proven visual descriptor rather than archetype 191.

The initial target family is JLLBFR base `0x00F2`, because M07/M08/M09B2 already use it as the safe alternate player-presentation seam.

The probe:

1. expands the eight facing selectors from `0x013F32 + 0x00F2`;
2. removes duplicate selectors while preserving order;
3. resolves every resulting frame through descriptor `0x0F0000`;
4. reconstructs each retail frame without writing pixel assets to disk;
5. recompiles the sequence with `sprite_sequence_compiler.py`;
6. reconstructs compiled output;
7. requires pixel-exact equality and exact preservation of the 15-byte mapping-record header;
8. emits only structural metrics and hashes;
9. resolves the same selectors against `0x0E51FE` for comparison only.

A failure of the current 16×16 grid-position contract is a real compiler limitation and stops M09C; it must not be hidden with coordinate guessing.

## Candidate integration architecture

The preferred M09C architecture is:

```text
player control / Y sprint state
        ↓
retail direction-family selection
        ↓
reserved authored selector path
        ↓
FDDC-compatible resolution
        ↓
object+0x24 encoded entry
object+0x20 mapping-record offset
        ↓
retail renderer
        ↓
authored chunk source / isolated cache namespace
```

The central invariant is:

```text
object+0x2C remains the runtime visual-avatar descriptor identity
```

M09C should extend selector/record resolution, not swap the object's descriptor pointer.

A direct FDDC hook is acceptable only if it reproduces the retail `+0x24/+0x20` state semantics for the authored selector and falls through byte-identically for all retail selectors. A cleaner descriptor-native unused selector/record path is preferable if the canonical probe proves safe storage exists.

## Storage constraint

FDDC stores a 16-bit mapping-record offset, and the renderer later resolves the current record relative to the object's descriptor. Therefore a truly descriptor-native authored mapping record must be addressable within the descriptor's relative offset model.

M09C must not allocate a record in arbitrary expanded ROM and assume the existing renderer can reach it.

If no safe native record slot exists inside the visual descriptor's reachable window, the milestone must explicitly introduce the smallest possible resolver/renderer indirection while preserving descriptor identity and retail fallback.

## Runtime gate

The eventual M09C runtime build must be compared against the correct logical parent, not blindly against retail.

Required behavior:

- Y clear before activation: pixel-identical to the chosen sprint parent path;
- Y held: differences remain avatar-local;
- authored frame changes follow actor/native animation state, not `F712` phase bits;
- Y release: exact convergence to the parent build;
- movement/control behavior remains the already-proven M07 sprint behavior;
- linked F9F8/FB6E synchronization remains unchanged;
- no descriptor substitution of the controlled player pair;
- cache/VRAM/SAT budgets remain within established assertions.

## Completion criteria

M09C is complete only when:

1. descriptor/family reconciliation is canonical-proven;
2. `0x0F0000` visual-avatar frames round-trip through the sequence compiler;
3. an authored selector/record path is proven non-overlapping and deterministic;
4. FDDC/native animation state drives authored record selection;
5. `object+0x2C` identity is preserved;
6. renderer/cache authored chunks remain isolated to the visual avatar;
7. deterministic BlastEm regression proves clean inactive fallback and native active progression;
8. evidence and output fingerprints are persisted before any vertical-slice art depends on the path.
