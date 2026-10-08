#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from vm_disasm import EXPECTED_SIZE,EXPECTED_SHA1,TYPE_SELECTOR_TABLE,TYPE_POINTER_TABLE,reachable,u32

SCENE_TABLE=0x013B4A
CURRENT_SCENE=0xFFFFFC42
REQUESTED_SCENE=0xFFFFFC3A
ENTRY_PARAM=0xFFFFFC3E
TRANSITION_FLAGS=0xFFFFFC46
TRANSITION_NATIVE=0x002482
Y_DISTANCE_NATIVE=0x00221A
TRANSITION_TYPES=(135,136,137,138)
AUTO_DOOR_TYPES=(14,15)

def native_calls(rom:bytes,type_id:int):
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    insns,_labels,_states=reachable(rom,start,max_states=200000,max_stack=32)
    return [i.get('operand') for i in insns.values() if i['op']==0x00E4]

def has_immediate(rom:bytes,type_id:int,value:int):
    start=u32(rom,TYPE_POINTER_TABLE+type_id*4)
    insns,_labels,_states=reachable(rom,start,max_states=200000,max_stack=32)
    return any(i['op'] in (0x001C,0x0080) and i.get('operand')==value for i in insns.values())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args()
    rom=a.rom.read_bytes();assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1

    # 0x10CFA begins by multiplying FC42 by four and indexing the scene pointer table at 0x13B4A.
    assert rom[0x010CFA:0x010D0C]==bytes.fromhex('3038fc42d040d04041f900013b4a20700000')

    # Transition native: linked object pointer from current+0x32; byte +7 -> FC3E;
    # signed byte +6 selects a relative scene delta, added to FC42 -> FC3A; FC46 flags transition.
    assert rom[0x002482:0x0024C6]==bytes.fromhex(
        '302d0032673c304010280007488031c0fc3e1028000648806714d078fc4231c0fc3a00780008fc464ef9000119f43038fc4231c0fc3a00780010fc464ef9000119f4'
    )

    # Actor-contact callback 0x28B0 special-cases player F9F8 and signals the linked object.
    assert rom[0x0028B0:0x0028C8]==bytes.fromhex('b4f8f9f86610304d32280030670832410069100000064e75')

    transition_rows=[]
    for tid in TRANSITION_TYPES:
        assert rom[TYPE_SELECTOR_TABLE+tid]==1
        calls=native_calls(rom,tid)
        assert TRANSITION_NATIVE in calls
        # All four install 0x28B0 into object+0x34 in their reachable prefix.
        start=u32(rom,TYPE_POINTER_TABLE+tid*4)
        insns,_labels,_states=reachable(rom,start,max_states=200000,max_stack=32)
        assert any(i['op']==0x0084 and i.get('operand')==0x000028B0 for i in insns.values())
        transition_rows.append({'type_id':tid,'role':'scene_transition_surface','status':'CONFIRMED'})

    # Native 0x221A wraps 0x18D6 with current object and F9F8 player; 0x18D6
    # returns abs(word current+0x14 - word player+0x14).
    assert rom[0x00221A:0x00222C]==bytes.fromhex('304d3278f9f84eb9000018d64ef9000119f4')
    assert rom[0x0018D6:0x0018E4]==bytes.fromhex('30280014906900146a0244404e75')

    door_rows=[]
    for tid in AUTO_DOOR_TYPES:
        calls=native_calls(rom,tid)
        assert Y_DISTANCE_NATIVE in calls
        assert has_immediate(rom,tid,0x0032)  # 50-unit Y-distance threshold
        assert has_immediate(rom,tid,0x001D) and has_immediate(rom,tid,0x0015) # paired SFX/event params
        door_rows.append({'type_id':tid,'role':'automatic_proximity_door_variant','status':'HIGH_CONFIDENCE','axis':'object+0x14','threshold':50})

    report={
      'schema':'truerecall.scene_transition_and_door.v1','base_sha1':digest,
      'confirmed_globals':{
        'current_scene_word':'FFFFFC42','requested_scene_word':'FFFFFC3A','entry_parameter_word':'FFFFFC3E','transition_flags_word':'FFFFFC46','scene_table':'0x013B4A'
      },
      'transition_native':{'address':'0x002482','linked_object_field':'object+0x32','relative_scene_delta_byte':'linked+0x06','entry_parameter_byte':'linked+0x07'},
      'scene_transition_types':transition_rows,
      'proximity_distance_native':{'address':'0x00221A','engine_helper':'0x0018D6','semantic':'absolute difference of object/player word +0x14'},
      'automatic_door_types':door_rows,
      'notes':'Transition-surface mechanics are instruction-level confirmed. Door naming combines the proven proximity/animation behavior with reconstructed initial presentation; therefore door identity is held at HIGH_CONFIDENCE rather than pure code-only CONFIRMED.'
    }
    text=json.dumps(report,indent=2,sort_keys=True);print(text)
    if a.json:a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
