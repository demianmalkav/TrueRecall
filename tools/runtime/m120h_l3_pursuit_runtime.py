#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from m100b_vertical_slice_runtime import BlastEmSession, EXPECTED_BLASTEM_SHA256, ram_pointer, sha256

EXPECTED_CANDIDATE_SHA1 = "acfecb2fdb5cc6c55a5c89ae172dd58d8444e1e3"
FC54 = 0xFFFC54
FC56 = 0xFFFC56
FC06 = 0xFFFC06
ACTIVE_COUNT = 0xFFF9F2
ACTIVE_SENTINEL = 0xFFF9F4
F9F8 = 0xFFF9F8
FB6E = 0xFFFB6E
CHASE_TYPE = 24
PROJECTILE_TYPE = 170


def sha1(path: Path) -> str:
    return hashlib.sha1(path.read_bytes()).hexdigest()


def descriptor(session: BlastEmSession, address: int) -> int:
    hi, lo = session.values([f"[0x{address + 0x2C:06X}]", f"[0x{address + 0x2E:06X}]"])
    return (hi << 16) | lo


def active_list(session: BlastEmSession) -> dict[str, Any]:
    count = session.values([f"[0x{ACTIVE_COUNT:06X}]"])[0]
    cur = ram_pointer(session.values([f"[0x{ACTIVE_SENTINEL:06X}]"])[0])
    out: list[dict[str, int]] = []
    seen: set[int] = set()
    for _ in range(40):
        if cur == 0 or (cur & 0xFFFF) == 0xF9F4:
            break
        if cur in seen:
            raise RuntimeError(f"active-list cycle at 0x{cur:06X}")
        seen.add(cur)
        nxt, type_id, x, y, dhi, dlo = session.values(
            [
                f"[0x{cur:06X}]",
                f"[0x{cur + 0x2A:06X}]",
                f"[0x{cur + 0x10:06X}]",
                f"[0x{cur + 0x14:06X}]",
                f"[0x{cur + 0x2C:06X}]",
                f"[0x{cur + 0x2E:06X}]",
            ]
        )
        out.append({"address": cur, "type": type_id, "x": x, "y": y, "descriptor": (dhi << 16) | dlo})
        cur = ram_pointer(nxt)
    return {"active_count": count, "objects": out}


def press(session: BlastEmSession, key: str, frames: int = 2) -> None:
    session.key(key, True)
    session.command(f"frames {frames}")
    session.cur += frames
    session.key(key, False)


def boot_scene0(session: BlastEmSession) -> None:
    for frame, key in ((930, "Return"), (1320, "a"), (1500, "a"), (1680, "a"), (1860, "a"), (2040, "a")):
        session.go(frame)
        session.key(key, True)
        session.go(frame + 2)
        session.key(key, False)
    session.go(2200)


def wait_until(session: BlastEmSession, predicate, *, step: int = 1, max_frames: int = 1000) -> int:
    elapsed = 0
    while elapsed < max_frames:
        session.command(f"frames {step}")
        session.cur += step
        elapsed += step
        if predicate():
            return elapsed
    raise TimeoutError(f"condition not reached in {max_frames} frames")


