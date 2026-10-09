# Technical State — TrueRecall

This file is the cumulative technical compendium. It records durable engine knowledge and authoring capabilities. It does **not** choose the current `NEXT`; for continuation always defer to `docs/PROJECT_STATE.md` and `docs/RECOVERY_MANIFEST.json`.

Status vocabulary follows `AGENTS.md`.

## Canonical ROM — CONFIRMED

- Title: `True Lies (World)`
- Size: `2,097,152` bytes
- CRC32: `18C09468`
- MD5: `2fee5ef253faebaff73c017a7bda1cff`
- SHA-1: `d39174bed46ede85531b86df7ba49123ce2f8411`
- Reset entry: `0x00000200`
- System signature: `GENSYSv1.4(May94)`
- Audio signature: `MAXMUS T Bardo 1993 V2.1a` near `0x0134A2`

The original ROM is immutable and never committed. Raw ROM availability is session-local and must be re-established/verified in every fresh context.

## Milestone overview

Completed foundation:

- **M0.1** canonical ROM validation.
- **M0.2** static landmarks / RAM / cheat-correlated seams.
- **M0.3** entity architecture.
- **M0.4** asset/cutscene extraction pipeline.
- **M0.5** gameplay map format.

Completed reconstruction / authoring foundation:

- **M0.6A/B** player input/control architecture and linked player-object model.
- **M0.6C** object stream / VM / archetype / animation / renderer reconstruction.
- **M0.6D/E** controlled VM editing plus source-level relocation/reassembly.
- **M0.6F** new independently addressable scripted type in an unused slot.
- **M0.6G/H** gameplay-map LZBeam relocation and one-tile authored edit.
- **M0.6I/J/K/L** placement replacement/insertion, mixed-stride descriptor regeneration and declarative scene-object compiler.
- **M0.6M** new scripted class placed directly into a persistent level stream.
- later M0.6 runtime probes proved the recovered type/placement path executes under BlastEm.

Runtime extension milestones:

- **M0.7 — COMPLETE:** deterministic BlastEm harness plus held-Y sprint extension with measured movement change and clean inactive fallback.
- **M0.8 — COMPLETE:** 4 MiB expansion plus runtime-visible authored player-local graphics through renderer/cache/VRAM/SAT.

Authoring milestones:

- **M0.9 — ACTIVE / integration-in-progress:** multi-frame compiler, cross-frame chunk deduplication, pixel-exact retail round-trip and stable authored-pixel runtime paths are proven. M0.9C has now recovered the canonical six-phase F9F8 native phase seam; one full-game visual containment/fallback regression remains before completion.
- **M0.10 — substantial authoring foundation complete:** M10A/B runtime-confirmed; M10C–F recover exact broadphase serialization, new-record geometry and declarative world manifests. Genuinely new/moved geometry still requires its own runtime validation before production reliance.
- **M0.11A–D — canonical unified scene-source foundation:** maps + persistent placements + world collision can be represented/compiled transactionally with representative exact no-op proofs. Later M11E–H experiments are preserved on separate branches and do not define the active continuation unless `PROJECT_STATE.md` switches tracks.

The first Total Recall production vertical slice has not started.

## Active continuation pointer

At the reconciliation checkpoint, active work is on:

```text
branch: m09c-native-sequence-seam
milestone: M0.9C
technical checkpoint: e77565bd0a56bc807806f9a91d2e87af70ed89e6
```

Do not treat this pointer as a substitute for `docs/PROJECT_STATE.md`; documentation-only commits advance the live branch HEAD.

## Runtime harness — CONFIRMED

A debug-capable BlastEm build has been controlled through deterministic absolute-frame scripts and an interactive 68K debugger/control socket.

The harness supports:

- booting canonical/generated ROMs;
- deterministic title/briefing navigation;
- six-button input injection;
- exact frame stepping;
- PTY debugger control/watchpoints;
- runtime state capture;
- logical parent/child comparisons.

Representative navigation path:

```text
930   Start
1320  A
1500  A
1680  A
1860  A
2040  A
```

The project-pinned BlastEm binary was restored and is no longer a general blocker. One environment-specific limitation remains: using BlastEm `shot` together with `-g` software rendering hangs. The debugger/control harness is healthy; visual capture for the active M09C gate must use the normal renderer or an external X capture path.

Runtime regression is mandatory for behavior/presentation/collision claims that depend on runtime semantics.

## Player input/control — CONFIRMED

Normalized input globals:

- `F6EA` previous input word — CONFIRMED.
- `F6EC` current input word — CONFIRMED.
- `F6EE` newly pressed edges — CONFIRMED.
- `F6F0` held overlap — CONFIRMED.

