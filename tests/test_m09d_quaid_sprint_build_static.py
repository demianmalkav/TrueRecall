from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

from m09c_native_phase_pixel_sequence import BANKS, genesis_checksum  # noqa: E402
from m09d_mapping_constrained_sprite_compiler import compile_banks  # noqa: E402
from m09d_quaid_sprint_build import (  # noqa: E402
    overlay_phase_banks,
    source_fingerprint,
    source_frames,
)

CONTRACT = json.loads(
    (ROOT / "extracted_metadata" / "m09d_quaid_sprint_contract.json").read_text(
        encoding="utf-8"
    )
)
EXPECTED_SOURCE_FINGERPRINT = "16df51a3063eaec999b88ad7d35dd8ba7d4fdb04"
EXPECTED_BANK_SHA1 = [
    "713264ed4ad4f14cc0bd0ea7bf7a498660bd77c7",
    "5270f74e4550626ea36275d11da57cbf70512fc0",
    "3fad55d7310d46347c10b1bcf6b62d48d4bbbcb0",
    "a1f88979ba18ef4957ab8efedf253339b5de489b",
    "e31bafa3d922343a8b29f0bf406d22d8c0f7b4da",
    "ed27b3d7630ae71b8e9dc518a36f1647630edfdb",
]


class M09DQuaidSprintBuildStaticTests(unittest.TestCase):
    def test_source_art_fingerprint_is_deterministic(self) -> None:
        frames = source_frames(CONTRACT)
        digest, rows = source_fingerprint(frames)
        self.assertEqual(digest, EXPECTED_SOURCE_FINGERPRINT)
        self.assertEqual(len(rows), 30)

    def test_mapping_compile_has_stable_phase_bank_fingerprints(self) -> None:
        import hashlib

        frames = source_frames(CONTRACT)
        banks, report = compile_banks(CONTRACT, frames)
        self.assertEqual(
            [hashlib.sha1(bank).hexdigest() for bank in banks], EXPECTED_BANK_SHA1
        )
        self.assertTrue(all(report["assertions"].values()))
        self.assertEqual([p["used_chunk_slots"] for p in report["phases"]], [17] * 6)

    def test_overlay_changes_only_phase_banks_and_header_checksum(self) -> None:
        parent = bytes([0xA5]) * 0x400000
        frames = source_frames(CONTRACT)
        banks, _ = compile_banks(CONTRACT, frames)
        out, checksum = overlay_phase_banks(parent, banks)
        self.assertEqual(len(out), len(parent))
        self.assertEqual(genesis_checksum(out), checksum)

        bank_ranges = [(address, address + 0x8000) for address in BANKS]
        for start, end in bank_ranges:
            self.assertEqual(out[start:end], banks[BANKS.index(start)])

        for start, end in [(0, 0x18E), (0x190, BANKS[0])]:
            self.assertEqual(out[start:end], parent[start:end])
        self.assertEqual(out[0x18E:0x190], checksum.to_bytes(2, "big"))
        self.assertEqual(out[BANKS[-1] + 0x8000 :], parent[BANKS[-1] + 0x8000 :])

    def test_overlay_rejects_wrong_bank_count_and_size(self) -> None:
        parent = bytes(0x400000)
        with self.assertRaisesRegex(ValueError, "expected 6 phase banks"):
            overlay_phase_banks(parent, [bytes(0x8000)] * 5)
        with self.assertRaisesRegex(ValueError, "exactly 0x8000"):
            overlay_phase_banks(parent, [bytes(1)] + [bytes(0x8000)] * 5)


if __name__ == "__main__":
    unittest.main()
