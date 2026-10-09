#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "rom_probe"))
from m09c_canonical_gate import (
    EXPECTED_ARCH191,
    EXPECTED_SHA1,
    EXPECTED_VISUAL,
    NATIVE_SCHEMA,
    VISUAL_SCHEMA,
    validate_reports,
)


def native_fixture() -> dict:
    return {
        "schema": NATIVE_SCHEMA,
        "base_sha1": EXPECTED_SHA1,
        "descriptors": {
            "archetype191": {"address": EXPECTED_ARCH191},
            "runtime_visual_avatar": {"address": EXPECTED_VISUAL},
        },
        "fddc": {"global_callers": [{"pc": 0x1F9A}]},
        "families": {
            "maniac_jllbfr": {
                "base": 0x00F2,
                "all_runtime_visual_valid": True,
            }
        },
        "resolved_record_counts": {
            "runtime_visual": 4,
            "archetype191": 4,
        },
        "runtime_visual_64k_ff_candidates": [
            {"start": 0x0F8000, "end": 0x0F8100, "size": 0x100}
        ],
    }


def visual_fixture() -> dict:
    return {
        "schema": VISUAL_SCHEMA,
        "base_sha1": EXPECTED_SHA1,
        "runtime_visual_descriptor": EXPECTED_VISUAL,
        "comparison_archetype191_descriptor": EXPECTED_ARCH191,
        "facing_family_base": 0x00F2,
        "frame_count": 2,
        "unique_selectors": [2, 0x102],
        "compiled_frames": [
            {"selector": 2, "matches_retail_pixels": True},
            {"selector": 0x102, "matches_retail_pixels": True},
        ],
        "compiler_metadata": {
            "frame_count": 2,
            "global_unique_chunks": 3,
            "max_frame_working_set": 2,
            "max_scanline_pieces": 2,
            "max_scanline_pixels": 32,
        },
        "chunk_bank_bytes": 384,
        "chunk_bank_sha1": "0" * 40,
    }


class M09CCanonicalGateStaticTest(unittest.TestCase):
    def test_valid_reports_promote_only_static_canonical_gates(self) -> None:
        summary = validate_reports(native_fixture(), visual_fixture())
        self.assertTrue(summary["native"]["jllbfr_runtime_visual_valid"])
        self.assertEqual(summary["native"]["fddc_global_callers"], 1)
        self.assertEqual(summary["visual"]["frame_count"], 2)
        self.assertEqual(summary["visual"]["global_unique_chunks"], 3)

    def test_wrong_visual_descriptor_is_rejected(self) -> None:
        native = native_fixture()
        native["descriptors"]["runtime_visual_avatar"]["address"] = 0x0E51FE
        with self.assertRaises(ValueError):
            validate_reports(native, visual_fixture())

    def test_incomplete_jllbfr_family_is_rejected(self) -> None:
        native = native_fixture()
        native["families"]["maniac_jllbfr"]["all_runtime_visual_valid"] = False
        with self.assertRaises(ValueError):
            validate_reports(native, visual_fixture())

    def test_non_pixel_exact_visual_roundtrip_is_rejected(self) -> None:
        visual = visual_fixture()
        visual["compiled_frames"][1]["matches_retail_pixels"] = False
        with self.assertRaises(ValueError):
            validate_reports(native_fixture(), visual)

    def test_selector_count_mismatch_is_rejected(self) -> None:
        visual = visual_fixture()
        visual["unique_selectors"] = [2]
        with self.assertRaises(ValueError):
            validate_reports(native_fixture(), visual)

    def test_base_sha_mismatch_is_rejected(self) -> None:
        visual = copy.deepcopy(visual_fixture())
        visual["base_sha1"] = "f" * 40
        with self.assertRaises(ValueError):
            validate_reports(native_fixture(), visual)


if __name__ == "__main__":
    unittest.main()
