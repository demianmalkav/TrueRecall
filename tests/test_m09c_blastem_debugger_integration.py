#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS / "runtime"))

from m09c_animation_state_trace import (
    BlastEmDebugger,
    latest_script_frame,
    parse_print_values,
)


def p32(value: int) -> bytes:
    return int(value).to_bytes(4, "big")


def synthetic_genesis_rom(path: Path) -> None:
    """Create a tiny ROM that alternates a RAM word forever.

    0x0200  MOVE.W #$1234,$00FF0000
    0x0208  MOVE.W #$5678,$00FF0000
    0x0210  BRA.S  $0200
    """
    rom = bytearray(0x40000)
    rom[0:4] = p32(0x00FF0000)
    rom[4:8] = p32(0x00000200)
    rom[0x100:0x110] = b"SEGA GENESIS    "
    rom[0x120:0x150] = b"TRUERECALL M09C DEBUG FIXTURE".ljust(0x30, b" ")
    rom[0x150:0x180] = b"TRUERECALL M09C DEBUG FIXTURE".ljust(0x30, b" ")
    rom[0x1A4:0x1A8] = p32(len(rom) - 1)
    rom[0x200:0x212] = bytes.fromhex(
        "33FC123400FF0000"
        "33FC567800FF0000"
        "60EE"
    )
    path.write_bytes(rom)


@unittest.skipUnless(os.environ.get("BLASTEM_BIN"), "BLASTEM_BIN not set")
class M09CBlastEmDebuggerIntegrationTest(unittest.TestCase):
    def test_pty_script_frames_watchpoint_and_memory_read(self) -> None:
        blastem = Path(os.environ["BLASTEM_BIN"])
        self.assertTrue(blastem.is_file(), blastem)

        with tempfile.TemporaryDirectory(prefix="m09c_blastem_ci_") as temp_name:
            temp = Path(temp_name)
            rom = temp / "fixture.bin"
            synthetic_genesis_rom(rom)
            script = temp / "fixture.script"
            script.write_text(
                "1 log trace_frame_1\n"
                "2 down 1 start\n"
                "2 log trace_frame_2\n"
                "3 up 1 start\n"
                "3 log trace_frame_3\n",
                encoding="utf-8",
            )

            debugger = BlastEmDebugger(
                blastem,
                rom,
                temp,
                xvfb=True,
                timeout=20.0,
            )
            try:
                startup = debugger.start()
                self.assertIn("200:", startup)
                self.assertIn("ctrl_sock: listening", startup)

                debugger.control_command(f"script {script}")
                frame_output = debugger.debugger_command("frames 2", timeout=20.0)
                self.assertIn("KIT SCRIPT loaded", frame_output)
                self.assertIn("KIT SCRIPT frame=2 at=2 down 1 start", frame_output)
                self.assertEqual(latest_script_frame(frame_output), 2)

                watch_output = debugger.debugger_command("watchpoint 0xFF0000 2")
                match = re.search(r"68K Watchpoint\s+(\d+)\s+set", watch_output)
                self.assertIsNotNone(match, watch_output)
                watch_id = int(match.group(1))

                hit_output = debugger.debugger_command("frames 1", timeout=20.0)
                self.assertIn(f"68K Watchpoint {watch_id} hit", hit_output)

                values = parse_print_values(
                    debugger.debugger_command("print/x [0xFF0000] pc")
                )
                self.assertEqual(len(values), 2)
                self.assertIn(values[0], (0x1234, 0x5678))
                self.assertIn(values[1], (0x200, 0x208, 0x210))
            finally:
                debugger.close()


if __name__ == "__main__":
    unittest.main()
