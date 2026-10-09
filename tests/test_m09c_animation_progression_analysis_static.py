#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "rom_probe"))

from m09c_animation_progression_analysis import analyze


def snapshot(record: int, encoded: int, pc: int, state22: int = 0) -> dict:
    return {
        "pc": pc,
        "words": {
            "0x20": record,
            "0x22": state22,
            "0x24": encoded,
        },
        "mapping_record_words": [
            "0x0001",
            "0x0002",
            "0x0003",
            "0x0010",
            "0x0020",
            "0x0010",
            "0x0010",
            "0x4002",
        ],
    }


def event(index: int, frame: int, name: str, snap: dict) -> dict:
    return {
        "event_index": index,
        "script_frame": frame,
        "watch": {"name": name},
        "snapshot": snap,
    }


def base_trace(events: list[dict], *, descriptor_changed: bool = False) -> dict:
    return {
        "schema": "truerecall.m09c.animation_state_trace.v1",
        "base_sha1": "synthetic",
        "pre_state": snapshot(0x0200, 0x0300, 0x9999),
        "events": events,
        "descriptor_changed_during_trace": descriptor_changed,
    }


class M09CAnimationProgressionAnalysisStaticTest(unittest.TestCase):
    def test_record_change_without_selection_is_native_progression_candidate(self) -> None:
        trace = base_trace([
            event(0, 2101, "animation_state_22", snapshot(0x0200, 0x0300, 0x1000, 1)),
            event(1, 2102, "mapping_record_offset", snapshot(0x0220, 0x0300, 0x1100, 0)),
        ])
        result = analyze(trace)
        self.assertEqual(result["progression_status"], "native_record_progression_observed")
        self.assertEqual(result["native_record_advance_count"], 1)
        transition = result["native_record_advances"][0]
        self.assertTrue(transition["encoded_stable"])
        self.assertEqual(transition["selection_events_since_previous_record"], 0)
        self.assertTrue(transition["native_progression_candidate"])
        self.assertEqual(result["m09c_gate"]["candidate_progression_writer_pcs"], [0x1100])
        self.assertTrue(result["state22_timer_candidate"])

    def test_intervening_selector_write_blocks_native_progression_claim(self) -> None:
        trace = base_trace([
            event(0, 2101, "encoded_animation_entry", snapshot(0x0200, 0x0302, 0x1200)),
            event(1, 2102, "mapping_record_offset", snapshot(0x0220, 0x0302, 0x1300)),
        ])
        result = analyze(trace)
        self.assertEqual(
            result["progression_status"],
            "record_changes_only_with_selection_or_ambiguous",
        )
        transition = result["record_transitions"][0]
        self.assertFalse(transition["encoded_stable"])
        self.assertEqual(transition["selection_events_since_previous_record"], 1)
        self.assertFalse(transition["native_progression_candidate"])
        self.assertFalse(result["m09c_gate"]["native_progression_evidence"])

    def test_same_value_reselection_still_blocks_native_claim(self) -> None:
        trace = base_trace([
            # The encoded value is unchanged, but a real +0x24 write occurred.
            event(0, 2101, "encoded_animation_entry", snapshot(0x0200, 0x0300, 0x1200)),
            event(1, 2102, "mapping_record_offset", snapshot(0x0220, 0x0300, 0x1300)),
        ])
        result = analyze(trace)
        transition = result["record_transitions"][0]
        self.assertTrue(transition["encoded_stable"])
        self.assertEqual(transition["selection_events_since_previous_record"], 1)
        self.assertFalse(transition["native_progression_candidate"])

    def test_second_record_transition_resets_selection_window(self) -> None:
        trace = base_trace([
            event(0, 2101, "encoded_animation_entry", snapshot(0x0200, 0x0302, 0x1200)),
            event(1, 2102, "mapping_record_offset", snapshot(0x0220, 0x0302, 0x1300)),
            event(2, 2105, "animation_state_22", snapshot(0x0220, 0x0302, 0x1400, 2)),
            event(3, 2106, "mapping_record_offset", snapshot(0x0240, 0x0302, 0x1500, 0)),
        ])
        result = analyze(trace)
        self.assertEqual(result["native_record_advance_count"], 1)
        self.assertEqual(result["native_record_advances"][0]["pc"], 0x1500)
        self.assertEqual(
            result["record_transitions"][1]["selection_events_since_previous_record"],
            0,
        )

    def test_descriptor_write_is_hard_invariant_violation(self) -> None:
        trace = base_trace([
            event(0, 2101, "descriptor_pointer", snapshot(0x0200, 0x0300, 0x1600)),
        ])
        result = analyze(trace)
        self.assertFalse(result["descriptor_invariant_ok"])
        self.assertEqual(result["descriptor_write_count"], 1)
        self.assertFalse(result["m09c_gate"]["descriptor_identity_preserved"])

    def test_trace_level_descriptor_flag_also_fails_invariant(self) -> None:
        result = analyze(base_trace([], descriptor_changed=True))
        self.assertFalse(result["descriptor_invariant_ok"])

    def test_wrong_schema_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            analyze({"schema": "wrong"})


if __name__ == "__main__":
    unittest.main()
