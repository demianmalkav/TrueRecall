# Audio System

## Confirmed anchor

The ROM contains the signature:

`MAXMUS T Bardo 1993 V2.1a`

at approximately `0x0134A2`.

This identifies the Beam Software Maxmus driver family used by the game.

## Current status

- Driver family: CONFIRMED.
- Signature location: CONFIRMED.
- Exact 68000 command API: UNRESOLVED.
- Z80 payload boundaries: UNRESOLVED.
- Music sequence format: UNRESOLVED.
- SFX table / instrument table: UNRESOLVED.

## Research strategy

1. Trace 68000 writes to Z80/bus-request hardware during music/SFX events.
2. Delimit Maxmus loader and Z80 driver image.
3. Compare behavior/signatures against other Beam titles using the same `T Bardo 1993 V2.1a` family.
4. Name play/stop/SFX/parameter commands only after dynamic proof.
5. Preserve the original driver initially; replace only if Total Recall requirements cannot be supported cleanly.