Control layering:

```text
normalized input
+ FB7C action/state bits
+ FB7E context/overlay bits
+ event routing
+ synchronized linked player objects
```

M0.7 deliberately uses an unused six-button input rather than replacing a retail action.

## Canonical linked player representation — CONFIRMED

A major M0.9C runtime correction supersedes the earlier pointer/descriptor interpretation.

Retail code loads `FFFFF9F8` and `FFFFFB6E` with `MOVEA.W`; these globals contain signed 16-bit RAM pointers, not adjacent halves of 32-bit pointers.

Observed canonical gameplay values:

```text
FFFFF9F8 -> FFFFC632  world/render avatar
FFFFFB6E -> FFFFC7FA  control/collision proxy
```

During held-Y sprint:

```text
F9F8 object+0x2A = 139
F9F8 object+0x2C = 0x000A0000
```

The descriptor remains stable through the observed native six-phase cycle.

### Superseded interpretation

M0.8 runtime renderer sweeping showed that scoping graphics substitution to `object+0x2C == 0x0F0000` creates a compact player-local visual difference and clean fallback. That proof remains valid as renderer/cache evidence.

It is **falsified** that `0x0F0000` is therefore the F9F8 world/render-avatar descriptor in the canonical tested path. M0.8 now records the narrower correct conclusion.

## Native F9F8 phase bridge — CONFIRMED

The linked-object bridge at `0x009D5E` transfers phase from the control proxy to the F9F8 avatar.

Effective transaction:

```text
phase_delta = proxy(+0x1E) - proxy(+0x1C)
current     = avatar(+0x1C) + phase_delta
avatar(+0x1E) = current
avatar(+0x24) = encoded_entry(avatar_descriptor, current)
avatar(+0x20) = mapping_record(avatar_descriptor, current)
```

Observed writer cluster:

```text
0x009D72  +0x1E
0x009D7E  +0x24
0x009D88  +0x20
0x011284  +0x22 mirror in observed trace
```

The old analytical rule "any +0x24 write = external reselection" is falsified for this cluster. Here `+0x1E -> +0x24 -> +0x20` is one native phase-advance transaction.

Evidence: `extracted_metadata/m09c_canonical_phase_bridge.json`.

## Native six-position sprint cycle — CONFIRMED

Observed F9F8 base phase:

```text
object+0x1C = 0x08B6
```

Cycle:

```text
0x08B6 -> 0x08B8 -> 0x08BA -> 0x08BC -> 0x08BE -> 0x08C0 -> wrap
```

Raw phase deltas:

```text
0, 2, 4, 6, 8, 10
```

Mapping-record cycle:

```text
0x2C08 0x2C24 0x2C44 0x2C64 0x2C80 0x2CA0
```

Encoded-entry cycle:

```text
0x02AC 0x02AE 0x02B0 0x02B2 0x02B4 0x32B6
```

No `+0x2C` write occurs during the observed trace.

## Generic entity architecture — CONFIRMED / HIGH CONFIDENCE

Shared seams:

- `object+0x34` entity↔entity interaction callback — HIGH CONFIDENCE.
- `object+0x38` entity↔world/structure collision callback — HIGH CONFIDENCE.
- `object+0x50` 8-way facing `0..7` — CONFIRMED.
- `object+0x2A` archetype/stat identity — CONFIRMED.
- `object+0x2C` animation/presentation descriptor pointer — CONFIRMED.

Generic pool:

- record size `0x72`;
- 35 records;
- pool base `FFFFF9FE`;
- free-list head `FFFFF9FC`;
- active count `FFFFF9F2`;
- active-list sentinel `FFFFF9F4`;
- allocator `0x00F732`;
- linked allocator `0x00F7CC`;
- destroy/free `0x00F8F8`;
- active-list insertion `0x00FA40`.

The 35-slot pool is a real Total Recall runtime design budget.

## Weapons — CONFIRMED

`FFFFFB8C` is the even-offset selector and `FFFFFB8E` the ownership mask.

| FB8C | Weapon | Own bit | Ammo | Handler |
|---:|---|---:|---|---|
| 0 | Pistol | `0x01` | `FFFFFB70` | `0x008720` |
| 2 | Shotgun | `0x02` | `FFFFFB72` | `0x008968` |
| 4 | Uzi | `0x04` | `FFFFFB74` | `0x008C28` |
| 6 | Grenade | `0x08` | `FFFFFB76` | `0x008FC2` |
| 8 | Mine | `0x10` | `FFFFFB78` | `0x00914A` |
| 10 | Flamethrower | `0x20` | `FFFFFB7A` | `0x008E1C` |

