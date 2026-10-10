#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from m100b_vertical_slice_runtime import EXPECTED_BLASTEM_SHA256, evaluate as evaluate_m100b, sha1, sha256
from m110b_palette_runtime import evaluate_cram, run_one

EXPECTED_DIRECT_PARENT_SHA1 = "49a6f19a0d6a1351f75ee5ecd72dff9da2e5e021"
EXPECTED_CANDIDATE_SHA1 = "b6c0303b83b6ac3ce8790171702c3d7f4a7eb7b0"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("blastem", type=Path)
    ap.add_argument("direct_parent", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--parent-display", default=":243")
    ap.add_argument("--candidate-display", default=":244")
    args = ap.parse_args()

    if sha256(args.blastem) != EXPECTED_BLASTEM_SHA256:
        raise SystemExit("wrong BlastEm binary")
    if sha1(args.direct_parent) != EXPECTED_DIRECT_PARENT_SHA1:
        raise SystemExit("wrong frozen M09D direct parent")
    if sha1(args.candidate) != EXPECTED_CANDIDATE_SHA1:
        raise SystemExit("wrong M1.1B candidate")

    parent_gameplay, parent_vdp, parent_state_sha256 = run_one(
        args.blastem, args.direct_parent, args.parent_display
    )
    candidate_gameplay, candidate_vdp, candidate_state_sha256 = run_one(
        args.blastem, args.candidate, args.candidate_display
    )

    gameplay = evaluate_m100b(parent_gameplay, candidate_gameplay)
    cram = evaluate_cram(parent_vdp["cram_words"], candidate_vdp["cram_words"])
    assertions = {
        "m100b_behavioral_regression": gameplay["pass"],
        "m110b_cram_regression": cram["pass"],
    }
    report = {
        "schema": "truerecall.m111e.graphics_regression.v1",
        "blastem_sha256": EXPECTED_BLASTEM_SHA256,
        "direct_parent_sha1": EXPECTED_DIRECT_PARENT_SHA1,
        "candidate_sha1": EXPECTED_CANDIDATE_SHA1,
        "parent_state_sha256": parent_state_sha256,
        "candidate_state_sha256": candidate_state_sha256,
        "m100b": {
            "assertions": gameplay["assertions"],
            "pass": gameplay["pass"],
        },
        "m110b_cram": cram,
        "assertions": assertions,
        "pass": all(assertions.values()),
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not report["pass"]:
        raise SystemExit("M1.1B closed-gate regression failed")


if __name__ == "__main__":
    main()
