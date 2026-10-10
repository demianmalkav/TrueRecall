#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import pty
import re
import select
import subprocess
import time
from pathlib import Path
from typing import Any

EXPECTED_PARENT_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_CANDIDATE_SHA1 = "84d3baf0fad9aaf5cf68f1d10c4afe3f003f3027"
EXPECTED_BLASTEM_SHA256 = "b511890bd1cd6616050e8b009aa9bf1d5d791a326682d3da76d9524467dfb0d2"
PROMPT = b"> "
ACTIVE_INPUT = 0x2044  # normalized Y + Left

SEMANTIC_OFFSETS = (0x1C, 0x1E, 0x20, 0x22, 0x24, 0x2A, 0x50, 0x6C)


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ram_pointer(word: int) -> int:
    return (0xFF0000 | (word & 0xFFFF)) if word & 0x8000 else word & 0xFFFF


class BlastEmSession:
    def __init__(self, blastem: Path, rom: Path, display: str):
        self.blastem = blastem
        self.rom = rom
        self.display = display
        self.package = blastem.parent
        self.xvfb: subprocess.Popen[bytes] | None = None
        self.proc: subprocess.Popen[bytes] | None = None
        self.master: int | None = None
        self.cur = 0
        self.x11 = ctypes.CDLL("libX11.so.6")
        self.xtst = ctypes.CDLL("libXtst.so.6")
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x11.XStringToKeysym.restype = ctypes.c_ulong
        self.x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XKeysymToKeycode.restype = ctypes.c_uint
        self.xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.x11.XFlush.argtypes = [ctypes.c_void_p]
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]

    def __enter__(self):
        self.xvfb = subprocess.Popen(
            ["Xvfb", self.display, "-screen", "0", "1280x960x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.2)
        master, slave = pty.openpty()
        env = os.environ.copy()
        env.update(
            DISPLAY=self.display,
            SDL_AUDIODRIVER="dummy",
            LD_LIBRARY_PATH=str(self.package / "lib"),
        )
        self.proc = subprocess.Popen(
            [str(self.blastem), "-d", str(self.rom)],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=self.package,
            env=env,
            close_fds=True,
        )
        os.close(slave)
        self.master = master
        self.read_prompt(20)
        self.key("4", True)
        self.key("4", False)
        return self

    def __exit__(self, exc_type, exc, tb):
        for name in ("Left", "w"):
            try:
                self.key(name, False)
            except Exception:
                pass
        if self.proc is not None:
            self.proc.terminate()
        if self.xvfb is not None:
            self.xvfb.terminate()
        if self.master is not None:
            os.close(self.master)

    def read_prompt(self, timeout: float = 15) -> str:
        assert self.master is not None and self.proc is not None
        data = b""
        end = time.time() + timeout
        while time.time() < end:
            if self.proc.poll() is not None:
                raise RuntimeError(f"BlastEm exited {self.proc.returncode}: {data[-2000:]!r}")
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if ready:
                data += os.read(self.master, 65536)
                if data.endswith(PROMPT):
                    return data.decode(errors="replace")
        raise TimeoutError(data[-2500:])

    def command(self, text: str, timeout: float = 15) -> str:
        assert self.master is not None
        os.write(self.master, (text + "\n").encode())
        return self.read_prompt(timeout)

    def values(self, expressions: list[str]) -> list[int]:
        output = self.command("print/x " + " ".join(expressions))
        values = [int(value, 16) for value in re.findall(r":\s*([0-9a-fA-F]+)\s*$", output, re.M)]
        if len(values) != len(expressions):
            raise RuntimeError((expressions, output, values))
        return values

    def key(self, name: str, down: bool) -> None:
        display = self.x11.XOpenDisplay(self.display.encode())
        if not display:
            raise RuntimeError("cannot open X display")
        try:
            keysym = self.x11.XStringToKeysym(name.encode())
            keycode = self.x11.XKeysymToKeycode(display, keysym)
            self.xtst.XTestFakeKeyEvent(display, keycode, 1 if down else 0, 0)
            self.x11.XFlush(display)
        finally:
            self.x11.XCloseDisplay(display)

    def go(self, frame: int) -> None:
        if frame > self.cur:
            self.command(f"frames {frame - self.cur}", 30)
            self.cur = frame

    def navigate_scene0(self) -> None:
        for frame, key in ((930, "Return"), (1320, "a"), (1500, "a"), (1680, "a"), (1860, "a"), (2040, "a")):
            self.go(frame)
            self.key(key, True)
            self.go(frame + 2)
            self.key(key, False)
        self.go(2200)

    def object_snapshot(self, address: int) -> dict[str, int]:
        offsets = (0x10, 0x14) + SEMANTIC_OFFSETS + (0x2C, 0x2E)
        vals = self.values([f"[0x{address + off:06X}]" for off in offsets])
        row = {f"0x{off:02X}": value for off, value in zip(offsets, vals)}
        row["descriptor"] = (row["0x2C"] << 16) | row["0x2E"]
        return row

    def sample(self, step: int, f9: int) -> dict[str, int]:
        x, y, ownership, ammo, current_input, active_count = self.values(
            [
                f"[0x{f9 + 0x10:06X}]",
                f"[0x{f9 + 0x14:06X}]",
                "[0xFFFB8E]",
                "[0xFFFB72]",
                "[0xFFF6EC]",
                "[0xFFF9F2]",
            ]
        )
        return {
            "step": step,
            "x": x,
            "y": y,
            "ownership": ownership,
            "shotgun_ammo": ammo,
            "input": current_input,
            "active_count": active_count,
        }

    def run_probe(self) -> dict[str, Any]:
        self.navigate_scene0()
        scene, f9word, fbword = self.values(["[0xFFFC42]", "[0xFFF9F8]", "[0xFFFB6E]"])
        f9 = ram_pointer(f9word)
        fb = ram_pointer(fbword)
        before = {
            "scene": scene,
            "f9_address": f9,
            "fb_address": fb,
            "f9": self.object_snapshot(f9),
            "fb": self.object_snapshot(fb),
        }
        samples = [self.sample(0, f9)]
        self.key("Left", True)
        self.key("w", True)
        for step in range(1, 31):
            self.command("frames 1")
            samples.append(self.sample(step, f9))
        self.key("Left", False)
        self.key("w", False)
        self.command("frames 2")
        samples.append(self.sample(32, f9))
        f9_after = ram_pointer(self.values(["[0xFFF9F8]"])[0])
        fb_after = ram_pointer(self.values(["[0xFFFB6E]"])[0])
        after = {
            "f9_address": f9_after,
            "fb_address": fb_after,
            "f9": self.object_snapshot(f9_after),
            "fb": self.object_snapshot(fb_after),
        }
        return {"before": before, "after": after, "samples": samples}


def semantic_object(row: dict[str, int]) -> dict[str, int]:
    keys = [f"0x{off:02X}" for off in SEMANTIC_OFFSETS] + ["descriptor"]
    return {key: row[key] for key in keys}


def evaluate(parent: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    ps, cs = parent["samples"], candidate["samples"]
    p0, c0 = ps[0], cs[0]
    p_end, c_end = ps[-1], cs[-1]
    active_parent = [row for row in ps if 1 <= row["step"] <= 30]
    active_candidate = [row for row in cs if 1 <= row["step"] <= 30]
    assertions = {
        "scene0_both": parent["before"]["scene"] == 0 and candidate["before"]["scene"] == 0,
        "f9_address_stable": parent["before"]["f9_address"] == candidate["before"]["f9_address"] == 0xFFC632,
        "player_semantics_equal_before": semantic_object(parent["before"]["f9"]) == semantic_object(candidate["before"]["f9"]),
        "proxy_semantics_equal_before": semantic_object(parent["before"]["fb"]) == semantic_object(candidate["before"]["fb"]),
        "canonical_player_descriptor": parent["before"]["f9"]["descriptor"] == candidate["before"]["f9"]["descriptor"] == 0x000A0000,
        "canonical_proxy_descriptor": parent["before"]["fb"]["descriptor"] == candidate["before"]["fb"]["descriptor"] == 0x000F0000,
        "same_spawn_position": (p0["x"], p0["y"]) == (c0["x"], c0["y"]) == (701, 558),
        "shotgun_pickup_effect_candidate_only": p0["ownership"] == 0x01 and p0["shotgun_ammo"] == 0 and c0["ownership"] == 0x03 and c0["shotgun_ammo"] == 5,
        "active_input_exact": all(row["input"] == ACTIVE_INPUT for row in active_parent + active_candidate),
        "parent_crosses_authored_wall_zone": min(row["x"] for row in ps) < 668,
        "candidate_blocked_by_authored_wall": min(row["x"] for row in cs) == 688 and c_end["y"] == 558,
        "movement_diverges_only_as_expected": p_end["x"] == 652 and c_end["x"] == 688 and p_end["y"] == c_end["y"] == 558,
        "player_semantics_preserved_after": semantic_object(parent["after"]["f9"]) == semantic_object(candidate["after"]["f9"]),
        "proxy_semantics_preserved_after": semantic_object(parent["after"]["fb"]) == semantic_object(candidate["after"]["fb"]),
    }
    return {"assertions": assertions, "pass": all(assertions.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("blastem", type=Path)
    ap.add_argument("parent", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--parent-display", default=":118")
    ap.add_argument("--candidate-display", default=":119")
    args = ap.parse_args()

    if sha256(args.blastem) != EXPECTED_BLASTEM_SHA256:
        raise SystemExit("wrong BlastEm binary")
    if sha1(args.parent) != EXPECTED_PARENT_SHA1:
        raise SystemExit("wrong frozen M09D direct parent")
    if sha1(args.candidate) != EXPECTED_CANDIDATE_SHA1:
        raise SystemExit("wrong M1.0A candidate")

    with BlastEmSession(args.blastem, args.parent, args.parent_display) as session:
        parent = session.run_probe()
    with BlastEmSession(args.blastem, args.candidate, args.candidate_display) as session:
        candidate = session.run_probe()
    verdict = evaluate(parent, candidate)
    report = {
        "schema": "truerecall.m100b.vertical_slice_runtime.v1",
        "blastem_sha256": EXPECTED_BLASTEM_SHA256,
        "parent_sha1": EXPECTED_PARENT_SHA1,
        "candidate_sha1": EXPECTED_CANDIDATE_SHA1,
        "parent": parent,
        "candidate": candidate,
        **verdict,
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not report["pass"]:
        raise SystemExit("M1.0B runtime regression failed")


if __name__ == "__main__":
    main()
