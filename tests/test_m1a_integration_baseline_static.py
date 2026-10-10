from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build"
sys.path.insert(0, str(BUILD))

from m1a_integration_baseline import (  # noqa: E402
    CHECKSUM_OFFSET,
    EXPECTED_COMBINED_CHECKSUM,
    EXPECTED_COMBINED_SHA1,
    M09D_V9_SHA1,
    M11D_SCENE18_SHA1,
    diff_ranges,
    intersect_ranges,
)


class M1AIntegrationBaselineStaticTests(unittest.TestCase):
    def test_diff_ranges_collapses_contiguous_bytes_and_ignores_checksum(self) -> None:
        base = bytearray(0x200)
        candidate = bytearray(base)
        candidate[0x10:0x13] = b"abc"
        candidate[0x20] = 1
        candidate[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2] = b"zz"
        self.assertEqual(diff_ranges(bytes(base), bytes(candidate)), [(0x10, 0x13), (0x20, 0x21)])

    def test_range_intersection_detects_real_overlap_only(self) -> None:
        self.assertEqual(intersect_ranges([(0x10, 0x20)], [(0x20, 0x30)]), [])
        self.assertEqual(intersect_ranges([(0x10, 0x21)], [(0x20, 0x30)]), [(0x20, 0x21)])

    def test_frozen_component_and_combined_fingerprints_are_pinned(self) -> None:
        self.assertEqual(M09D_V9_SHA1, "eccbd54596c932ba3d7d2361af2437e59087b853")
        self.assertEqual(M11D_SCENE18_SHA1, "fac81fdc87b76a75c9b590d58707b16fcd6a5f04")
        self.assertEqual(EXPECTED_COMBINED_SHA1, "b96cfb9652a4c5dce7142fe0e03bfb1b257cc474")
        self.assertEqual(EXPECTED_COMBINED_CHECKSUM, "0x5E8B")


if __name__ == "__main__":
    unittest.main()
