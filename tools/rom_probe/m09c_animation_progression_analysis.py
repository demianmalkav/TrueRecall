#!/usr/bin/env python3
"""Analyze M09C animation-state traces into progression evidence.

The runtime tracer records writes to the visual avatar's animation-state cluster.
This analyzer separates selection from progression:

- object+0x24 changing means the encoded animation entry/selection changed;
- object+0x20 changing with no intervening +0x24 write is evidence that the
  current mapping record advanced without a fresh FDDC-style selection;
- object+0x22 activity around +0x20 transitions is a timer/state candidate;
- any object+0x2C write violates the M09C descriptor-identity invariant.

The output is evidence classification only. It does not assign semantic names to
control words +0/+2/+4 unless runtime correlation supports them.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TRACE_SCHEMA = "truerecall.m09c.animation_state_trace.v1"
ANALYSIS_SCHEMA = "truerecall.m09c.animation_progression_analysis.v1"


def parse_word(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(value)


def state_word(snapshot: dict[str, Any], offset: int) -> int:
    return parse_word(snapshot["words"][f"0x{offset:02X}"])


def event_pc(event: dict[str, Any]) -> int:
    return parse_word(event["snapshot"]["pc"])


def event_frame(event: dict[str, Any]) -> int:
    value = event.get("script_frame")
    return -1 if value is None else int(value)


def event_index(event: dict[str, Any]) -> int:
    value = event.get("event_index")
    return -1 if value is None else int(value)


def analyze(trace: dict[str, Any]) -> dict[str, Any]:
    if trace.get("schema") != TRACE_SCHEMA:
        raise ValueError("unsupported M09C trace schema")

    events = sorted(
        list(trace.get("events", [])),
        key=lambda row: (event_index(row), event_frame(row)),
    )
    by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        name = event.get("watch", {}).get("name", "unknown")
        by_field[name].append(event)

    descriptor_events = by_field.get("descriptor_pointer", [])
    descriptor_invariant_ok = not descriptor_events and not trace.get(
        "descriptor_changed_during_trace", False
    )

    writer_pcs: dict[str, list[dict[str, Any]]] = {}
    for field, rows in sorted(by_field.items()):
        counts = Counter(event_pc(row) for row in rows)
        writer_pcs[field] = [
            {"pc": pc, "count": count}
            for pc, count in counts.most_common()
        ]

    record_events = by_field.get("mapping_record_offset", [])
    encoded_events = by_field.get("encoded_animation_entry", [])
    state22_events = by_field.get("animation_state_22", [])

    record_transitions = []
    previous_record_snapshot = trace.get("pre_state")
    previous_record_event_index = -1
    for event in record_events:
        current = event["snapshot"]
        current_index = event_index(event)
        before_record = (
            None
            if previous_record_snapshot is None
            else state_word(previous_record_snapshot, 0x20)
        )
        before_encoded = (
            None
            if previous_record_snapshot is None
            else state_word(previous_record_snapshot, 0x24)
        )
        after_record = state_word(current, 0x20)
        after_encoded = state_word(current, 0x24)
        intervening_selection_events = [
            row
            for row in encoded_events
            if previous_record_event_index < event_index(row) < current_index
        ]
        transition = {
            "event_index": current_index,
            "frame": event_frame(event),
            "pc": event_pc(event),
            "record_before": before_record,
            "record_after": after_record,
            "encoded_before": before_encoded,
            "encoded_after": after_encoded,
            "encoded_stable": before_encoded == after_encoded,
            "record_changed": before_record != after_record,
            "selection_events_since_previous_record": len(intervening_selection_events),
            "selection_event_indices_since_previous_record": [
                event_index(row) for row in intervening_selection_events
            ],
            "record_header_words": list(current.get("mapping_record_words", [])),
        }
        transition["native_progression_candidate"] = bool(
            transition["record_changed"]
            and transition["encoded_stable"]
            and transition["selection_events_since_previous_record"] == 0
        )
        record_transitions.append(transition)
        previous_record_snapshot = current
        previous_record_event_index = current_index

    native_record_advances = [
        row for row in record_transitions if row["native_progression_candidate"]
    ]

    state22_frames = [event_frame(row) for row in state22_events]
    for transition in record_transitions:
        frame = transition["frame"]
        transition["state22_events_same_or_previous_frame"] = sum(
            1 for candidate in state22_frames if candidate in (frame - 1, frame)
        )

    selection_frames = [event_frame(row) for row in encoded_events]
    record_frames = [row["frame"] for row in record_transitions]

    if native_record_advances:
        progression_status = "native_record_progression_observed"
    elif record_transitions:
        progression_status = "record_changes_only_with_selection_or_ambiguous"
    else:
        progression_status = "no_record_progression_observed"

    timer_candidate = bool(state22_events and record_transitions)

    return {
        "schema": ANALYSIS_SCHEMA,
        "base_sha1": trace.get("base_sha1"),
        "trace_event_count": len(events),
        "descriptor_invariant_ok": descriptor_invariant_ok,
        "descriptor_write_count": len(descriptor_events),
        "field_event_counts": {
            field: len(rows) for field, rows in sorted(by_field.items())
        },
        "writer_pcs": writer_pcs,
        "record_transitions": record_transitions,
        "native_record_advance_count": len(native_record_advances),
        "native_record_advances": native_record_advances,
        "encoded_selection_frames": selection_frames,
        "mapping_record_frames": record_frames,
        "state22_frames": state22_frames,
        "state22_timer_candidate": timer_candidate,
        "progression_status": progression_status,
        "m09c_gate": {
            "descriptor_identity_preserved": descriptor_invariant_ok,
            "native_progression_evidence": bool(native_record_advances),
            "candidate_progression_writer_pcs": sorted(
                {row["pc"] for row in native_record_advances}
            ),
            "candidate_state22_writer_pcs": sorted(
                {event_pc(row) for row in state22_events}
            ),
        },
        "semantic_policy": (
            "Do not name record control words or object+0x22 as timer/next-frame "
            "state until canonical trace correlation establishes that behavior."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("trace", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    result = analyze(trace)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