## Persistent scene-object stream — CONFIRMED / AUTHORABLE

All 19 retail scenes parse structurally.

- 2,449 placements.
- 128 placed `type_id`s.
- 1,689 six-byte records.
- 760 eight-byte records.
- Y-sorted spatial materialization.
- descriptor contains count, decoded offsets, compressed source and `(stride,quantity)` runs.

The project can reproducibly decode, replace/remove/add, regenerate mixed strides, LZBeam-encode, relocate, patch scene pointers, repair checksum and reparse generated scenes.

## Object VM — CONFIRMED / AUTHORABLE

Most behavior uses a 72-opcode VM:

- dispatcher `0x011934`;
- opcode table `0x011814–0x011933`;
- representation selector `0x07A33C`;
- type pointer table `0x07953E`.

Assembler/disassembler round-trip covers 136 scripted IDs and 27,818 reachable instruction addresses with exact re-encoding of retail-reached opcodes.

## Semantic catalog / spawn graph — PARTIAL BUT PRODUCTION-USEFUL

Structural coverage: all 128 placed IDs / 2,449 placements.

Persisted semantic state:

- 58 explicitly named identities from mechanical/direct evidence;
- 37 IDs deliberately unresolved at broad authoring-class level rather than guessed visually;
- pickups, objective items, doors, controllers, civilians, ranged actors, spread actors, hazards/destructibles, vehicle/loot props and bosses separated mechanically.

Constant spawn graph:

- 58 parent types with proven children;
- 79 unique parent→child edges;
- 42 runtime-only child types.

## Gameplay map / LZBeam authoring — CONFIRMED

LZBeam decoding and deterministic encoding are implemented. M0.6G/H prove the full decode→edit→encode→relocate→reparse path for gameplay tilemaps.

## Animation / sprite renderer — CONFIRMED / RUNTIME-AUTHORABLE

Mapping pieces are 4 bytes:

```text
byte x_offset
byte y_offset
word graphics/flip id
```

Each piece renders one fixed 16×16 chunk = 128 bytes = four Genesis tiles. The renderer uses a dynamic VRAM chunk cache keyed by `piece_word & 0x3FFF`.

### M0.8 authored graphics proof

A 4 MiB build proves new player-local sprite bytes can flow through renderer/cache/VRAM/SAT during sprint with exact inactive fallback.

```text
output SHA-1 a540621010aa529fc2371f6c7f433f6fa1cafbac
ROM size      4,194,304
checksum      0x934F
raw bank      0x210000
M0.8 scoped visual component 0x0F0000
```

Do not reinterpret the last line as canonical F9F8 identity; see the M0.9C correction above.

## M0.9 sequence authoring — ACTIVE

`tools/build/sprite_sequence_compiler.py` supports multiple source frames and emits one shared raw chunk bank, mapping records, global cross-frame deduplication and cost/working-set metadata.

Pixel-exact retail round-trip on four player frames:

```text
frames                    4
global unique chunks      6
chunk bytes               768
max per-frame working set 2
piece count per frame     2
```

M09B2 proved four authored pixel phases with exact pre/post fallback, but progression came from `F712` and was diagnostic rather than actor-native.

### M0.9C native-phase six-bank build — IMPLEMENTED

Authoritative builder: `tools/build/m09c_native_phase_pixel_sequence.py`.

It uses:

```text
raw_delta = (object+0x1E) - (object+0x1C)
```

for deltas `0,2,4,6,8,10`, scoped to canonical F9F8 descriptor `0x000A0000`.

Banks / cache namespaces:

```text
0 -> 0x210000 / 0x3A00
1 -> 0x218000 / 0x3B00
2 -> 0x220000 / 0x3C00
3 -> 0x228000 / 0x3D00
4 -> 0x230000 / 0x3E00
5 -> 0x238000 / 0x3F00
```

Audited proof build:

```text
size     4,194,304
SHA-1    3256f9dcbc6376624716e3508f41c0439e17cef6
checksum 0x843C
```

Twelve exact 68000 trampoline executions (six source dispatch + six cache-key dispatch) pass under the pinned BlastEm core.

Evidence: `extracted_metadata/m09c_native_phase_trampoline_runtime.json`.

Latest technical CI checkpoint records 42 tests passing with zero failures/errors and debugger/control-socket integration success.

Remaining M09C gate: full-game visual containment/fallback regression using a capture path that does not combine `shot` with BlastEm `-g`.

## M0.10 world collision authoring — SUBSTANTIAL FOUNDATION

