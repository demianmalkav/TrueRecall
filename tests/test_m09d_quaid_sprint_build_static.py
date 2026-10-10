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
EXPECTED_SOURCE_FINGERPRINT = "da0a060e77f9da835b388ffe94a8090d75cd51ea"
EXPECTED_BANK_SHA1 = [
    "97a9f024374b75810dd060ff8c03b4b703cd7ab6",
    "fce14e16bc2325ea603f7ad973a0033c56f68098",
    "38c2f905c4f05cc01938f440f2e7cd8a9fa28d74",
    "12fd0abb168d4983fc3b6d2d46a4589317c8f6c2",
    "0cd1b90c15c55504e2e55e992197022a5856204f",
    "416007b12132f06ff30fa009649e4b1c6379d5c1",
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
