# M0.7 — Runtime-Validated Controlled Player Extension

M0.7 closes the runtime gate that remained after the static M0.6 authoring work. It proves that the True Lies player can be extended with a new input-driven behavior while the original game remains runnable under a deterministic emulator harness.

## Behavior under test

A previously unused six-button input, **Y**, is used as an isolated sprint overlay.

The build adds two controlled hooks:

- player animation selection around `0x0083A6`;
- player movement handling around `0x009864`.

When normalized input `F6EC` has the Y bit active (`BTST #5` in the sprint trampoline), the extension:

- selects a dedicated sprint animation row;
- applies larger movement parameters (`0x0300`, `0x0280`) through the existing movement helper path.

When Y is not held, execution falls back to the retail instructions and branches.

## New animation row

The direction/animation table originally rooted around `0x013F32` is relocated into safe expanded space for the experiment. A sprint-only row is added at selector base `0x1FF0`.

The initial runtime proof deliberately uses a byte-identical known-safe retail animation row as the contents of the new selector. This separates two claims:

1. the engine accepts a newly addressable animation row in the extended table;
2. the new state can select it at runtime without destabilizing fallback behavior.

The later M0.8 work replaces this conservative presentation proof with independently authored sprite pixels.

## Deterministic runtime harness

BlastEm is controlled by a frame script and Unix control socket. The navigation sequence reaches gameplay at deterministic frames and then holds `Left + Y` in a fixed window.

Representative sequence:

```text
930   Start
1320  A
1500  A
1680  A
1860  A
2040  A
2100  Left + Y down
2142  Y/Left up
```

Screenshots are captured at the same absolute frame numbers for baseline and modified ROMs.

## Runtime result — CONFIRMED

During the Y-held interval, the sprint build advances the player/camera farther than the retail-equivalent path, proving that the movement extension is executing rather than merely changing static data.

Controlled no-op/relocation variants were also compared in the gameplay region and remained pixel-equivalent where equivalence was expected.

When Y is released, the build returns to the original fallback path.

## What M0.7 proves

The project can now perform and observe this complete runtime operation:

```text
new controller input
→ isolated hook
→ relocated extension code
→ new player behavior
→ new animation selector/row
→ existing engine movement/render path
→ deterministic emulator execution
→ frame-level regression comparison
```

This is the first runtime-validated engine extension and therefore closes the formal M0.7 gate.

## Remaining limitation after M0.7

The animation row itself is structurally new but initially reuses retail-safe graphical content. M0.8 addresses the stronger requirement: independently authored sprite pixel data routed through the retail renderer/VRAM cache and visible only during the new state.
