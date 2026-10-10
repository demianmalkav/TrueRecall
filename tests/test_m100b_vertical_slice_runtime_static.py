from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools" / "runtime"
sys.path.insert(0, str(RUNTIME))

from m100b_vertical_slice_runtime import ACTIVE_INPUT, evaluate  # noqa: E402


def obj(descriptor: int) -> dict[str, int]:
    return {
        "0x1C": 0x10,
        "0x1E": 0x10,
        "0x20": 0x20,
        "0x22": 0x20,
        "0x24": 0x30,
        "0x2A": 139 if descriptor == 0x000A0000 else 1,
        "0x50": 4,
        "0x6C": 23 if descriptor == 0x000A0000 else 1,
        "descriptor": descriptor,
    }


def fixture(candidate: bool) -> dict:
    xs = [701] + ([688] * 30 if candidate else [700 - min(i * 2, 48) for i in range(1, 31)]) + [688 if candidate else 652]
    samples = []
    for i, x in enumerate(xs):
        step = 0 if i == 0 else (32 if i == len(xs) - 1 else i)
        samples.append(
            {
                "step": step,
                "x": x,
                "y": 558,
                "ownership": 3 if candidate else 1,
                "shotgun_ammo": 5 if candidate else 0,
                "input": 0 if step in (0, 32) else ACTIVE_INPUT,
                "active_count": 6,
            }
        )
    return {
        "before": {
            "scene": 0,
            "f9_address": 0xFFC632,
            "fb_address": 0xFFC86C if candidate else 0xFFC7FA,
            "f9": obj(0x000A0000),
            "fb": obj(0x000F0000),
        },
        "after": {
            "f9_address": 0xFFC632,
            "fb_address": 0xFFC86C if candidate else 0xFFC7FA,
            "f9": obj(0x000A0000),
            "fb": obj(0x000F0000),
        },
        "samples": samples,
    }


class M100BVerticalSliceRuntimeStaticTests(unittest.TestCase):
    def test_expected_parent_candidate_pair_passes(self) -> None:
        result = evaluate(fixture(False), fixture(True))
        self.assertTrue(result["pass"])
        self.assertTrue(all(result["assertions"].values()))

    def test_wrong_candidate_descriptor_fails(self) -> None:
        candidate = fixture(True)
        candidate["before"]["f9"]["descriptor"] = 0x000A0002
        result = evaluate(fixture(False), candidate)
        self.assertFalse(result["pass"])
        self.assertFalse(result["assertions"]["canonical_player_descriptor"])

    def test_missing_shotgun_grant_fails(self) -> None:
        candidate = fixture(True)
        candidate["samples"][0]["ownership"] = 1
        candidate["samples"][0]["shotgun_ammo"] = 0
        result = evaluate(fixture(False), candidate)
        self.assertFalse(result["assertions"]["shotgun_pickup_effect_candidate_only"])

    def test_wall_pass_through_fails(self) -> None:
        candidate = fixture(True)
        for row in candidate["samples"]:
            if row["step"] not in (0,):
                row["x"] = 652
        result = evaluate(fixture(False), candidate)
        self.assertFalse(result["assertions"]["candidate_blocked_by_authored_wall"])

    def test_proxy_address_may_shift_but_semantics_must_not(self) -> None:
        parent = fixture(False)
        candidate = fixture(True)
        self.assertNotEqual(parent["before"]["fb_address"], candidate["before"]["fb_address"])
        self.assertTrue(evaluate(parent, candidate)["assertions"]["proxy_semantics_equal_before"])
        candidate = copy.deepcopy(candidate)
        candidate["before"]["fb"]["0x2A"] = 2
        self.assertFalse(evaluate(parent, candidate)["assertions"]["proxy_semantics_equal_before"])


if __name__ == "__main__":
    unittest.main()
