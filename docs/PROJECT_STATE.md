# TrueRecall — Authoritative Project State

This is the **single authoritative human-readable continuation state** for TrueRecall. Machine-readable companion: `docs/RECOVERY_MANIFEST.json`. Historical milestone documents and chat transcripts never override `NEXT` here.

## Active continuation

```text
branch:     m09c-native-sequence-seam
milestone:  M1.2A — L3 urban pursuit/subway production slice
checkpoint: c62773ade80792fe575e9f4980ab8f9fd25db665
```

M0.9C is COMPLETE. M0.9D is COMPLETE/FROZEN. M1.0A/B and M1.1A/B/C are COMPLETE. M1.2A remains active until the Level Bible's normal-combat requirement is explicitly proven in the production L3 sequence.

## Canonical ROM

```text
True Lies (World)
size  2,097,152
CRC32 18C09468
MD5   2fee5ef253faebaff73c017a7bda1cff
SHA1  d39174bed46ede85531b86df7ba49123ce2f8411
```

The original ROM is immutable and never committed.

## Frozen contracts

Player M0.9D remains frozen:

```text
source fingerprint da0a060e77f9da835b388ffe94a8090d75cd51ea
build SHA1         49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021
checksum           0x266C
F9F8 descriptor    0x000A0000
native phases      0,2,4,6,8,10
```

M09D supplies the vertical slice's **new Quaid behavior** through the proven sprint path. Do not edit v11 player pixels during M1.2A.

Closed scene-authoring contracts remain stable: scene-source v1/v2/v3, `scene_overlay.v1`, confirmed scene0 primary graphics, collision/object authoring and the M120C safe VRAM-slot contract.

## M120C — three-zone L3 skeleton — CONFIRMED RUNTIME / NOT ART FREEZE

```text
manifest:     tools/build/examples/m120c_l3_three_zone_overlay.json
builder:      tools/build/m120c_l3_three_zone_build.py
candidate:    7bd2144c22074bce5eebdf3e6e15f2f2c7db4ebe
checksum:     0x029E
map rect:     E000 x=0,y=12,w=27,h=11
```

The three readable bands are pursuit entry, objective platform and subway transition. They use only runtime-confirmed primary graphics slots `2..16`; 15/15 payloads are byte-exact in VDP VRAM. Status remains `NOT_ART_FREEZE`.

Evidence: `extracted_metadata/m120c_l3_three_zone_runtime.json`.

## M120G — native subway objective in production layout — COMPLETE / CONFIRMED

M120G preserves the M120C visual skeleton and replaces temporary proof shotgun/wall content with the retail subway objective pair:

```text
type60 lever      x=724 y=558 status=0x7800 stride=6
type87 signal box x=652 y=558 status=0x7800 stride=6
```

Native runtime progression:

```text
ready       FC54=0x0000 FC06=0x0002
lever       FC54=0x4000 FC06=0x003C
signal box  FC54=0x4000 FC06=0x0036
```

No debugger write to FC54 is used.

```text
builder:   tools/build/m120g_l3_objective_build.py
candidate: 150373a312283f5c89e5fa00e99f19d7a83bff44
checksum:  0xB7B0
```

M120G keeps all 15 authored VRAM slots, frozen player/proxy descriptors and full M120C CRAM byte-exact.

Evidence: `extracted_metadata/m120g_l3_production_objective_runtime.json`.

## M120H — scene-specific pursuit pressure — COMPLETE / CONFIRMED

### Trigger seam

Runtime and VM analysis closed a private one-shot latch in type87:

```text
FC54 = mission/objective word
FC56 bit0 = type87 one-shot latch
FC06 = message offset/state
```

All three recovered VM references to `FFFFFC56` are in type87. The successful lever-present branch keeps `FC54=0x4000`, produces message `0x36` and clears `FC56 bit0` from `1 -> 0`; the no-lever branch produces `0x34` and leaves FC56 at `1`.

M120H reuses that exact successful branch rather than adding a global AI subsystem. The retail type87 VM script is relocated from `0x17F2A6` to `0x308000`; immediately after its unique FC56 clear it calls the already-proven `SpawnLinkedObject` native with child type24.

```text
builder:             tools/build/m120h_l3_pursuit_trigger.py
runtime regression:  tools/runtime/m120h_l3_pursuit_runtime.py
M120G parent:        150373a312283f5c89e5fa00e99f19d7a83bff44
M120H candidate:     acfecb2fdb5cc6c55a5c89ae172dd58d8444e1e3
checksum:            0xD0C0
relocated type87 VM: 0x308000
script bytes:        334
reachable VM insns:  89
```

The build differs from M120G only inside the allowed VM relocation window, the type87 pointer-table entry and the Genesis checksum. Frozen player phase banks are unchanged.

### Runtime causal proof

At successful signal-box completion:

```text
active objects: 7 -> 8
new object:     exactly one type24
spawn position: x=651 y=558
descriptor:     0x000CA38C
FC54:           0x4000
FC56:           0
FC06:           0x0036
```

The signal-box interaction temporarily owns control. After the native interaction releases, Quaid reaches x=724 while the spawned type24 advances toward him:

