#!/usr/bin/env python3
"""Deterministic BlastEm trace of native player animation state.

This tool combines two facilities present in the project-pinned BlastEm build:

- the KIT absolute-frame input script loaded through BLASTEM_CTRL_SOCK;
- the interactive 68K debugger driven through a pseudo-terminal.

It navigates to gameplay, resolves the visual player object through FFFFF9F8 at
runtime, verifies its descriptor, installs watchpoints on animation-state words
and records state/header snapshots whenever those words change during held-Y
sprint input.

No ROM bytes or retail sprite pixels are emitted. The JSON result contains RAM
state, PCs, mapping-record headers and debugger evidence only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pty
import re
import select
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

BASE_SIZE = 2_097_152
BASE_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
VISUAL_PLAYER_GLOBAL = 0xFFF9F8
CONTROL_PROXY_GLOBAL = 0xFFFB6E
VBLANK_COUNTER = 0xFFF712
EXPECTED_VISUAL_DESCRIPTOR = 0x0F0000

TRACE_ARM_FRAME = 2099
TRACE_END_FRAME = 2142
POST_FRAME = 2144

WATCH_FIELDS = {
    0x20: "mapping_record_offset",
    0x22: "animation_state_22",
    0x24: "encoded_animation_entry",
    0x2C: "descriptor_pointer",
}
WIDE_WATCH_FIELDS = {
    0x1C: "animation_state_1c",
    0x1E: "animation_state_1e",
    **WATCH_FIELDS,
}

PROMPT = b"> "
WATCH_HIT_RE = re.compile(r"68K Watchpoint\s+(\d+)\s+hit", re.I)
SCRIPT_FRAME_RE = re.compile(r"KIT SCRIPT frame=(\d+) at=(\d+) log trace_frame_(\d+)")
PRINT_VALUE_RE = re.compile(r"^(.+?):\s*([0-9A-Fa-f]+)\s*$")


def verify_rom(raw: bytes) -> None:
    if len(raw) != BASE_SIZE:
        raise ValueError(f"expected 2 MiB canonical base, got {len(raw)} bytes")
    digest = hashlib.sha1(raw).hexdigest()
    if digest != BASE_SHA1:
        raise ValueError(f"wrong base SHA-1: {digest}")


def build_input_script() -> str:
    lines = [
        "930 down 1 start",
        "932 up 1 start",
        "1320 down 1 a",
        "1322 up 1 a",
        "1500 down 1 a",
        "1502 up 1 a",
        "1680 down 1 a",
        "1682 up 1 a",
        "1860 down 1 a",
        "1862 up 1 a",
        "2040 down 1 a",
        "2042 up 1 a",
    ]
    for frame in range(TRACE_ARM_FRAME, POST_FRAME + 1):
        if frame == 2100:
            lines.extend([
                "2100 down 1 left",
                "2100 down 1 y",
            ])
        if frame == TRACE_END_FRAME:
            lines.extend([
                f"{TRACE_END_FRAME} up 1 y",
                f"{TRACE_END_FRAME} up 1 left",
            ])
        lines.append(f"{frame} log trace_frame_{frame}")
    return "\n".join(lines) + "\n"


def combine_words(high: int, low: int) -> int:
    return ((high & 0xFFFF) << 16) | (low & 0xFFFF)


def physical_24(address: int) -> int:
    return address & 0xFFFFFF


def parse_print_values(text: str) -> list[int]:
    values: list[int] = []
    for line in text.replace("\r", "").splitlines():
        match = PRINT_VALUE_RE.match(line.strip())
        if match:
            values.append(int(match.group(2), 16))
    return values


def latest_script_frame(text: str) -> int | None:
    hits = SCRIPT_FRAME_RE.findall(text)
    if not hits:
        return None
    return int(hits[-1][2])


class BlastEmDebugger:
    def __init__(
        self,
        blastem: Path,
        rom: Path,
        work_dir: Path,
        *,
        xvfb: bool,
        timeout: float = 10.0,
    ) -> None:
        self.blastem = blastem
        self.rom = rom
        self.work_dir = work_dir
        self.timeout = timeout
        self.socket_path = work_dir / "blastem-control.sock"
        self.master_fd: int | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.control: socket.socket | None = None
        self.xvfb = xvfb

    def start(self) -> str:
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        master, slave = pty.openpty()
        env = os.environ.copy()
        env["SDL_AUDIODRIVER"] = "dummy"
        env["BLASTEM_CTRL_SOCK"] = str(self.socket_path)
        command = [str(self.blastem), "-g", "-d", str(self.rom)]
        if self.xvfb:
            xvfb_run = shutil.which("xvfb-run")
            if not xvfb_run:
                raise RuntimeError("xvfb-run requested but not installed")
            command = [xvfb_run, "-a", *command]
        self.process = subprocess.Popen(
            command,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            close_fds=True,
        )
        os.close(slave)
        self.master_fd = master
        startup = self.read_until_prompt(self.timeout)
        deadline = time.time() + self.timeout
        while time.time() < deadline and not self.socket_path.exists():
            time.sleep(0.05)
        if not self.socket_path.exists():
            raise RuntimeError("BlastEm control socket did not appear")
        control = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        control.settimeout(self.timeout)
        control.connect(str(self.socket_path))
        self.control = control
        return startup

    def read_until_prompt(self, timeout: float | None = None) -> str:
        if self.master_fd is None:
            raise RuntimeError("debugger not started")
        timeout = self.timeout if timeout is None else timeout
        data = bytearray()
        deadline = time.time() + timeout
        while time.time() < deadline:
            readable, _, _ = select.select([self.master_fd], [], [], 0.1)
            if not readable:
                continue
            try:
                chunk = os.read(self.master_fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            data.extend(chunk)
            if data.endswith(PROMPT):
                return data.decode("utf-8", "replace")
        raise TimeoutError(f"BlastEm debugger prompt timeout; tail={bytes(data[-1000:])!r}")

    def debugger_command(self, command: str, timeout: float | None = None) -> str:
        if self.master_fd is None:
            raise RuntimeError("debugger not started")
        os.write(self.master_fd, (command + "\n").encode("utf-8"))
        if command == "quit":
            return ""
        return self.read_until_prompt(timeout)

    def control_command(self, command: str) -> None:
        if self.control is None:
            raise RuntimeError("control socket not connected")
        self.control.sendall((command + "\n").encode("utf-8"))

    def print_expressions(self, expressions: list[str]) -> list[int]:
        text = self.debugger_command("print/x " + " ".join(expressions))
        values = parse_print_values(text)
        if len(values) != len(expressions):
            raise RuntimeError(
                f"expected {len(expressions)} printed values, got {len(values)}: {text!r}"
            )
        return values

    def close(self) -> None:
        try:
            if self.process is not None and self.process.poll() is None and self.master_fd is not None:
                os.write(self.master_fd, b"quit\n")
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
        finally:
            if self.control is not None:
                self.control.close()
            if self.master_fd is not None:
                try:
                    os.close(self.master_fd)
                except OSError:
                    pass


def read_long_pointer(debugger: BlastEmDebugger, address: int) -> int:
    high, low = debugger.print_expressions(
        [f"[0x{address:06X}]", f"[0x{address + 2:06X}]"],
    )
    return combine_words(high, low)


def read_state_snapshot(debugger: BlastEmDebugger, object_address: int) -> dict[str, Any]:
    obj = physical_24(object_address)
    offsets = [0x1C, 0x1E, 0x20, 0x22, 0x24, 0x2A, 0x2C, 0x2E, 0x50]
    values = debugger.print_expressions([f"[0x{obj + off:06X}]" for off in offsets])
    words = {f"0x{off:02X}": value for off, value in zip(offsets, values)}
    descriptor = combine_words(words["0x2C"], words["0x2E"])
    record_offset = words["0x20"]
    record_address = physical_24(descriptor + record_offset)
    record_words = debugger.print_expressions(
        [f"[0x{record_address + off:06X}]" for off in range(0, 0x10, 2)]
    )
    pc_a6_d0_d1 = debugger.print_expressions(["pc", "a6", "d0", "d1"])
    vblank = debugger.print_expressions([f"[0x{VBLANK_COUNTER:06X}]"])[0]
    return {
        "object_address": object_address,
        "object_physical": obj,
        "words": words,
        "descriptor": descriptor,
        "mapping_record_address": record_address,
        "mapping_record_words": [f"0x{value:04X}" for value in record_words],
        "pc": pc_a6_d0_d1[0],
        "a6": pc_a6_d0_d1[1],
        "d0": pc_a6_d0_d1[2],
        "d1": pc_a6_d0_d1[3],
        "vblank_counter": vblank,
    }


def trace(
    blastem: Path,
    rom: Path,
    *,
    wide_state: bool,
    max_events: int,
    xvfb: bool,
) -> dict[str, Any]:
    raw = rom.read_bytes()
    verify_rom(raw)

    with tempfile.TemporaryDirectory(prefix="truerecall_m09c_") as temp_name:
        temp = Path(temp_name)
        script = temp / "m09c-input.script"
        script.write_text(build_input_script(), encoding="utf-8")

        debugger = BlastEmDebugger(blastem, rom, temp, xvfb=xvfb)
        events: list[dict[str, Any]] = []
        try:
            startup = debugger.start()
            debugger.control_command(f"script {script}")

            # Stop one frame before Y is pressed. This gives us a fully initialized
            # gameplay avatar while ensuring watchpoints are armed before the first
            # sprint input frame.
            pretrace_output = debugger.debugger_command(f"frames {TRACE_ARM_FRAME}", timeout=45)
            observed_frame = latest_script_frame(pretrace_output)
            if observed_frame != TRACE_ARM_FRAME:
                raise RuntimeError(
                    f"input script did not reach trace arm frame: {observed_frame}"
                )

            visual_pointer = read_long_pointer(debugger, VISUAL_PLAYER_GLOBAL)
            proxy_pointer = read_long_pointer(debugger, CONTROL_PROXY_GLOBAL)
            pre_state = read_state_snapshot(debugger, visual_pointer)
            if pre_state["descriptor"] != EXPECTED_VISUAL_DESCRIPTOR:
                raise RuntimeError(
                    f"visual descriptor mismatch: 0x{pre_state['descriptor']:08X}"
                )

            watch_fields = WIDE_WATCH_FIELDS if wide_state else WATCH_FIELDS
            watch_ids: dict[int, dict[str, Any]] = {}
            for offset, name in watch_fields.items():
                size = 4 if offset == 0x2C else 2
                output = debugger.debugger_command(
                    f"watchpoint 0x{physical_24(visual_pointer) + offset:06X} {size}"
                )
                match = re.search(r"68K Watchpoint\s+(\d+)\s+set", output)
                if not match:
                    raise RuntimeError(f"failed to create watchpoint for {name}: {output!r}")
                watch_ids[int(match.group(1))] = {
                    "offset": offset,
                    "name": name,
                    "size": size,
                }

            current_frame = TRACE_ARM_FRAME
            while current_frame < TRACE_END_FRAME and len(events) < max_events:
                remaining = TRACE_END_FRAME - current_frame
                output = debugger.debugger_command(f"frames {remaining}", timeout=45)
                script_frame = latest_script_frame(output)
                if script_frame is not None:
                    current_frame = max(current_frame, script_frame)
                hit = WATCH_HIT_RE.search(output)
                if hit:
                    watch_id = int(hit.group(1))
                    watch = watch_ids.get(watch_id, {"name": "unknown", "offset": None, "size": None})
                    snapshot = read_state_snapshot(debugger, visual_pointer)
                    backtrace = debugger.debugger_command("backtrace")
                    events.append(
                        {
                            "event_index": len(events),
                            "script_frame": current_frame,
                            "watchpoint_id": watch_id,
                            "watch": watch,
                            "hit_output": output,
                            "snapshot": snapshot,
                            "backtrace": backtrace,
                        }
                    )
                    continue

                # No watchpoint interrupted the frame command; it reached the
                # requested end frame normally.
                current_frame = TRACE_END_FRAME

            if len(events) >= max_events and current_frame < TRACE_END_FRAME:
                stop_reason = "max_events"
            else:
                stop_reason = "trace_end_frame"

            final_state = read_state_snapshot(debugger, visual_pointer)
            descriptor_changed = any(
                event["watch"]["offset"] == 0x2C for event in events
            )

            return {
                "schema": "truerecall.m09c.animation_state_trace.v1",
                "base_sha1": BASE_SHA1,
                "frames": {
                    "arm": TRACE_ARM_FRAME,
                    "y_down": 2100,
                    "y_up": TRACE_END_FRAME,
                    "post": POST_FRAME,
                },
                "visual_pointer": visual_pointer,
                "control_proxy_pointer": proxy_pointer,
                "expected_visual_descriptor": EXPECTED_VISUAL_DESCRIPTOR,
                "pre_state": pre_state,
                "watchpoints": watch_ids,
                "event_count": len(events),
                "events": events,
                "final_state": final_state,
                "descriptor_changed_during_trace": descriptor_changed,
                "stop_reason": stop_reason,
                "startup_tail": startup[-2000:],
                "runtime_validation": "animation-state trace only; presentation regression remains separate",
            }
        finally:
            debugger.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--blastem", type=Path, required=True)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--wide-state", action="store_true")
    ap.add_argument("--max-events", type=int, default=256)
    ap.add_argument(
        "--xvfb",
        action="store_true",
        help="run BlastEm through xvfb-run (recommended in headless Linux)",
    )
    args = ap.parse_args()

    report = trace(
        args.blastem,
        args.rom,
        wide_state=args.wide_state,
        max_events=args.max_events,
        xvfb=args.xvfb,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
