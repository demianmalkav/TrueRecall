# M0.9C — Native Animation Progression Trace

Status: **TRACE/ANALYSIS PIPELINE IMPLEMENTED / CANONICAL ROM EXECUTION PENDING**

This sub-gate addresses the remaining M09C ambiguity after selector resolution was recovered: what actually advances the selected player's mapping record over time.

## Why this gate exists

`0x00FDDC` is a selector resolver, not by itself a multi-frame sequencer. Its confirmed core writes:

```text
object+0x24  encoded animation entry
object+0x20  mapping-record offset
```

The archetype setter also clears a nearby animation-state cluster:

```text
object+0x1C
object+0x1E
object+0x20
object+0x22
object+0x24
```

The 16-byte mapping record begins with three unresolved control words at `+0x00/+0x02/+0x04` before origin/clip/flags/piece-count data.

M09C must therefore observe the retail runtime relationship among `+0x20`, `+0x22`, `+0x24` and the mapping-record control words before assigning timer/next-frame semantics or designing an authored hook.

## Restored BlastEm automation path

The pinned BlastEm build contains two facilities that can be combined deterministically:

1. `BLASTEM_CTRL_SOCK` control socket;
2. the interactive 68K debugger.

The control socket accepts:

```text
script <absolute-path>
```

and loads the existing KIT absolute-frame script format used by prior runtime milestones:

```text
930 down 1 start
932 up 1 start
...
2100 down 1 left
2100 down 1 y
2142 up 1 y
2142 up 1 left
```

Crucially, the script can be queued while the debugger is paused at reset. A subsequent debugger command:

```text
frames N
```

resumes emulation for an exact number of video frames; during that run the queued KIT script is loaded and applies its absolute-frame actions.

This allows frame-deterministic input and debugger watchpoints to coexist without wall-clock timing.

## Runtime tracer

`tools/runtime/m09c_animation_state_trace.py` implements that combined harness.

Execution flow:

```text
verify canonical ROM SHA-1
→ launch pinned BlastEm under PTY debugger
→ connect BLASTEM_CTRL_SOCK
→ queue KIT navigation/sprint script
→ frames 2099
→ read FFFFF9F8 dynamically
→ read FFFFFB6E dynamically
→ snapshot visual actor state
→ require object+0x2C == 0x0F0000
→ arm animation-state watchpoints
→ run through frame 2142
→ snapshot on every watched write
→ emit JSON evidence
```

The visual object address is never hard-coded. It is resolved from `FFFFF9F8` after gameplay is initialized.

Default watched fields:

```text
object+0x20  mapping record offset
object+0x22  unresolved animation state
object+0x24  encoded animation entry
object+0x2C  descriptor pointer (invariant watch)
```

`--wide-state` additionally watches `+0x1C/+0x1E`.

At every hit the tracer records:

- script frame marker;
- watchpoint identity;
- PC, A6, D0 and D1;
- object state words `+0x1C/+0x1E/+0x20/+0x22/+0x24/+0x2A/+0x2C/+0x50`;
- reconstructed long descriptor pointer;
- current mapping-record address;
- all eight words of the current 16-byte record header;
- the VBlank counter at `FFFFF712`;
- debugger backtrace;
- raw watchpoint hit text.

No retail pixel bytes are exported.

## Frame evidence

The generated KIT script places a `log trace_frame_N` action on every frame from 2099 through 2144. Watchpoint output therefore carries an absolute script-frame anchor without relying on host timing.

The known navigation path remains:

```text
930   Start
1320  A
1500  A
1680  A
1860  A
2040  A
2100  Left + Y down
2142  Y + Left up
```

Watchpoints are armed at frame 2099, before the first Y sprint frame.

## Progression analyzer

`tools/rom_probe/m09c_animation_progression_analysis.py` consumes the trace JSON and separates selection from progression.

Evidence rules:

```text
+0x24 write
    = selection/reselection event

+0x20 write
+ encoded +0x24 value stable
+ no intervening +0x24 watch event
    = native mapping-record progression candidate

+0x22 activity around +0x20 transitions
    = timer/state candidate only; not yet named

+0x2C write
    = M09C descriptor-identity invariant violation
```

The explicit intervening-selection rule prevents a false positive where `+0x24` is written and happens to return to the same numeric value before the next record transition.

The analyzer groups candidate writer PCs by field and returns:

- candidate progression writer PCs;
- candidate `+0x22` writer PCs;
- record-transition frames;
- selection frames;
- mapping-record header words at each transition;
- descriptor invariant result;
- whether native progression has actually been observed.

## Interpretation boundary

Even if `+0x22` changes immediately before every `+0x20` transition, it remains only a timer/state candidate until the canonical trace proves a repeatable relationship.

Likewise, mapping-record control words `+0/+2/+4` remain unnamed until their values correlate with runtime cadence, record transitions or writer code paths.

M09C must prefer measured state transitions over semantic guesses.

## Harness validation

ROM-independent tests cover:

- KIT script construction and exact navigation inputs;
- contiguous trace-frame markers;
- debugger print parsing;
- 32-bit pointer reconstruction from two 16-bit debugger reads;
- 24-bit physical-address projection;
- trace-frame extraction;
- progression classification with and without intervening selector writes;
- same-value reselection rejection;
- descriptor-write invariant failure.

A separate integration test launches the pinned BlastEm build against a synthetic Genesis ROM and exercises the real PTY debugger/control-socket path. The first CI attempt reached the integration stage but failed before emulator startup because Ubuntu lacked `libpulse.so.0`; the workflow now installs the required PulseAudio/ALSA/sample-rate runtime libraries and checks `ldd` for unresolved dependencies before retrying.

## Canonical completion gate

This sub-gate is complete only when the canonical True Lies ROM trace demonstrates all of the following:

1. `FFFFF9F8` resolves to the expected visual actor during the tested gameplay window;
2. `object+0x2C` begins at `0x0F0000` and receives no writes during the trace;
3. actual writer PCs for `+0x20/+0x22/+0x24` are captured;
4. at least one mapping-record transition can be classified as selection-driven or native progression-driven without ambiguity;
5. mapping-record header values are correlated with those transitions;
6. the analysis JSON is persisted before any authored native-sequence hook is designed.

Only after that evidence should M09C choose whether the authored sequence can live entirely in descriptor-native state or requires a minimal progression indirection.
