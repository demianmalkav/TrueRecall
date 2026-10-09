#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass

from world_collision_codec import assert_retail_exact_scene, p16, serialize_index


@dataclass
class WorldRecord:
    offset: int
    world_type: int
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    name: str | None = None

    def as_row(self):
        return [self.offset, self.world_type, self.x_min, self.y_min, self.x_max, self.y_max]


def export_scene(rom: bytes, scene_index: int):
    layout = assert_retail_exact_scene(rom, scene_index)
    return {
        "scene": scene_index,
        "grid": [layout["grid_w"], layout["grid_h"]],
        "grid_bytes": layout["grid_bytes"],
        "record_start": layout["record_start"],
        "records": [
            {
                "id": f"retail_{i:03d}",
                "offset": row[0],
                "type": row[1],
                "rect": row[2:],
            }
            for i, row in enumerate(layout["records"])
        ],
    }


def records_from_manifest(manifest):
    return [
        WorldRecord(
            int(row["offset"]),
            int(row["type"]),
            *map(int, row["rect"]),
            row.get("id"),
        )
        for row in manifest["records"]
    ]


def apply_ops(manifest, ops):
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in manifest.items() if k != "records"}
    records = [dict(row) for row in manifest["records"]]
    by_id = {row["id"]: row for row in records}

    for op in ops:
        kind = op["op"]
        if kind == "remove":
            record_id = op["id"]
            records = [row for row in records if row["id"] != record_id]
            by_id.pop(record_id, None)
        elif kind == "replace":
            row = by_id[op["id"]]
            if "type" in op:
                row["type"] = int(op["type"])
            if "rect" in op:
                row["rect"] = list(map(int, op["rect"]))
        elif kind == "add":
            record_id = op["id"]
            if record_id in by_id:
                raise ValueError(f"duplicate world record id: {record_id}")
            row = {
                "id": record_id,
                "offset": int(op["offset"]),
                "type": int(op["type"]),
                "rect": list(map(int, op["rect"])),
            }
            records.append(row)
            by_id[record_id] = row
        else:
            raise ValueError(f"unknown world manifest op: {kind}")

    out["records"] = records
    return out


def compile_manifest(manifest, pool_start: int | None = None):
    grid_w, grid_h = manifest["grid"]
    records = records_from_manifest(manifest)
    rows = [record.as_row() for record in records]
    grid, pool, memberships = serialize_index(rows, grid_w, grid_h, pool_start=pool_start)

    record_bytes = {}
    for record in records:
        record_bytes[record.offset] = b"".join(
            p16(value)
            for value in (
                record.world_type,
                record.x_min,
                record.y_min,
                record.x_max,
                record.y_max,
            )
        )

    return {
        "grid": grid,
        "pool": pool,
        "memberships": memberships,
        "record_bytes": record_bytes,
    }