def run_probe(session: BlastEmSession) -> dict[str, Any]:
    boot_scene0(session)
    f9 = ram_pointer(session.values([f"[0x{F9F8:06X}]"])[0])
    fb = ram_pointer(session.values([f"[0x{FB6E:06X}]"])[0])
    frozen = {
        "f9_address": f9,
        "fb_address": fb,
        "f9_descriptor": descriptor(session, f9),
        "fb_descriptor": descriptor(session, fb),
    }

    session.key("Right", True)
    session.key("w", True)
    wait_until(session, lambda: session.values([f"[0x{FC54:06X}]"])[0] == 0x4000, step=5, max_frames=600)
    session.key("Right", False)
    session.key("w", False)
    lever_fc54, lever_fc56, lever_fc06 = session.values([f"[0x{FC54:06X}]", f"[0x{FC56:06X}]", f"[0x{FC06:06X}]"])
    lever = {"frame": session.cur, "fc54": lever_fc54, "fc56": lever_fc56, "fc06": lever_fc06}

    for index in range(5):
        session.command("frames 120")
        session.cur += 120
        press(session, "a")
        if session.values([f"[0x{ACTIVE_COUNT:06X}]"])[0] <= 7 and index >= 1:
            break
    session.command("frames 120")
    session.cur += 120

    session.key("Left", True)
    session.key("w", True)
    wait_until(session, lambda: session.values([f"[0x{FC06:06X}]"])[0] == 0x36, step=1, max_frames=700)
    session.key("Left", False)
    session.key("w", False)

    fc54, fc56, fc06 = session.values([f"[0x{FC54:06X}]", f"[0x{FC56:06X}]", f"[0x{FC06:06X}]"])
    signal_active = active_list(session)
    spawned = [row for row in signal_active["objects"] if row["type"] == CHASE_TYPE]
    if len(spawned) != 1:
        raise RuntimeError(f"expected one active type24 after signal branch, got {spawned}")
    child = spawned[0]
    signal = {"frame": session.cur, "fc54": fc54, "fc56": fc56, "fc06": fc06, "active_count": signal_active["active_count"], "child": child}

    session.key("Right", True)
    session.key("w", True)
    release_rows: list[dict[str, Any]] = []
    for tag in ("advance_1", "advance_2"):
        session.command("frames 118")
        session.cur += 118
        press(session, "a")
        f9_now = ram_pointer(session.values([f"[0x{F9F8:06X}]"])[0])
        state = active_list(session)
        by_addr = {row["address"]: row for row in state["objects"]}
        release_rows.append({
            "tag": tag,
            "frame": session.cur,
            "player_x": session.values([f"[0x{f9_now + 0x10:06X}]"])[0],
            "child": by_addr.get(child["address"]),
            "active_count": state["active_count"],
        })

    chase_samples: list[dict[str, Any]] = []
    projectile_observed = False
    for _ in range(7):
        session.command("frames 5")
        session.cur += 5
        f9_now = ram_pointer(session.values([f"[0x{F9F8:06X}]"])[0])
        state = active_list(session)
        by_addr = {row["address"]: row for row in state["objects"]}
        types = [row["type"] for row in state["objects"]]
        projectile_observed = projectile_observed or PROJECTILE_TYPE in types
        chase_samples.append({
            "frame": session.cur,
            "player_x": session.values([f"[0x{f9_now + 0x10:06X}]"])[0],
            "child": by_addr.get(child["address"]),
            "active_count": state["active_count"],
            "types": types,
        })
    session.key("Right", False)
    session.key("w", False)

    return {"frozen": frozen, "lever": lever, "signal": signal, "release": release_rows, "chase_samples": chase_samples, "projectile170_observed": projectile_observed}


def evaluate(probe: dict[str, Any]) -> dict[str, Any]:
    signal_child = probe["signal"]["child"]
    release2_child = probe["release"][1]["child"]
    later_children = [row["child"] for row in probe["chase_samples"] if row["child"] is not None]
    max_child_x = max([signal_child["x"]] + [row["x"] for row in later_children])
    assertions = {
        "frozen_player_descriptor": probe["frozen"]["f9_descriptor"] == 0x000A0000,
        "frozen_proxy_descriptor": probe["frozen"]["fb_descriptor"] == 0x000F0000,
        "lever_native_flag": probe["lever"]["fc54"] == 0x4000,
        "lever_does_not_clear_fc56": probe["lever"]["fc56"] == 1,
        "signal_success_message": probe["signal"]["fc06"] == 0x36,
        "signal_preserves_fc54": probe["signal"]["fc54"] == 0x4000,
        "signal_clears_private_latch": probe["signal"]["fc56"] == 0,
        "one_type24_spawned": signal_child["type"] == CHASE_TYPE,
        "spawn_position_exact": (signal_child["x"], signal_child["y"]) == (651, 558),
        "player_control_releases": probe["release"][1]["player_x"] > probe["release"][0]["player_x"],
        "type24_survives_release": release2_child is not None and release2_child["type"] == CHASE_TYPE,
        "type24_advances_toward_player": max_child_x > signal_child["x"],
    }
    return {"assertions": assertions, "pass": all(assertions.values()), "max_child_x": max_child_x}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("blastem", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--display", default=":321")
    args = ap.parse_args()

    if sha256(args.blastem) != EXPECTED_BLASTEM_SHA256:
        raise SystemExit("wrong BlastEm binary")
    if sha1(args.candidate) != EXPECTED_CANDIDATE_SHA1:
        raise SystemExit("wrong M120H candidate")

    old_home = os.environ.get("HOME")
    with tempfile.TemporaryDirectory() as temp_home:
        os.environ["HOME"] = temp_home
        try:
            with BlastEmSession(args.blastem, args.candidate, args.display) as session:
                probe = run_probe(session)
        finally:
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home

    verdict = evaluate(probe)
    report = {
        "schema": "truerecall.m120h.l3_pursuit_runtime.v1",
        "status": "PASS" if verdict["pass"] else "FAIL",
        "blastem_sha256": EXPECTED_BLASTEM_SHA256,
        "candidate_sha1": EXPECTED_CANDIDATE_SHA1,
        "claim": "scene-specific chase pressure: type87 success clears private FC56 latch and spawns one type24 that advances toward Quaid after interaction release; projectile fire is not required for this gate",
        "probe": probe,
        **verdict,
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not report["pass"]:
        raise SystemExit("M120H pursuit runtime regression failed")


if __name__ == "__main__":
    main()
