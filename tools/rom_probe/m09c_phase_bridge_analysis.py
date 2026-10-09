#!/usr/bin/env python3
"""Classify canonical M09C animation events using the recovered phase bridge.

The original progression analyzer assumed that a +0x24 write between mapping
records meant a fresh external selection. Canonical tracing disproved that rule:
routine 0x009D5E advances the linked F9F8 avatar by writing, in order,

    0x009D72  object+0x1E  current phase selector
    0x009D7E  object+0x24  encoded descriptor entry
    0x009D88  object+0x20  resolved mapping record

Those three writes are one native progression transaction, not reselection.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TRACE_SCHEMAS = {
    "truerecall.m09c.animation_state_trace.v1",
    "truerecall.m09c.animation_state_trace.v2",
}
ANALYSIS_SCHEMA = "truerecall.m09c.phase_bridge_analysis.v1"

BRIDGE_CURRENT_PC = 0x009D72
BRIDGE_ENCODED_PC = 0x009D7E
BRIDGE_RECORD_PC = 0x009D88
STATE22_MIRROR_PC = 0x011284


def parse_word(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(value)


def event_index(event: dict[str, Any]) -> int:
    return int(event.get("event_index", -1))


def event_frame(event: dict[str, Any]) -> int:
    value = event.get("script_frame")
    return -1 if value is None else int(value)


def event_pc(event: dict[str, Any]) -> int:
    snapshot = event["snapshot"]
    return parse_word(snapshot["pc"])


def watch_offset(event: dict[str, Any]) -> int | None:
    value = event.get("watch", {}).get("offset")
    return None if value is None else int(value)


def state_word(event_or_snapshot: dict[str, Any], offset: int) -> int:
    snapshot = event_or_snapshot.get("snapshot", event_or_snapshot)
    return parse_word(snapshot["words"][f"0x{offset:02X}"])


def _events_between(events: list[dict[str, Any]], start: int, end: int) -> list[dict[str, Any]]:
    return [row for row in events if start < event_index(row) <= end]


def analyze(trace: dict[str, Any]) -> dict[str, Any]:
    if trace.get("schema") not in TRACE_SCHEMAS:
        raise ValueError(f"unsupported trace schema: {trace.get('schema')}")

    events = sorted(list(trace.get("events", [])), key=event_index)
    descriptor_events = [row for row in events if watch_offset(row) == 0x2C]
    descriptor_invariant_ok = not descriptor_events and not trace.get(
        "descriptor_changed_during_trace", False
    )

    by_offset: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in events:
        offset = watch_offset(row)
        if offset is not None:
            by_offset[offset].append(row)

    record_events = by_offset.get(0x20, [])
    bridge_transactions: list[dict[str, Any]] = []
    previous_record_event_index = -1
    previous_record = state_word(trace["pre_state"], 0x20) if trace.get("pre_state") else None

    for record_event in record_events:
        idx = event_index(record_event)
        window = _events_between(events, previous_record_event_index, idx)
        current_writes = [row for row in window if watch_offset(row) == 0x1E and event_pc(row) == BRIDGE_CURRENT_PC]
        encoded_writes = [row for row in window if watch_offset(row) == 0x24 and event_pc(row) == BRIDGE_ENCODED_PC]
        record_is_bridge = event_pc(record_event) == BRIDGE_RECORD_PC

        ordered_bridge = bool(
            record_is_bridge
            and current_writes
            and encoded_writes
            and event_index(current_writes[-1]) < event_index(encoded_writes[-1]) < idx
        )

        after_record = state_word(record_event, 0x20)
        base_1c = state_word(record_event, 0x1C)
        current_1e = state_word(record_event, 0x1E)
        raw_delta = (current_1e - base_1c) & 0xFFFF
        encoded = state_word(record_event, 0x24)

        bridge_transactions.append({
            "record_event_index": idx,
            "frame": event_frame(record_event),
            "record_writer_pc": event_pc(record_event),
            "record_before": previous_record,
            "record_after": after_record,
            "base_1c": base_1c,
            "current_1e": current_1e,
            "raw_phase_delta": raw_delta,
            "encoded_24": encoded,
            "current_writer_event_index": event_index(current_writes[-1]) if current_writes else None,
            "encoded_writer_event_index": event_index(encoded_writes[-1]) if encoded_writes else None,
            "native_phase_bridge": ordered_bridge and previous_record != after_record,
        })
        previous_record = after_record
        previous_record_event_index = idx

    native = [row for row in bridge_transactions if row["native_phase_bridge"]]

    state22_events = by_offset.get(0x22, [])
    mirror_events = []
    for row in state22_events:
        mirror_events.append({
            "event_index": event_index(row),
            "frame": event_frame(row),
            "pc": event_pc(row),
            "value_22": state_word(row, 0x22),
            "value_20": state_word(row, 0x20),
            "matches_record": state_word(row, 0x22) == state_word(row, 0x20),
            "canonical_mirror_writer": event_pc(row) == STATE22_MIRROR_PC,
        })

    writer_counts = Counter((watch_offset(row), event_pc(row)) for row in events)
    writer_matrix = [
        {"offset": offset, "pc": pc, "count": count}
        for (offset, pc), count in sorted(writer_counts.items())
    ]

    observed_deltas = [row["raw_phase_delta"] for row in native]
    canonical_six_phase_values = {0, 2, 4, 6, 8, 10}
    six_phase_cycle_supported = canonical_six_phase_values.issubset(set(observed_deltas))

    return {
        "schema": ANALYSIS_SCHEMA,
        "base_sha1": trace.get("base_sha1"),
        "trace_schema": trace.get("schema"),
        "trace_event_count": len(events),
        "descriptor_identity_preserved": descriptor_invariant_ok,
        "descriptor_write_count": len(descriptor_events),
        "bridge_writer_pcs": {
            "current_1e": BRIDGE_CURRENT_PC,
            "encoded_24": BRIDGE_ENCODED_PC,
            "record_20": BRIDGE_RECORD_PC,
        },
        "record_transactions": bridge_transactions,
        "native_phase_bridge_count": len(native),
        "native_phase_bridges": native,
        "observed_native_raw_deltas": observed_deltas,
        "six_phase_cycle_supported": six_phase_cycle_supported,
        "state22_mirror_events": mirror_events,
        "state22_mirrors_record_on_all_observed_events": bool(mirror_events) and all(
            row["matches_record"] for row in mirror_events
        ),
        "writer_matrix": writer_matrix,
        "m09c_gate": {
            "descriptor_identity_preserved": descriptor_invariant_ok,
            "native_phase_bridge_observed": bool(native),
            "six_phase_cycle_supported": six_phase_cycle_supported,
            "phase_source": "((object+0x1E)-(object+0x1C)) >> 1",
        },
        "semantic_policy": (
            "A 0x9D7E write to +0x24 inside the 0x9D72->0x9D7E->0x9D88 cluster "
            "is part of native progression, not evidence of external reselection. "
            "+0x22 is classified only as a record mirror for this trace."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    result = analyze(json.loads(args.trace.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
