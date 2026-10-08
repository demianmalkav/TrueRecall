#!/usr/bin/env python3
"""Build a machine-readable semantic authoring catalog for retail True Lies placements.

The catalog combines only independently recoverable structural/mechanical facts:
placements/scenes, representation, initial archetype/stats, conservative callback
prefixes, initial presentation families, known combat roles and curated semantic
labels whose evidence is already documented by project probes.

Missing labels remain unresolved; this tool never guesses from graphics alone.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32
from initial_visual_cfg_probe import decode
from initial_presentation_cfg_probe import first_presentation_calls

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA1 = "d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_SELECTOR_TABLE = 0x07A33C
TYPE_POINTER_TABLE = 0x07953E
ARCHETYPE_TABLE = 0x079906
HP_NORMAL = 0x07A066
HP_HARD = 0x079F74
DAMAGE_NORMAL = 0x079E82
DAMAGE_HARD = 0x079D90

# Curated semantic labels only where independent evidence has been recorded.
IDENTITY = {
    51: ("flamethrower_weapon_pickup", "CONFIRMED"),
    52: ("flamethrower_fuel_pickup", "CONFIRMED"),
    53: ("grenade_pickup", "CONFIRMED"),
    54: ("health_pickup", "CONFIRMED"),
    61: ("extra_life_pickup", "CONFIRMED"),
    62: ("mine_pickup", "CONFIRMED"),
    68: ("shotgun_ammo_pickup", "CONFIRMED"),
    69: ("shotgun_weapon_pickup", "CONFIRMED"),
    70: ("uzi_weapon_pickup", "CONFIRMED"),
    71: ("uzi_ammo_pickup", "CONFIRMED"),
    63: ("security_passcard", "CONFIRMED"),
    58: ("gate_key", "CONFIRMED"),
    60: ("subway_lever", "CONFIRMED"),
    55: ("palace_key", "CONFIRMED"),
    56: ("catacombs_key", "CONFIRMED"),
    64: ("alpha_security_pass", "CONFIRMED"),
    65: ("beta_security_pass", "CONFIRMED"),
    66: ("gamma_security_pass", "CONFIRMED"),
    67: ("delta_security_pass", "CONFIRMED"),
    9: ("bomb_disarming_key", "CONFIRMED"),
    57: ("brass_key", "CONFIRMED"),
    13: ("security_passcard_door", "CONFIRMED"),
    16: ("palace_gate", "CONFIRMED"),
    17: ("catacombs_gate", "CONFIRMED"),
    18: ("locked_gate_palace_key_profile", "CONFIRMED"),
    77: ("alpha_pass_door", "CONFIRMED"),
    78: ("beta_pass_door", "CONFIRMED"),
    79: ("gamma_pass_door", "CONFIRMED"),
    80: ("delta_pass_door", "CONFIRMED"),
    87: ("subway_signal_box", "CONFIRMED"),
    48: ("locked_gate_key_required", "CONFIRMED"),
    122: ("locked_gate_key_required", "CONFIRMED"),
    46: ("truck", "CONFIRMED"),
    12: ("modem_connection_completion_interactable", "CONFIRMED"),
    113: ("destructible_loot_supply_crate", "CONFIRMED"),
    81: ("mission_transition_controller", "CONFIRMED"),
    100: ("mission_completion_controller", "CONFIRMED"),
    133: ("crate_count_objective_controller", "CONFIRMED"),
    134: ("crate_count_objective_controller", "CONFIRMED"),
    34: ("scene14_scroll_state_controller", "CONFIRMED"),
    10: ("scene14_camera_scroll_boundary_trigger_A", "HIGH_CONFIDENCE"),
    101: ("scene14_camera_scroll_boundary_trigger_B", "HIGH_CONFIDENCE"),
    4: ("randomized_damaging_prop_spawner", "HIGH_CONFIDENCE"),
    88: ("extraction_van_controller", "HIGH_CONFIDENCE"),
    97: ("train_blockade_stronghold_logic", "HIGH_CONFIDENCE"),
    125: ("computer_destruction_objective_controller", "HIGH_CONFIDENCE"),
    129: ("bomb_objective_controller", "HIGH_CONFIDENCE"),
    131: ("modem_computer_objective_interactable", "HIGH_CONFIDENCE"),
    132: ("objective_completion_trigger", "HIGH_CONFIDENCE"),
    3: ("crimson_jihad_message_linked_hostile", "HIGH_CONFIDENCE"),
    104: ("boss_class_ranged_actor", "CONFIRMED"),
    121: ("boss_class_composite_ranged_actor", "CONFIRMED"),
    41: ("special_directional_projectile_actor", "CONFIRMED"),
    29: ("explosive_barrel_variant_A", "HIGH_CONFIDENCE"),
    31: ("explosive_barrel_variant_B", "HIGH_CONFIDENCE"),
    72: ("spike_trap_horizontal_variant_A", "HIGH_CONFIDENCE"),
    73: ("spike_trap_horizontal_variant_B", "HIGH_CONFIDENCE"),
    74: ("spike_trap_vertical_variant_A", "HIGH_CONFIDENCE"),
    75: ("spike_trap_vertical_variant_B", "HIGH_CONFIDENCE"),
}

CIVILIANS = {11, 40, 49, 50, 84, 102, 105, 108, 109, 110, 119, 120, 128}
STANDARD_RANGED = {5, 7, 24, 25, 28, 38, 39, 82, 98, 107, 112, 126, 127}
SPREAD_RANGED = {20, 86}
CONTACT_HAZARDS = {29, 31, 35, 36, 72, 73, 74, 75, 93, 94, 95}
PICKUPS = {51, 52, 53, 54, 61, 62, 68, 69, 70, 71}
OBJECTIVE_ITEMS = {9, 55, 56, 57, 58, 60, 63, 64, 65, 66, 67}
DOOR_INTERACTABLES = {12, 13, 16, 17, 18, 48, 77, 78, 79, 80, 87, 122}
CONTROLLERS = {4, 10, 34, 81, 100, 101, 133, 134}
CONTROLLER_CANDIDATES = {88, 97, 125, 129, 131, 132}


def placement_info(rom: bytes):
    counts: Counter[int] = Counter()
    scenes: dict[int, set[int]] = defaultdict(set)
    for scene_index in range(SCENE_COUNT):
        scene = u32(rom, SCENE_TABLE + scene_index * 4)
        desc = u32(rom, scene + 0x0A)
        count = u16(rom, desc)
        pos = u16(rom, desc + 2)
        decoded = lzbeam_decode(rom, u32(rom, desc + 6))
        run_pos = desc + 0x0A
        total = 0
        runs = []
        while total < count:
            stride, quantity = rom[run_pos], rom[run_pos + 1]
            run_pos += 2
            assert stride in (6, 8) and quantity > 0
            runs.append((stride, quantity))
            total += quantity
        for stride, quantity in runs:
            for _ in range(quantity):
                type_id = u16(decoded, pos) & 0x03FF
                counts[type_id] += 1
                scenes[type_id].add(scene_index)
                pos += stride
    return counts, scenes


def reachable_natives(rom: bytes, type_id: int, max_states: int = 50_000):
    if rom[TYPE_SELECTOR_TABLE + type_id] == 0:
        return set()
    queue = deque([(u32(rom, TYPE_POINTER_TABLE + type_id * 4), ())])
    seen = set()
    natives = set()
    while queue and len(seen) < max_states:
        pc, stack = queue.popleft()
        key = (pc, stack)
        if key in seen or not (0 <= pc < len(rom) - 2):
            continue
        seen.add(key)
        ins = decode(rom, pc)
        if ins.get("bad"):
            continue
        op = ins["op"]
        if op == 0x00E4:
            natives.add(ins.get("operand"))
        if op in (0x0000, 0x0004):
            queue.append((ins["target"], stack))
            queue.append((ins["end"], stack))
        elif op == 0x0008:
            queue.append((ins["target"], stack))
        elif op == 0x000C:
            if len(stack) < 16:
                queue.append((ins["target"], stack + (ins["end"],)))
        elif op == 0x0010:
            if stack:
                queue.append((stack[-1], stack[:-1]))
        elif op == 0x00AC:
            for _, target in ins["cases"]:
                queue.append((target, stack))
            queue.append((ins["end"], stack))
        else:
            queue.append((ins["end"], stack))
    return natives


def presentation_classification(result: dict) -> str:
    families = {(call["mode"], call["arg0"]) for call in result["calls"]}
    if result["direct_code"]:
        return "direct_code"
    if result["truncated"]:
        return "truncated"
    if not result["calls"]:
        return "no_initial_presentation_native"
    if len(families) == 1:
        return "unique_presentation_family"
    return "branch_variants"


def authoring_kind(type_id: int) -> tuple[str, str]:
    """Return broad authoring category + confidence without guessing unresolved classes."""
    if type_id in PICKUPS:
        return "pickup", "CONFIRMED"
    if type_id in OBJECTIVE_ITEMS:
        return "objective_item", "CONFIRMED"
    if type_id in DOOR_INTERACTABLES:
        return "door_or_interactable", "CONFIRMED"
    if type_id in CONTROLLERS:
        return "controller_or_trigger", "CONFIRMED" if type_id in {34,81,100,133,134} else "HIGH_CONFIDENCE"
    if type_id in CONTROLLER_CANDIDATES:
        return "controller_or_interactable", "HIGH_CONFIDENCE"
    if type_id in CIVILIANS:
        return "civilian_actor", "CONFIRMED"
    if type_id in STANDARD_RANGED or type_id in SPREAD_RANGED or type_id in {41,104,121}:
        return "hostile_combat_actor", "CONFIRMED"
    if type_id in CONTACT_HAZARDS:
        return "contact_hazard_or_destructible", "CONFIRMED"
    if type_id == 46:
        return "vehicle_prop", "CONFIRMED"
    if type_id == 113:
        return "destructible_loot_prop", "CONFIRMED"
    if type_id == 3:
        return "hostile_actor", "HIGH_CONFIDENCE"
    return "unresolved", "HYPOTHESIS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"wrong ROM size: {len(rom)}")
    digest = hashlib.sha1(rom).hexdigest()
    if digest != EXPECTED_SHA1:
        raise SystemExit(f"wrong base ROM SHA-1: {digest}")

    counts, scenes = placement_info(rom)
    assert len(counts) == 128 and sum(counts.values()) == 2449

    rows = []
    named = 0
    kind_counts = Counter()
    presentation_counts = Counter()
    for type_id in sorted(counts):
        natives = reachable_natives(rom, type_id)
        presentation = first_presentation_calls(rom, type_id)
        pclass = presentation_classification(presentation)
        presentation_counts[pclass] += 1

        identity = None
        if type_id in IDENTITY:
            label, status = IDENTITY[type_id]
            identity = {"label": label, "status": status}
            named += 1

        kind, kind_status = authoring_kind(type_id)
        kind_counts[kind] += 1
        roles = []
        if type_id in CIVILIANS:
            roles.append({"role": "civilian", "status": "CONFIRMED"})
        if type_id in STANDARD_RANGED:
            roles.append({"role": "standard_ranged_shooter", "status": "CONFIRMED"})
        if type_id in SPREAD_RANGED:
            roles.append({"role": "spread_shooter", "status": "CONFIRMED"})
        if type_id in CONTACT_HAZARDS:
            roles.append({"role": "contact_damage_hazard", "status": "CONFIRMED"})
        if type_id == 41:
            roles.append({"role": "special_directional_projectile_actor", "status": "CONFIRMED"})
        if type_id == 104:
            roles.append({"role": "boss_class_ranged_actor", "status": "CONFIRMED"})
        if type_id == 121:
            roles.append({"role": "boss_class_composite_ranged_actor", "status": "CONFIRMED"})
        if 0x002038 in natives:
            roles.append({"role": "uses_facing_movement_native", "status": "CONFIRMED"})

        rows.append({
            "type_id": type_id,
            "placements": counts[type_id],
            "scenes": sorted(scenes[type_id]),
            "representation": "direct_code" if rom[TYPE_SELECTOR_TABLE + type_id] == 0 else "scripted_vm",
            "initial_archetype_id": type_id,
            "initial_animation_descriptor": f"0x{u32(rom, ARCHETYPE_TABLE + type_id * 4):06X}",
            "hp_normal": rom[HP_NORMAL + type_id],
            "hp_hard": rom[HP_HARD + type_id],
            "damage_normal": rom[DAMAGE_NORMAL + type_id],
            "damage_hard": rom[DAMAGE_HARD + type_id],
            "presentation_classification": pclass,
            "presentation_calls": [
                {"mode": c["mode"], "arg0": f"0x{c['arg0']:04X}", "arg1": f"0x{c['arg1']:04X}"}
                for c in presentation["calls"]
            ],
            "authoring_kind": {"value": kind, "status": kind_status},
            "identity": identity,
            "mechanical_roles": roles,
        })

    report = {
        "schema": "truerecall.semantic_authoring_catalog.v3",
        "base_sha1": digest,
        "type_count": len(counts),
        "placement_count": sum(counts.values()),
        "named_identity_count": named,
        "unlabeled_identity_count": len(counts) - named,
        "authoring_kind_counts": dict(sorted(kind_counts.items())),
        "presentation_coverage": dict(sorted(presentation_counts.items())),
        "policy": "Labels/categories are emitted only from recorded evidence; unresolved values are explicit and are not inferred from graphics alone.",
        "types": rows,
    }
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
