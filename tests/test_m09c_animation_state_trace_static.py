#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "runtime"))

from m09c_animation_state_trace import (
    POST_FRAME,
    TRACE_ARM_FRAME,
    TRACE_END_FRAME,
    build_input_script,
    combine_words,
    latest_script_frame,
    parse_print_values,
    physical_24,
)


class M09CAnimationStateTraceStaticTest(unittest.TestCase):
    def test_pointer_word_combination_and_24bit_projection(self) -> None:
        self.assertEqual(combine_words(0xFFFF, 0xF9FE), 0xFFFFF9FE)
        self.assertEqual(physical_24(0xFFFFF9FE), 0xFFF9FE)
        self.assertEqual(combine_words(0x000F, 0x0000), 0x000F0000)

    def test_debugger_print_parser(self) -> None:
        text = (
            "print/x [0xFFF9F8] [0xFFF9FA]\r\n"
            "[0xFFF9F8]: FFFF\r\n"
            "[0xFFF9FA]: F9FE\r\n"
            "> "
        )
        self.assertEqual(parse_print_values(text), [0xFFFF, 0xF9FE])

    def test_latest_script_frame(self) -> None:
        text = (
            "KIT SCRIPT frame=2100 at=2100 log trace_frame_2100\n"
            "68K Watchpoint 0 hit, old value: 1, new value 2\n"
            "KIT SCRIPT frame=2101 at=2101 log trace_frame_2101\n"
        )
        self.assertEqual(latest_script_frame(text), 2101)
        self.assertIsNone(latest_script_frame("68K Watchpoint 0 hit"))

    def test_input_script_preserves_known_navigation(self) -> None:
        lines = build_input_script().splitlines()
        for expected in (
            "930 down 1 start",
            "932 up 1 start",
            "1320 down 1 a",
            "1500 down 1 a",
            "1680 down 1 a",
            "1860 down 1 a",
            "2040 down 1 a",
            "2100 down 1 left",
            "2100 down 1 y",
            f"{TRACE_END_FRAME} up 1 y",
            f"{TRACE_END_FRAME} up 1 left",
        ):
            self.assertIn(expected, lines)

    def test_input_script_has_contiguous_trace_frame_markers(self) -> None:
        lines = set(build_input_script().splitlines())
        for frame in range(TRACE_ARM_FRAME, POST_FRAME + 1):
            self.assertIn(f"{frame} log trace_frame_{frame}", lines)

    def test_input_script_has_single_sprint_window(self) -> None:
        lines = build_input_script().splitlines()
        self.assertEqual(lines.count("2100 down 1 y"), 1)
        self.assertEqual(lines.count(f"{TRACE_END_FRAME} up 1 y"), 1)
        self.assertLess(lines.index("2100 down 1 y"), lines.index(f"{TRACE_END_FRAME} up 1 y"))


if __name__ == "__main__":
    unittest.main()
