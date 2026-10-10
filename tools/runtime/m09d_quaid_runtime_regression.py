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
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

PROMPT = b"> "
PRINT_RE = re.compile(r"^(.+?):\s*([0-9A-Fa-f]+)\s*$")
OBJECT_OFFSETS = [
    0x10, 0x12, 0x14, 0x16, 0x18, 0x1A, 0x1C, 0x1E,
    0x20, 0x22, 0x24, 0x2A, 0x2C, 0x2E, 0x50, 0x54, 0x56,
]
WINDOW = (320, 240, 960, 720)
SCENE = (0, 18, 640, 370)
ACTIVE_FRAMES = 42
POST_FRAMES = 5
BOOT_FRAMES = 100
SETTLE_FRAMES = 2
EXPECTED_DESCRIPTOR = 0x000A0000
EXPECTED_PHASES = {0, 2, 4, 6, 8, 10}


def parse_values(text: str) -> list[int]:
    out = []
    for line in text.replace("\r", "").splitlines():
        match = PRINT_RE.match(line.strip())
        if match:
            out.append(int(match.group(2), 16))
    return out


def ram_pointer(word: int) -> int:
    return (0xFF0000 | (word & 0xFFFF)) if word & 0x8000 else word & 0xFFFF


class Runner:
    def __init__(
        self,
        rom: Path,
        blastem: Path,
        state: Path,
        out_dir: Path,
        display: str,
    ) -> None:
        self.rom = rom
        self.blastem = blastem
        self.package = blastem.parent
        self.state_path = state
        self.out_dir = out_dir
        self.display = display
        self.master: int | None = None
        self.proc: subprocess.Popen | None = None
        self.xvfb: subprocess.Popen | None = None
        self.env: dict[str, str] | None = None

    def read_prompt(self, timeout: float = 15) -> str:
        assert self.master is not None
        data = bytearray()
        end = time.time() + timeout
        while time.time() < end:
            ready, _, _ = select.select([self.master], [], [], 0.05)
            if not ready:
                continue
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            data += chunk
            if data.endswith(PROMPT):
                return data.decode("utf-8", "replace")
        raise TimeoutError(bytes(data[-2000:]))

    def debugger(self, command: str, timeout: float = 15) -> str:
        assert self.master is not None
        os.write(self.master, (command + "\n").encode())
        return self.read_prompt(timeout)

    def key(self, name: str, down: bool) -> None:
        x11 = ctypes.CDLL("libX11.so.6")
        xtst = ctypes.CDLL("libXtst.so.6")
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        x11.XStringToKeysym.restype = ctypes.c_ulong
        x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        x11.XKeysymToKeycode.restype = ctypes.c_uint
        xtst.XTestFakeKeyEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        x11.XFlush.argtypes = [ctypes.c_void_p]
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        display = x11.XOpenDisplay(self.display.encode())
        if not display:
            raise RuntimeError(f"cannot open X display {self.display}")
        try:
            keysym = x11.XStringToKeysym(name.encode())
            keycode = x11.XKeysymToKeycode(display, keysym)
            xtst.XTestFakeKeyEvent(display, keycode, 1 if down else 0, 0)
            x11.XFlush(display)
        finally:
            x11.XCloseDisplay(display)

    def start(self) -> None:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        save_dir = Path.home() / ".local" / "share" / "blastem" / self.rom.stem
        save_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.state_path, save_dir / "quicksave.state")

        self.xvfb = subprocess.Popen(
            ["Xvfb", self.display, "-screen", "0", "1280x960x24", "-nolisten", "tcp"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.25)
        master, slave = pty.openpty()
        self.master = master
        self.env = os.environ.copy()
        self.env.update(
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
            env=self.env,
            close_fds=True,
        )
        os.close(slave)
        self.read_prompt(20)
        self.debugger(f"frames {BOOT_FRAMES}", 20)
        # Pinned BlastEm default mapping: keyboard L loads quick state.
        self.key("l", True)
        self.key("l", False)
        log = self.debugger("frames 1", 10)
        if "Loaded state from" not in log:
            raise RuntimeError("quicksave did not load")
        self.debugger(f"frames {SETTLE_FRAMES}", 10)

    def values(self, expressions: list[str]) -> list[int]:
        values = parse_values(self.debugger("print/x " + " ".join(expressions)))
        if len(values) != len(expressions):
            raise RuntimeError((expressions, values))
        return values

    def state(self) -> dict:
        f9_word, fb_word, fb7c, fb7e, current_input, edge, held = self.values(
            [
                "[0xFFF9F8]", "[0xFFFB6E]", "[0xFFFB7C]", "[0xFFFB7E]",
                "[0xFFF6EC]", "[0xFFF6EE]", "[0xFFF6F0]",
            ]
        )
        f9 = ram_pointer(f9_word)
        proxy = ram_pointer(fb_word)
        f9_values = self.values([f"[0x{f9 + off:06X}]" for off in OBJECT_OFFSETS])
        proxy_values = self.values([f"[0x{proxy + off:06X}]" for off in OBJECT_OFFSETS])
        f9_fields = {f"{off:02X}": value for off, value in zip(OBJECT_OFFSETS, f9_values)}
        proxy_fields = {
            f"{off:02X}": value for off, value in zip(OBJECT_OFFSETS, proxy_values)
        }
        return {
            "F9F8_word": f9_word,
            "F9F8": f9,
            "FB6E_word": fb_word,
            "FB6E": proxy,
            "FB7C": fb7c,
            "FB7E": fb7e,
            "F6EC": current_input,
            "F6EE": edge,
            "F6F0": held,
            "f9": f9_fields,
            "proxy": proxy_fields,
            "f9_descriptor": ((f9_fields["2C"] & 0xFFFF) << 16)
            | (f9_fields["2E"] & 0xFFFF),
            "proxy_descriptor": ((proxy_fields["2C"] & 0xFFFF) << 16)
            | (proxy_fields["2E"] & 0xFFFF),
            "f9_raw_delta": (f9_fields["1E"] - f9_fields["1C"]) & 0xFFFF,
        }

    def capture(self, label: str) -> Path:
        assert self.env is not None
        root = self.out_dir / f"root_{label}.png"
        picture = self.out_dir / f"{label}.png"
        subprocess.run(
            ["scrot", "-o", "-z", str(root)],
            env=self.env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        image = Image.open(root).convert("RGB").crop(WINDOW)
        root.unlink()
        image.save(picture)
        if max(ImageStat.Stat(image).mean) < 1:
            raise RuntimeError(f"black capture: {label}")
        return picture

    def close(self) -> None:
        for key in ("w", "Left"):
            try:
                self.key(key, False)
            except Exception:
                pass
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(1)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.xvfb and self.xvfb.poll() is None:
            self.xvfb.terminate()
            try:
                self.xvfb.wait(1)
            except subprocess.TimeoutExpired:
                self.xvfb.kill()
        if self.master is not None:
            try:
                os.close(self.master)
            except OSError:
                pass


def run_capture(rom: Path, blastem: Path, state: Path, out_dir: Path, display: str) -> dict:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    runner = Runner(rom, blastem, state, out_dir, display)
    rows = []
    try:
        runner.start()
        pre = runner.capture("pre")
        rows.append({"kind": "pre", "step": 0, "state": runner.state(), "png_sha256": hashlib.sha256(pre.read_bytes()).hexdigest()})
        # Pinned BlastEm default mapping: W = Genesis Y, plus physical Left.
        runner.key("Left", True)
        runner.key("w", True)
        for step in range(1, ACTIVE_FRAMES + 1):
            runner.debugger("frames 1", 10)
            current = runner.state()
            picture = runner.capture(f"a{step:02d}")
            rows.append({"kind": "active", "step": step, "state": current, "png_sha256": hashlib.sha256(picture.read_bytes()).hexdigest()})
        runner.key("w", False)
        runner.key("Left", False)
        for _ in range(POST_FRAMES):
            runner.debugger("frames 1", 10)
        post = runner.capture("post")
        rows.append({"kind": "post", "step": POST_FRAMES, "state": runner.state(), "png_sha256": hashlib.sha256(post.read_bytes()).hexdigest()})
        report = {
            "schema": "truerecall.m09d.capture.v1",
            "rom_sha1": hashlib.sha1(rom.read_bytes()).hexdigest(),
            "common_state_sha256": hashlib.sha256(state.read_bytes()).hexdigest(),
            "blastem_sha256": hashlib.sha256(blastem.read_bytes()).hexdigest(),
            "rows": rows,
            "capture_method": "pinned BlastEm normal renderer; common native pre-Y state; XTest W=Y + Left; external X11 scrot",
        }
        (out_dir / "run.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        runner.close()


def image_metrics(parent: Path, candidate: Path) -> dict:
    a = Image.open(parent).convert("RGB")
    b = Image.open(candidate).convert("RGB")
    scene_diff = ImageChops.difference(a, b).crop(SCENE)
    bbox = scene_diff.getbbox()
    different = 0
    for y in range(scene_diff.height):
        for x in range(scene_diff.width):
            if scene_diff.getpixel((x, y)) != (0, 0, 0):
                different += 1
    return {
        "scene_different_pixels": different,
        "scene_bbox": None
        if not bbox
        else [bbox[0], bbox[1] + SCENE[1], bbox[2], bbox[3] + SCENE[1]],
        "scene_bbox_w": 0 if not bbox else bbox[2] - bbox[0],
        "scene_bbox_h": 0 if not bbox else bbox[3] - bbox[1],
    }


def compare(parent_dir: Path, candidate_dir: Path) -> dict:
    parent_report = json.loads((parent_dir / "run.json").read_text(encoding="utf-8"))
    candidate_report = json.loads((candidate_dir / "run.json").read_text(encoding="utf-8"))
    parent = {(row["kind"], row["step"]): row for row in parent_report["rows"]}
    candidate = {(row["kind"], row["step"]): row for row in candidate_report["rows"]}
    rows = []
    state_mismatches = []
    scalar_keys = [
        "F9F8_word", "F9F8", "FB6E_word", "FB6E", "FB7C", "FB7E",
        "F6EC", "F6EE", "F6F0", "f9_descriptor", "proxy_descriptor", "f9_raw_delta",
    ]
    field_keys = [f"{off:02X}" for off in OBJECT_OFFSETS]
    specifications = [("pre", 0, "pre")]
    specifications += [("active", step, f"a{step:02d}") for step in range(1, ACTIVE_FRAMES + 1)]
    specifications += [("post", POST_FRAMES, "post")]

    for kind, step, label in specifications:
        pstate = parent[(kind, step)]["state"]
        cstate = candidate[(kind, step)]["state"]
        mismatch = []
        for key in scalar_keys:
            if pstate[key] != cstate[key]:
                mismatch.append([key, pstate[key], cstate[key]])
        for obj in ("f9", "proxy"):
            for key in field_keys:
                if pstate[obj][key] != cstate[obj][key]:
                    mismatch.append([f"{obj}.{key}", pstate[obj][key], cstate[obj][key]])
        if mismatch:
            state_mismatches.append({"kind": kind, "step": step, "mismatch": mismatch})
        rows.append(
            {
                "kind": kind,
                "step": step,
                "phase": cstate["f9_raw_delta"],
                "input": cstate["F6EC"],
                "descriptor": cstate["f9_descriptor"],
                "state_equal": not mismatch,
                **image_metrics(parent_dir / f"{label}.png", candidate_dir / f"{label}.png"),
            }
        )

    active = [row for row in rows if row["kind"] == "active"]
    visible = [row for row in active if row["scene_different_pixels"] > 0]
    phases = {row["phase"] for row in active}
    first_visible = min(row["step"] for row in visible)
    assertions = {
        "pre_scene_exact": rows[0]["scene_different_pixels"] == 0,
        "post_scene_exact": rows[-1]["scene_different_pixels"] == 0,
        "active_y_left_normalized": all((row["input"] & 0x2004) == 0x2004 for row in active),
        "runtime_state_equal": not state_mismatches,
        "canonical_descriptor_preserved": all(row["descriptor"] == EXPECTED_DESCRIPTOR for row in active),
        "all_six_phases_observed": phases == EXPECTED_PHASES,
        "activation_latency_at_most_2_frames": first_visible <= 3,
        "visible_after_warmup_every_frame": all(row["scene_different_pixels"] > 0 for row in active if row["step"] >= first_visible),
        "all_visible_diffs_within_scaled_retail_envelope": all(row["scene_bbox_w"] <= 96 and row["scene_bbox_h"] <= 128 for row in visible),
        "every_phase_has_visible_frame": all(any(row["phase"] == phase for row in visible) for phase in EXPECTED_PHASES),
    }
    return {
        "schema": "truerecall.m09d.quaid_runtime_regression.v1",
        "parent_sha1": parent_report["rom_sha1"],
        "candidate_sha1": candidate_report["rom_sha1"],
        "common_state_sha256": parent_report["common_state_sha256"],
        "blastem_sha256": parent_report["blastem_sha256"],
        "capture_method": parent_report["capture_method"],
        "native_retail_actor_envelope": [48, 64],
        "capture_scale": 2,
        "scaled_envelope": [96, 128],
        "rows": rows,
        "state_mismatches": state_mismatches,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("parent_rom", type=Path)
    ap.add_argument("candidate_rom", type=Path)
    ap.add_argument("blastem", type=Path)
    ap.add_argument("state", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--parent-display", default=":148")
    ap.add_argument("--candidate-display", default=":149")
    args = ap.parse_args()

    parent_dir = args.out_dir / "parent"
    candidate_dir = args.out_dir / "candidate"
    run_capture(args.parent_rom, args.blastem, args.state, parent_dir, args.parent_display)
    run_capture(args.candidate_rom, args.blastem, args.state, candidate_dir, args.candidate_display)
    report = compare(parent_dir, candidate_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    evidence = args.out_dir / "m09d_quaid_runtime_regression.json"
    evidence.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assertions": report["assertions"], "pass": report["pass"]}, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
