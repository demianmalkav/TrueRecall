#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "rom_probe"))

from m09c_phase_bridge_analysis import analyze


def snapshot(pc: int, base: int, current: int, record: int, encoded: int) -> dict:
    return {
        "pc": pc,
        "words": {
            "0x1C": base,
            "0x1E": current,
            "0x20": record,
            "0x22": record,
            "0x24": encoded,
            "0x2C": 0x000A,
            "0x2E": 0x0000,
        },
    }


def event(index: int, frame: int, offset: int, name: str, pc: int, base: int, current: int, record: int, encoded: int) -> dict:
    return {
        "event_index": index,
        "script_frame": frame,
        "watch": {"offset": offset, "name": name, "size": 2},
        "snapshot": snapshot(pc, base, current, record, encoded),
    }


def canonical_like_trace() -> dict:
    base = 0x08B6
    events = []
    index = 0
    records = [0x2C08, 0x2C24, 0x2C44, 0x2C64, 0x2C80, 0x2CA0]
    encoded = [0x02AC, 0x02AE, 0x02B0, 0x02B2, 0x02B4, 0x32B6]
    for phase, (record, entry) in enumerate(zip(records, encoded)):
        current = base + phase * 2
        frame = 2107 + phase * 5
        events.append(event(index, frame, 0x1E, "animation_state_1e", 0x009D72, base, current, record, entry)); index += 1
        events.append(event(index, frame, 0x24, "encoded_animation_entry", 0x009D7E, base, current, record, entry)); index += 1
        events.append(event(index, frame, 0x20, "mapping_record_offset", 0x009D88, base, current, record, entry)); index += 1
        events.append(event(index, frame, 0x22, "animation_state_22", 0x011284, base, current, record, entry)); index += 1
    return {
        "schema": "truerecall.m09c.animation_state_trace.v2",
        "base_sha1": "d39174bed46ede85531b86df7ba49123ce2f8411",
        "pre_state": snapshot(0, base, base, 0x0D6E, 0x309E),
        "events": events,
        "descriptor_changed_during_trace": False,
    }


class M09CPhaseBridgeAnalysisStaticTest(unittest.TestCase):
    def test_canonical_bridge_cluster_is_native_progression(self) -> None:
        result = analyze(canonical_like_trace())
        self.assertTrue(result["descriptor_identity_preserved"])
        self.assertEqual(result["native_phase_bridge_count"], 6)
        self.assertEqual(result["observed_native_raw_deltas"], [0, 2, 4, 6, 8, 10])
        self.assertTrue(result["six_phase_cycle_supported"])

    def test_plus24_write_inside_bridge_is_not_reselection(self) -> None:
        result = analyze(canonical_like_trace())
        self.assertTrue(all(row["native_phase_bridge"] for row in result["record_transactions"]))
        self.assertTrue(all(row["encoded_writer_event_index"] is not None for row in result["record_transactions"]))

    def test_state22_is_only_record_mirror_evidence(self) -> None:
        result = analyze(canonical_like_trace())
        self.assertTrue(result["state22_mirrors_record_on_all_observed_events"])
        self.assertTrue(all(row["canonical_mirror_writer"] for row in result["state22_mirror_events"]))

    def test_external_encoded_write_does_not_fake_bridge(self) -> None:
        trace = canonical_like_trace()
        trace["events"][1] = event(1, 2107, 0x24, "encoded_animation_entry", 0x00FDF8, 0x08B6, 0x08B6, 0x2C08, 0x02AC)
        result = analyze(trace)
        self.assertFalse(result["record_transactions"][0]["native_phase_bridge"])
        self.assertEqual(result["native_phase_bridge_count"], 5)

    def test_descriptor_write_fails_identity_gate(self) -> None:
        trace = canonical_like_trace()
        extra = event(len(trace["events"]), 2139, 0x2C, "descriptor_pointer", 0x123456, 0x08B6, 0x08B6, 0x2C08, 0x02AC)
        trace["events"].append(extra)
        result = analyze(trace)
        self.assertFalse(result["descriptor_identity_preserved"])
        self.assertEqual(result["descriptor_write_count"], 1)


if __name__ == "__main__":
    unittest.main()
