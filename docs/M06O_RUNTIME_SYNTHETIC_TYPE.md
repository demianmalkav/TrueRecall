# M0.6O — Runtime execution of repurposed type 1

M0.6O is the first deterministic runtime proof that a TrueRecall-relocated VM program can affect the running retail engine. A later debugger finding requires a narrower interpretation than the original document claimed.

## Correction discovered after M0.6O

The original M0.6O interpretation assumed `type_id 1` was unused because it has zero persistent retail placements.

Later GDB tracing disproved that assumption: during the first mission the retail engine reaches `Type_Init` with `D0 & 0x03FF == 1` even without an added type-1 placement. Type 1 is therefore **runtime-reachable retail behavior**.

Consequently, M0.6O does **not** prove that the added scene placement caused type 1 to materialize, and it does not prove creation of a new namespace class.

What it *does* prove is still useful: changing type 1 from its retail direct-code representation to our relocated VM program changes live runtime behavior exactly as encoded by that VM program.

## Laboratory build

The build:

- changes retail type 1 from direct-code to VM-scripted representation;
- points it to a relocated script at `0x1FB000`;
- clones the presentation/stat profile of shotgun pickup type 69;
- changes shotgun award from retail `+5` shells to `+6`;
- additionally places type 1 in scene 0 at `(2680,556)`.

Because type 1 is now known to be spawned dynamically by retail logic, the added placement cannot be isolated as the causal source of the observed HUD change.

Build tool: `tools/build/m06o_runtime_visible_type1.py`.

Canonical input SHA-1:

```text
d39174bed46ede85531b86df7ba49123ce2f8411
```

M0.6O output SHA-1:

```text
58fd98253343a4ec86bd0ff67afb698b545b4510
```

## Deterministic runtime harness — CONFIRMED

Runtime validation used:

```text
blastem 1.0.0-6e5677969b59
```

with BlastEm's frame-script facility through the control socket.

Deterministic sequence:

```text
frame 930  pad 1 START down
frame 932  pad 1 START up
frame 1320 pad 1 A down
frame 1322 pad 1 A up
frame 1400 screenshot
```

Observed sequencing:

- frame 930 selects default `New Game`;
- by frame 1270 the first briefing is complete;
- frame 1320 A enters gameplay;
- frame 1400 is inside scene 0 with HUD active.

This sequence is a valid reusable runtime regression primitive for later builds.

## Runtime result — CONFIRMED, causal scope corrected

At frame 1400:

### Retail ROM

- shotgun slot empty;
- no shotgun ammo count.

### M0.6O

- shotgun icon present;
- ammo count `06`.

That matches the semantics of the relocated type-1 VM program.

The safe conclusion is:

```text
retail runtime invokes type 1
→ patched type-table representation resolves to relocated VM program
→ VM executes
→ shotgun ownership/ammo changes
→ live HUD reflects 06 shells
```

The stronger chain previously claimed — specifically `new persistent placement → materialization` — is **not established by M0.6O** and is withdrawn.

## Diagnostic fingerprints

At frame 1400 with BlastEm `1.0.0-6e5677969b59`:

```text
retail full PNG SHA-1: 002c7126165165cde9f2eff8c8b6dd656e223ed6
M0.6O full PNG SHA-1: 30a787020137a14d6bc6e72e6373d18b53a43049
```

HUD crop `(90,203)-(205,235)`, decoded RGB bytes:

```text
retail: d2679780a448d6bbff6d278161c44e16c51e576c
M0.6O:  a1dc52dd90c4503280db6ab8aaf9caf8175155af
```

Copyrighted screenshots remain local and are not committed.

## Engineering consequence

The correction strengthens the project's methodology:

- zero scene placements does not imply an unused type ID;
- namespace availability must include runtime spawn analysis;
- a placement test must use an ID proven absent from retail runtime behavior, or extend the namespace beyond retail tables;
- causality should be demonstrated with a distinct runtime marker/breakpoint or behavior not reachable through pre-existing retail spawns.

The extended-namespace line M0.6P/Q/R exists specifically to solve this stronger problem.

## M0.7 status

M0.6O remains a useful runtime proof of VM relocation/representation replacement, but it is not sufficient for M0.7. Formal M0.7 still requires a genuinely new player state/mechanic+animation or an equivalently novel and causally isolated gameplay extension.
