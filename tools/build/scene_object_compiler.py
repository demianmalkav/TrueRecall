#!/usr/bin/env python3
"""Compile declarative True Lies / TrueRecall scene-object edits into a ROM.

The compiler preserves the scene-local opaque prefix from the canonical base,
rebuilds the full placement record stream, regenerates stride runs, LZBeam
encodes the stream, relocates descriptor+resource into a verified FF region,
patches the scene descriptor pointer and repairs the Genesis checksum.

Manifest schema: truerecall.scene_object_patch.v1
"""
from __future__ import annotations

import argparse, hashlib, json
from dataclasses import replace
from pathlib import Path
from typing import Any

from object_stream_codec import parse_scene, Placement, serialize_compiled, build_descriptor
from lzbeam_codec import encode_stream

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
CHECKSUM_OFFSET = 0x018E
DEFAULT_FREE_START = 0x1FABC3
DEFAULT_FREE_END = 0x200000
TYPE_MASK = 0x03FF


def checksum(buf: bytes | bytearray) -> int:
    total = 0
    for off in range(0x200, len(buf), 2):
        total = (total + ((buf[off] << 8) | buf[off + 1])) & 0xFFFF
    return total


def parse_int(value: Any) -> int:
    if isinstance(value, int): return value
    if isinstance(value, str): return int(value, 0)
    raise TypeError(value)


def align(value: int, alignment: int = 2) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def manifest_placement(obj: dict, index: int, order: int) -> tuple[Placement, int]:
    stride = parse_int(obj.get("stride", 6)); type_id = parse_int(obj["type_id"]); flags = parse_int(obj.get("status_flags", "0x7800"))
    x = parse_int(obj["x"]); y = parse_int(obj["y"]); param = obj.get("param")
    if stride == 8:
        if param is None: raise ValueError("8-byte add requires param")
        param = parse_int(param)
    elif stride == 6:
        if param is not None: raise ValueError("6-byte add cannot carry param")
    else: raise ValueError("stride must be 6 or 8")
    if not 0 <= type_id <= TYPE_MASK: raise ValueError(type_id)
    return Placement(index, stride, (flags & ~TYPE_MASK) | type_id, x, y, param, -1), order


def apply_manifest(base: list[Placement], manifest: dict) -> list[Placement]:
    rows = [(replace(p), p.index) for p in base]; next_order = max((o for _, o in rows), default=-1) + 1
    for op_number, op in enumerate(manifest.get("operations", [])):
        kind = op["op"]
        if kind in ("replace", "remove"):
            base_index = parse_int(op["base_index"])
            hits = [i for i, (p, order) in enumerate(rows) if p.index == base_index and order == base_index]
            if len(hits) != 1: raise ValueError(f"base_index {base_index} is not uniquely present at operation {op_number}")
            pos = hits[0]
            if kind == "remove": rows.pop(pos); continue
            p, order = rows[pos]
            type_id = parse_int(op.get("type_id", p.type_id)); flags = parse_int(op.get("status_flags", p.status_flags)); stride = parse_int(op.get("stride", p.stride))
            x = parse_int(op.get("x", p.x)); y = parse_int(op.get("y", p.y)); param = op.get("param", p.param)
            if stride == 8:
                if param is None: raise ValueError("8-byte replace requires param")
                param = parse_int(param)
            elif stride == 6: param = None
            else: raise ValueError("stride must be 6 or 8")
            rows[pos] = (Placement(p.index, stride, (flags & ~TYPE_MASK) | type_id, x, y, param, -1), order)
        elif kind == "add":
            p, order = manifest_placement(op, -1, next_order); next_order += 1; rows.append((p, order))
        else:
            raise ValueError(f"unknown operation {kind}")
    rows.sort(key=lambda item: (item[0].y, item[1]))
    return [replace(p, index=i) for i, (p, _order) in enumerate(rows)]


