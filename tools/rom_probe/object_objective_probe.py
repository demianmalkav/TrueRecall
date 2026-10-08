#!/usr/bin/env python3
"""Recover objective/key object semantics from the True Lies retail ROM.

Uses the object VM scripts, FC54 mission-flag word and the game's own message
string table. The output contains labels and structural evidence only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from level_objects_probe import SCENE_COUNT, SCENE_TABLE, lzbeam_decode, u16, u32

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1="d39174bed46ede85531b86df7ba49123ce2f8411"
TYPE_POINTER_TABLE=0x07953E
MESSAGE_TABLE=0x0063DC
MISSION_FLAGS=0xFFFFFC54


def placed_by_scene(rom: bytes) -> tuple[Counter[int],dict[int,list[int]]]:
    counts=Counter(); scenes={}
    for scene_index in range(SCENE_COUNT):
        scene=u32(rom,SCENE_TABLE+scene_index*4)
        desc=u32(rom,scene+0x0A)
        count=u16(rom,desc); start=u16(rom,desc+2); source=u32(rom,desc+6)
        decoded=lzbeam_decode(rom,source)
        runs=[]; rp=desc+0x0A; total=0
        while total<count:
            stride=rom[rp]; quantity=rom[rp+1]; rp+=2
            runs.append((stride,quantity)); total+=quantity
        pos=start
        for stride,quantity in runs:
            for _ in range(quantity):
                type_id=u16(decoded,pos)&0x03FF
                counts[type_id]+=1
                scenes.setdefault(type_id,[]).append(scene_index)
                pos+=stride
    return counts,scenes


def message(rom: bytes, message_id: int) -> str:
    ptr=u16(rom,MESSAGE_TABLE+message_id)
    end=rom.find(b"$",ptr)
    assert end>=ptr
    return rom[ptr:end].decode("latin1").replace(">"," ").replace("<"," ")


def script_has(rom: bytes,type_id: int,pattern: bytes,window: int=0x800) -> bool:
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    return rom.find(pattern,start,min(start+window,len(rom)))>=0


def flag_set_pattern(bit: int) -> bytes:
    return bytes.fromhex("0028fffffc54") + bytes.fromhex("0080") + bit.to_bytes(2,"big") + bytes.fromhex("00b40058fffffc54")


def flag_test_pattern(bit: int) -> bytes:
    return bytes.fromhex("0028fffffc54") + bytes.fromhex("0080") + bit.to_bytes(2,"big") + bytes.fromhex("00b0")


def message_pattern(message_id: int) -> bytes:
    return bytes.fromhex("001c") + message_id.to_bytes(2,"big") + bytes.fromhex("00f0001c030000f000e40000af08")


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("--json",type=Path)
    args=ap.parse_args(); rom=args.rom.read_bytes()
    assert len(rom)==EXPECTED_SIZE
    digest=hashlib.sha1(rom).hexdigest(); assert digest==EXPECTED_SHA1

    # FC06 is the message-table offset; rendering indexes the word table at 0x63DC.
    assert rom[0x00623A:0x006258] == bytes.fromhex("3038fc0641f9000063dc30300000223c000063dc0281ffff000080412240")
    # FC54 is explicitly cleared during scene/mission setup.
    assert rom[0x000FBA:0x000FC0] == bytes.fromhex("4278fc5431fc")

    counts,scenes=placed_by_scene(rom)

    labels=[
        (63,"security_passcard",0x8000,[0x0A,0x0C]),
        (58,"gate_key",0x8000,[0x2C]),
        (60,"subway_lever",0x4000,[0x3A,0x3C]),
        (55,"palace_key",0x0400,[0x56]),
        (56,"catacombs_key",0x0800,[0x58]),
        (57,"brass_key",0x1000,[0x5A]),
        (64,"alpha_security_pass",0x1000,[0x78]),
        (65,"beta_security_pass",0x2000,[0x7A]),
        (66,"gamma_security_pass",0x4000,[0x7C]),
        (67,"delta_security_pass",0x8000,[0x7E]),
    ]
    rows=[]
    for type_id,name,bit,message_ids in labels:
        assert script_has(rom,type_id,flag_set_pattern(bit))
        assert all(script_has(rom,type_id,message_pattern(mid)) for mid in message_ids)
        rows.append({
            "type_id":type_id,"name":name,"status":"CONFIRMED","mission_flag":f"0x{bit:04X}",
            "placements":counts[type_id],"scenes":sorted(set(scenes.get(type_id,[]))),
            "messages":[{"id":f"0x{mid:02X}","text":message(rom,mid)} for mid in message_ids],
        })

    # China reuses one type for three sequential bomb-disarming keys.
    assert counts[9]==3 and sorted(scenes[9])==[9,10,11]
    for mid in (0x62,0x64,0x66):
        assert script_has(rom,9,message_pattern(mid))
    for bit in (0x2000,0x4000,0x8000):
        assert script_has(rom,9,flag_set_pattern(bit))
    rows.append({
        "type_id":9,"name":"bomb_disarming_key","status":"CONFIRMED","placements":3,"scenes":[9,10,11],
        "progression_flags":["0x2000","0x4000","0x8000"],
        "messages":[{"id":f"0x{mid:02X}","text":message(rom,mid)} for mid in (0x62,0x64,0x66)],
    })

    controllers=[
        (13,"security_passcard_door",0x8000,[0x04]),
        (16,"palace_gate",0x0400,[0x5C]),
        (17,"catacombs_gate",0x0800,[0x5E]),
        (18,"locked_gate_palace_key_profile",0x0400,[0x60]),
        (77,"alpha_pass_door",0x1000,[0x70]),
        (78,"beta_pass_door",0x2000,[0x72]),
        (79,"gamma_pass_door",0x4000,[0x74]),
        (80,"delta_pass_door",0x8000,[0x76]),
        (87,"subway_signal_box",0x4000,[0x34,0x36,0x38]),
    ]
    control_rows=[]
    for type_id,name,bit,message_ids in controllers:
        assert script_has(rom,type_id,flag_test_pattern(bit))
        found=[mid for mid in message_ids if script_has(rom,type_id,message_pattern(mid))]
        assert found
        control_rows.append({
            "type_id":type_id,"name":name,"status":"CONFIRMED","required_flag":f"0x{bit:04X}",
            "placements":counts[type_id],"scenes":sorted(set(scenes.get(type_id,[]))),
            "messages":[{"id":f"0x{mid:02X}","text":message(rom,mid)} for mid in found],
        })

    report={
        "schema":"truerecall.object_objectives.v1","base_sha1":digest,
        "mission_flag_ram":"FFFFFC54","message_offset_ram":"FFFFFC06","message_pointer_table":"0x0063DC",
        "objective_items":rows,"gates_and_controllers":control_rows,
        "scene_mapping_evidence":{
            "china":"bomb-disarming-key type 9 appears exactly once in scenes 9, 10 and 11",
            "refinery":"Alpha/Beta/Gamma/Delta pass pickups and matching pass doors are concentrated in scene 13",
        },
    }
    text=json.dumps(report,indent=2,sort_keys=True); print(text)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True); args.json.write_text(text+"\n",encoding="utf-8")


if __name__=="__main__": main()
