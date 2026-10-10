from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "build"))

import m120g_l3_objective_build as buildmod

BASE_OVERLAY = ROOT / "tools/build/examples/m120c_l3_three_zone_overlay.json"
PLACEMENT = ROOT / "tools/build/examples/m120g_l3_objective_placement.json"


class M120GL3ObjectiveStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = json.loads(BASE_OVERLAY.read_text(encoding="utf-8"))
        self.placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))

    def test_objective_contract_and_positions_are_pinned(self) -> None:
        self.assertEqual(self.placement["schema"], "truerecall.m120g.objective_placement.v1")
        rows = self.placement["objects"]
        self.assertEqual(
            [(r["type_id"], r["status_flags"], r["stride"], r["x"], r["y"]) for r in rows],
            [(60, "0x7800", 6, 724, 558), (87, "0x7800", 6, 652, 558)],
        )
        self.assertTrue(self.placement["replace_base_objects"])
        self.assertTrue(self.placement["replace_base_world"])
        self.assertEqual(self.placement["world"], [])

    def test_composition_changes_only_production_object_world_domains(self) -> None:
        original = copy.deepcopy(self.base)
        out = buildmod.compose_production_overlay(self.base, self.placement)
        self.assertEqual(self.base, original)
        for key in ("identity", "palette", "maps", "primary_graphics"):
            self.assertEqual(out[key], self.base[key])
        self.assertEqual(out["objects"], self.placement["objects"])
        self.assertEqual(out["world"], [])
        self.assertEqual(out["id"], "m120g_l3_native_objective_production")

    def test_pinned_candidate_fingerprints(self) -> None:
        self.assertEqual(buildmod.EXPECTED_SCENE_SHA1, "cd43a4b53371e4d8329eaa328582ffd64262bddf")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_SHA1, "150373a312283f5c89e5fa00e99f19d7a83bff44")
        self.assertEqual(buildmod.EXPECTED_OUTPUT_CHECKSUM, "0xB7B0")
        self.assertEqual(buildmod.FROZEN_M09D_SHA1, "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021")


if __name__ == "__main__":
    unittest.main()