def first_ff_region(raw: bytes, start: int, end: int, length: int, alignment: int = 2) -> int:
    p = align(start, alignment)
    while p + length <= end:
        q = raw.find(b"\xff" * min(length, 32), p, end)
        if q < 0: return -1
        q = align(q, alignment)
        if q + length <= end and all(x == 0xFF for x in raw[q:q+length]): return q
        p = q + alignment
    return -1


def build(raw: bytes, manifest: dict) -> tuple[bytes, dict]:
    if manifest.get("schema") != "truerecall.scene_object_patch.v1": raise ValueError("unsupported manifest schema")
    scene_index = parse_int(manifest["scene_index"]); stream = parse_scene(raw, scene_index); placements = apply_manifest(stream.placements, manifest)
    decoded, runs = serialize_compiled(stream.prefix, placements); encoded = encode_stream(decoded)
    descriptor_length = 10 + 2 * len(runs)
    free_start = parse_int(manifest.get("free_start", DEFAULT_FREE_START)); free_end = parse_int(manifest.get("free_end", DEFAULT_FREE_END))
    reserve = descriptor_length + 1 + len(encoded); descriptor_address = first_ff_region(raw, free_start, free_end, reserve, 2)
    if descriptor_address < 0: raise ValueError("no sufficiently large FF region")
    lz_address = align(descriptor_address + descriptor_length, 2); total_end = lz_address + len(encoded)
    if total_end > free_end or any(x != 0xFF for x in raw[descriptor_address:total_end]): raise ValueError("allocation is not pristine FF")
    descriptor = build_descriptor(count=len(placements), start=len(stream.prefix), end=len(decoded), source_lz=lz_address, runs=runs)
    out = bytearray(raw); out[descriptor_address:descriptor_address+len(descriptor)] = descriptor; out[lz_address:lz_address+len(encoded)] = encoded
    out[stream.scene_ptr+0x0A:stream.scene_ptr+0x0E] = descriptor_address.to_bytes(4, "big"); out[CHECKSUM_OFFSET:CHECKSUM_OFFSET+2] = checksum(out).to_bytes(2, "big")

    rebuilt = parse_scene(bytes(out), scene_index)
    assert rebuilt.descriptor == descriptor_address and rebuilt.source_lz == lz_address and len(rebuilt.placements) == len(placements)
    for expected, actual in zip(placements, rebuilt.placements):
        assert (expected.stride, expected.status, expected.x, expected.y, expected.param) == (actual.stride, actual.status, actual.x, actual.y, actual.param)

    report = {
        "schema":"truerecall.scene_object_build.v1","scene_index":scene_index,
        "base_descriptor":f"0x{stream.descriptor:06X}","new_descriptor":f"0x{descriptor_address:06X}",
        "base_lz":f"0x{stream.source_lz:06X}","new_lz":f"0x{lz_address:06X}",
        "base_placements":len(stream.placements),"new_placements":len(placements),"prefix_bytes":len(stream.prefix),
        "decoded_bytes":len(decoded),"encoded_bytes":len(encoded),"stride_runs":[list(x) for x in runs],
        "checksum":f"0x{checksum(out):04X}","output_sha1":hashlib.sha1(out).hexdigest(),"operations":manifest.get("operations",[]),
    }
    return bytes(out), report


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("rom", type=Path); ap.add_argument("manifest", type=Path); ap.add_argument("output", type=Path); ap.add_argument("--report", type=Path); args = ap.parse_args()
    raw = args.rom.read_bytes(); assert len(raw) == EXPECTED_SIZE
    digest = hashlib.sha1(raw).hexdigest(); assert digest == EXPECTED_SHA1
    manifest = json.loads(args.manifest.read_text(encoding="utf-8")); out, report = build(raw, manifest); report["base_sha1"] = digest
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_bytes(out)
    text = json.dumps(report, indent=2, sort_keys=True); print(text)
    if args.report: args.report.write_text(text + "\n", encoding="utf-8")

if __name__ == "__main__": main()