World records are ten-byte typed half-open rectangles:

```text
+0x00 world_type
+0x02 x_min
+0x04 y_min
+0x06 x_max
+0x08 y_max
```

### M10A — runtime-confirmed relocation

Scene-0 world resource relocated byte-identically to expanded ROM at `0x230000`; deterministic 13-frame gameplay comparison remained pixel-identical.

### M10B — runtime-confirmed material behavior

- `type 9 -> 11` on a target record allows player pass-through.
- `type 9 -> 10` preserves player blocking while allowing projectiles through.

### M10C — exact broadphase serializer — STATIC CONFIRMED

Dense 64×64-pixel cells point to a deduplicated variable-length list pool. Record membership is half-open rectangle intersection; references are ordered by record offset descending; duplicate membership tuples share a pointer.

Scene 0 retail grid/list pool is reproduced byte-for-byte. A proof moves a wall across cell boundaries and regenerates only affected memberships.

### M10D — new world record — STATIC CONFIRMED

A new type-9 rectangle can be allocated outside the retail record table and indexed through a separately placed list pool without reusing retail geometry.

### M10E — all-scene reconstruction — CONFIRMED

Exact grid + list-pool + membership reconstruction for all 19 scenes.

- 18 scenes derive grid dimensions from gameplay-map dimensions.
- scene 6: `26×55` recovered by record-extent factorization.
- scene 18: valid `9×20` empty layer.

Evidence: `extracted_metadata/world_collision_all_scenes.json`.

### M10F — declarative world manifest — STATIC CONFIRMED

`tools/build/world_collision_manifest.py` exposes stable-ID records with type and rectangle coordinates and supports `add`, `remove`, `replace`.

No-op export→compile exactness: 19/19 scenes.

Scene-18 new-wall proof:

```text
type 9
offset 0x0200
rect (64,64)..(80,256)
affected cells (1,1),(1,2),(1,3)
one shared deduplicated membership list
```

Evidence: `extracted_metadata/m10f_world_manifest.json`.

New/moved geometry still requires its own runtime validation before production reliance.

## M0.11 unified scene authoring — FOUNDATION PRESENT

M11A–D establish transactionally compiled scene state across gameplay maps, persistent objects and world collision.

Canonical v1 scene source includes:

- scene index and immutable scene-level selectors/pointers;
- plane descriptors/dimensions/tile words;
- persistent object prefix + stable IDs/type/status/stride/x/y/param;
- world grid dimensions + stable collision records.

Derived structures such as broadphase membership and object stride runs are regenerated from canonical source rather than hand-edited.

Representative exact no-op canonical source proofs exist for scenes 0, 5, 6 and 18. Later palette/source-v2/transaction-v2 work is preserved on parallel M11 branches.

## Parallel preserved branches

These contain real experimental progress and must not be deleted merely because M09C is active:

```text
m11e-scene-source-matrix
m11f-palette-authoring
m11g-scene-source-v2
m11h-scene-transaction-v2
```

Their continuation is subordinate to `docs/PROJECT_STATE.md`.

## Audio — PARTIAL

Maxmus `T Bardo 1993 V2.1a` is confirmed. Exact 68000↔Z80 command API, sequence encoding and production music/SFX authoring path remain unresolved.

## Known historical/falsified M09C interpretations

Retained for provenance but not current truth:

- F9F8 descriptor `0x0F0000` — FALSIFIED as canonical F9F8 identity.
- reconstructing F9F8/FB6E as adjacent-word 32-bit pointers — FALSIFIED.
- treating every `+0x24` write as external reselection — FALSIFIED for native bridge `0x009D5E`.
- `tools/rom_probe/m09c_canonical_gate.py` as current promotion gate — HISTORICAL.
- JLLBFR@`0x0F0000` visual-roundtrip interpretation as current integration model — HISTORICAL/FALSIFIED.

Current M09C tools are listed in `docs/PROJECT_STATE.md` and `docs/RECOVERY_MANIFEST.json`.

## Production-readiness summary

Already production-useful foundations:

- deterministic base-ROM identity and build verification;
- player input/control seam;
- object/VM/placement authoring;
- LZBeam map authoring;
- sprite compilation and renderer/cache authoring;
- declarative world-collision authoring;
- canonical unified scene source foundation.

Still blocking the first production vertical slice:

- close the M0.9C six-phase full-game visual containment/fallback gate;
- promote diagnostic sprite pixels into deterministic Quaid source frames with budget assertions;
- runtime-validate genuinely new authored geometry on the world-collision path as needed for the chosen slice;
- then freeze an integration baseline before adding story/level production content.
