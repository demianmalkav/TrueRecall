#!/usr/bin/env python3
"""Validate TrueRecall disaster-recovery state without prior chat context."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_SCHEMA = "truerecall.recovery_manifest.v1"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(root: Path) -> dict:
    path = root / "docs" / "RECOVERY_MANIFEST.json"
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_git_branch(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return out or None


def validate_static(root: Path, manifest: dict) -> list[Check]:
    checks: list[Check] = []

    checks.append(
        Check(
            "manifest_schema",
            "PASS" if manifest.get("schema") == EXPECTED_SCHEMA else "FAIL",
            str(manifest.get("schema")),
        )
    )

    authority = manifest.get("authority", {})
    required = [
        authority.get("human_state"),
        authority.get("machine_state"),
        authority.get("technical_compendium"),
        authority.get("operating_contract"),
        authority.get("recovery_procedure"),
    ]
    missing = [p for p in required if not p or not (root / p).is_file()]
    checks.append(
        Check(
            "authority_files",
            "PASS" if not missing else "FAIL",
            "all present" if not missing else "missing: " + ", ".join(map(str, missing)),
        )
    )

    active_branch = authority.get("active_branch")
    project_state_path = root / str(authority.get("human_state", ""))
    project_state = project_state_path.read_text(encoding="utf-8") if project_state_path.is_file() else ""
    branch_in_state = bool(active_branch and active_branch in project_state)
    milestone = manifest.get("active", {}).get("milestone")
    milestone_in_state = bool(milestone and milestone in project_state)
    checkpoint = manifest.get("generated_from_technical_checkpoint")
    checkpoint_in_state = bool(checkpoint and checkpoint in project_state)

    checks.extend(
        [
            Check("branch_agreement", "PASS" if branch_in_state else "FAIL", str(active_branch)),
            Check("milestone_agreement", "PASS" if milestone_in_state else "FAIL", str(milestone)),
            Check("checkpoint_agreement", "PASS" if checkpoint_in_state else "FAIL", str(checkpoint)),
        ]
    )

    authoritative_tools: Iterable[str] = manifest.get("authoritative_tools", [])
    missing_tools = [p for p in authoritative_tools if not (root / p).is_file()]
    checks.append(
        Check(
            "authoritative_tools",
            "PASS" if not missing_tools else "FAIL",
            "all present" if not missing_tools else "missing: " + ", ".join(missing_tools),
        )
    )

    evidence_paths = [
        manifest.get("evidence", {}).get("canonical_phase_bridge"),
        manifest.get("evidence", {}).get("trampoline_runtime"),
    ]
    missing_evidence = [p for p in evidence_paths if not p or not (root / p).is_file()]
    checks.append(
        Check(
            "primary_evidence",
            "PASS" if not missing_evidence else "FAIL",
            "all present" if not missing_evidence else "missing: " + ", ".join(map(str, missing_evidence)),
        )
    )

    if not manifest.get("open"):
        checks.append(Check("open_gate", "FAIL", "no OPEN gate recorded"))
    else:
        checks.append(Check("open_gate", "PASS", manifest["open"][0].get("name", "unnamed")))

    if not manifest.get("next"):
        checks.append(Check("next_sequence", "FAIL", "NEXT is empty"))
    else:
        checks.append(Check("next_sequence", "PASS", f"{len(manifest['next'])} ordered actions"))

    git_branch = current_git_branch(root)
    if git_branch is None:
        checks.append(Check("live_git_branch", "WARN", "git branch unavailable"))
    elif git_branch == "HEAD":
        checks.append(Check("live_git_branch", "WARN", "detached HEAD; compare ref externally"))
    elif git_branch == active_branch:
        checks.append(Check("live_git_branch", "PASS", git_branch))
    else:
        checks.append(Check("live_git_branch", "WARN", f"current={git_branch}; expected={active_branch}"))

    return checks


def validate_rom(manifest: dict, rom_path: Path | None) -> list[Check]:
    if rom_path is None:
        return [Check("canonical_rom", "SKIP", "no ROM path supplied")]
    if not rom_path.is_file():
        return [Check("canonical_rom", "FAIL", f"not found: {rom_path}")]

    spec = manifest["canonical_rom"]
    size = rom_path.stat().st_size
    digest = sha1_file(rom_path)
    ok = size == int(spec["size_bytes"]) and digest.lower() == spec["sha1"].lower()
    detail = f"size={size} sha1={digest}"
    return [Check("canonical_rom", "PASS" if ok else "FAIL", detail)]


def render(checks: Iterable[Check], manifest: dict) -> str:
    lines = ["TrueRecall recovery doctor"]
    for check in checks:
        lines.append(f"{check.name:24} {check.status:5}  {check.detail}")
    active = manifest.get("active", {})
    lines.extend(
        [
            "",
            f"ACTIVE BRANCH: {manifest.get('authority', {}).get('active_branch')}",
            f"MILESTONE:     {active.get('milestone')} — {active.get('name')}",
            f"OPEN:          {manifest.get('open', [{}])[0].get('name')}",
            f"NEXT:          {manifest.get('next', [''])[0]}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?", type=Path, help="optional canonical True Lies ROM path")
    args = parser.parse_args()

    root = repo_root()
    manifest = load_manifest(root)
    checks = validate_static(root, manifest) + validate_rom(manifest, args.rom)
    print(render(checks, manifest))
    return 1 if any(c.status == "FAIL" for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
