# M0.6O — Runtime-validated synthetic scripted type

M0.6O is the first TrueRecall build where a newly created scripted object class is not only structurally valid but is observed affecting the running retail engine.

It builds on M0.6F/M0.6M:

- repurpose unused retail `type_id 1` as a scripted VM class;
- clone the safe presentation/stat profile of retail shotgun pickup `type 69`;
- relocate a new VM source block to `0x1FB000`;
- edit the shotgun amount from retail `+5` shells to `+6`;
- place the new class directly into scene 0 at `(2680,556)`.

Build tool: `tools/build/m06o_runtime_visible_type1.py`.

## Static build identity

Canonical input:

```text
True Lies (World)
SHA-1 d39174bed46ede85531b86df7ba49123ce2f8411
```

M0.6O output:

```text
SHA-1 58fd98253343a4ec86bd0ff67afb698b545b4510
```

The generated ROM is not committed.

## Deterministic runtime sequence

Runtime validation used the ulalume BlastEm fork build:

```text
blastem 1.0.0-6e5677969b59
```

The fork's frame-script facility was loaded through the control socket. The relevant input sequence is:

```text
frame 930  pad 1 START down
frame 932  pad 1 START up
frame 1320 pad 1 A down
frame 1322 pad 1 A up
frame 1400 screenshot
```

Observed state:

- frame 930 selects the default `New Game` menu item;
- by frame 1270 the first mission briefing is fully written;
- the A press at frame 1320 enters gameplay;
- frame 1400 is inside scene 0 with the player/HUD active.

The same input frames were executed against the canonical retail ROM and M0.6O.

## Runtime result — CONFIRMED

At frame 1400:

### Retail ROM

- shotgun weapon slot is empty;
- no shotgun-ammo count is displayed in that slot.

### M0.6O

- shotgun weapon icon is present;
- ammo count reads **`06`**.

This is exactly the semantic change encoded by synthetic `type_id 1`.

The result proves the complete runtime chain:

```text
new type-table entry
→ new relocated VM program
→ new persistent scene placement
→ spatial materialization
→ VM execution
→ weapon ownership/ammo mutation
→ live HUD update
```

No retail placed class was replaced to obtain this result.

## Diagnostic screenshot fingerprints

These hashes are environment/frame-specific regression aids, not universal emulator-independent truths.

At frame 1400 with BlastEm `1.0.0-6e5677969b59`:

```text
retail full PNG SHA-1: 002c7126165165cde9f2eff8c8b6dd656e223ed6
M0.6O full PNG SHA-1: 30a787020137a14d6bc6e72e6373d18b53a43049
```

HUD diagnostic crop `(x=90..204, y=203..234)`, decoded RGB bytes:

```text
retail crop SHA-1: d2679780a448d6bbff6d278161c44e16c51e576c
M0.6O crop SHA-1: a1dc52dd90c4503280db6ab8aaf9caf8175155af
```

Copyrighted runtime screenshots remain local and are not committed.

## Milestone interpretation

M0.6O removes the largest uncertainty behind M0.6F–M: the authoring/reinsertion pipeline is not merely statically self-consistent; the retail engine accepts and executes a newly addressable scripted class placed by TrueRecall tooling.

This is a **runtime-validated engine extension**.

However, the project's stricter M0.7 design gate remains intentionally separate: M0.7 should demonstrate a genuinely new player mechanic/state+animation or another comparably novel gameplay behavior, not only a cloned retail behavior with a changed constant.

## Next step

Use the now-proven runtime harness to validate:

1. M0.6H one-tile gameplay-map edit;
2. placement add/remove/replace builds;
3. a deliberately novel object behavior assembled from VM primitives;
4. then the first new player-state/mechanic prototype for formal M0.7.