```text
frame 2714  Quaid x=665  type24 x=651
frame 2834  Quaid x=665  type24 x=651
frame 2954  Quaid x=724  type24 x=658
frame 2959  Quaid x=724  type24 x=666
frame 2964  Quaid x=724  type24 x=673
frame 2969  Quaid x=724  type24 x=681
frame 2974  Quaid x=724  type24 x=688
frame 2979  Quaid x=724  type24 x=696
frame 2984  Quaid x=724  type24 x=703
frame 2989  Quaid x=724  type24 x=707
```

This closes **scene-specific pursuit pressure**. Type24 is independently part of the retail standard ranged-fire family, but projectile type170 was not observed in this M120H trigger window; do not overclaim firing here.

Rejected prototypes remain rejected: direct `FireStandardProjectile` before the type87 message disturbed the native interaction; direct firing after its scheduler wait created a zero-useful-velocity projectile that disappeared.

Evidence: `extracted_metadata/m120h_l3_pursuit_runtime.json`.

### M120H CI

```text
technical commit: c62773ade80792fe575e9f4980ab8f9fd25db665
Actions run:      38082267677
static:           PASS
BlastEm harness:  PASS
artifact id:      11681215754
artifact SHA256:  0aba626206fb2070c0a3efd7b67dca559e1f81ea3b5eb822636d2887d15e58bc
```

## Vertical-slice closure audit

The Level Bible requires the first vertical slice to exercise:

```text
normal combat
objectives
new Quaid behavior
at least one custom film-specific subsystem
```

Current evidence matrix:

```text
objectives                    CLOSED — M120G native lever/signal-box progression
new Quaid behavior            CLOSED — frozen M09D sprint
custom film-specific pressure CLOSED — M120H post-objective chase-pressure trigger
normal combat                 OPEN — hostile chase exists, but no production combat exchange has yet been runtime-proven
```

Therefore M1.2A is not declared complete yet. The remaining functional gate is deliberately narrow: prove one normal combat encounter in the same production L3 build without destabilizing M120H.

## FALSIFIED / boundaries

- **FALSIFIED:** retail-unreferenced primary tile indices `565+` are safe production VRAM slots. Use only direct residency evidence or a recovered allocation contract.
- Scene10 remains outside confirmed primary-only v3 graphics scope.
- M120C/G/H environment art is a production skeleton, not final art freeze.
- Type24 pursuit movement is confirmed in M120H; projectile firing in that trigger window is not.
- Do not revive the rejected direct-projectile trigger prototypes.

## OPEN

### O6 — M120I normal combat encounter

Add the smallest production combat encounter that satisfies the Level Bible's normal-combat requirement. Prefer a mechanically confirmed retail hostile/ranged family and prove actual combat activity at runtime — ideally projectile type170 creation or an equally direct damage/combat event. Keep the M120H chase trigger intact.

### O7 — vertical-slice functional freeze

After M120I is green, rerun the integrated objective + pursuit + combat sequence and mechanically preserve the M120C visual resources, M09D Quaid, palette and scene-source contracts. Only then mark the L3 vertical slice functionally complete; art polish can remain a separate non-blocking pass.

## NEXT

1. Inventory scene0-compatible mechanically confirmed hostile families and choose the smallest actor/placement that can demonstrate normal combat without a new AI system.
2. Build an isolated placement/probe on the M120H parent and require actual combat activity rather than visual inference; projectile type170 creation is the preferred discriminator for the standard ranged family.
3. If a candidate fails to engage, reject it after the anti-loop limit and test another already-confirmed retail family rather than altering global AI.
4. Integrate the first green encounter as M120I while preserving the M120G objective and M120H type87-triggered pursuit.
5. Run the final functional closure regression and update this state/manifest; synchronize Drive only after the new checkpoint is green.

## Retry / anti-loop rules

- Maximum two retries for the same failing hypothesis without new evidence.
- Closed M09C/M09D/M1.0/M1.1/M120G/M120H gates reopen only on contradictory evidence.
- Do not edit v11 player pixels during M1.2A.
- Keep scene_source v1/v2/v3 contracts stable; production overlays sit above v3.
- Never infer free VRAM from an unreferenced tilemap index.
- Never commit exported retail scene sources or retail tile dumps.
- Do not assume type1 is unused; runtime disproved that earlier assumption.
- Prefer recovered retail combat primitives over speculative universal AI systems.

## CONTINUATION FOOTER

```text
DONE     M120H closed: type87's private FC56 latch now triggers a single type24 pursuit actor; causal spawn and post-interaction chase movement are runtime-proven; builder/runtime probe/CI are pinned.
EVIDENCE m120h_l3_pursuit_runtime.json + Actions run 38082267677 + artifact 11681215754.
OPEN     one normal-combat encounter remains before the L3 vertical slice can be functionally frozen.
NEXT     build M120I from M120H using a mechanically confirmed retail hostile; prove actual combat activity (preferably projectile170), integrate it without disturbing objective/pursuit/player/visual contracts, then run the functional closure regression.
```
