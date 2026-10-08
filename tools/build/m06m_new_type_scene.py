#!/usr/bin/env python3
"""M0.6M: create an independent scripted type and place it directly in a scene."""
from __future__ import annotations

import argparse, hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROM_PROBE = HERE.parent / "rom_probe"
sys.path.insert(0, str(ROM_PROBE))

from vm_source_export import export_type_source
from vm_asm import assemble, parse_text
from vm_disasm import reachable, u32
from scene_object_compiler import build as build_scene
from object_stream_codec import parse_scene

EXPECTED_SIZE=2_097_152
EXPECTED_SHA1="d39174bed46ede85531b86df7ba49123ce2f8411"
TS=0x07A33C; TP=0x07953E; AT=0x079906; TF=0x07A24A
HPN=0x07A066; HPH=0x079F74; DMGN=0x079E82; DMGH=0x079D90; CHECK=0x018E
NEW_TYPE=1; DONOR=69; SCRIPT=0x1FB000; SCRIPT_REGION_START=0x1FABC3; SCENE_REGION_START=0x1FC000
EXPECTED_OUTPUT_SHA1="dc672e205686957c0c17655a387e7ea211eb9ef6"


def checksum(buf):
    total=0
    for off in range(0x200,len(buf),2): total=(total+((buf[off]<<8)|buf[off+1]))&0xFFFF
    return total


def set_u32(buf,off,val):
    buf[off:off+4]=val.to_bytes(4,"big")


def patch_type(raw:bytes)->bytes:
    assert raw[TS+NEW_TYPE]==0 and u32(raw,TP+NEW_TYPE*4)==0x009732
    start,src=export_type_source(raw,DONOR); assert start==0x1761F0
    old="  MOVI_W_D1 0x0005\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    new="  MOVI_W_D1 0x0006\n  ADD_D1_TO_D2\n  STORE_ABS_W_D2 0xFFFFFB72\n"
    assert src.count(old)==1
    blob,_=assemble(parse_text(src.replace(old,new)),SCRIPT)
    assert SCRIPT>=SCRIPT_REGION_START and SCRIPT+len(blob)<=SCENE_REGION_START
    assert all(x==0xFF for x in raw[SCRIPT:SCRIPT+len(blob)])
    out=bytearray(raw); out[SCRIPT:SCRIPT+len(blob)]=blob; out[TS+NEW_TYPE]=1; set_u32(out,TP+NEW_TYPE*4,SCRIPT)
    set_u32(out,AT+NEW_TYPE*4,u32(raw,AT+DONOR*4))
    for table in (TF,HPN,HPH,DMGN,DMGH): out[table+NEW_TYPE]=raw[table+DONOR]
    ins,_,_=reachable(bytes(out),SCRIPT,max_states=200000,max_stack=32); assert len(ins)==68
    return bytes(out)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path); ap.add_argument("output",type=Path); args=ap.parse_args(); raw=args.rom.read_bytes()
    assert len(raw)==EXPECTED_SIZE and hashlib.sha1(raw).hexdigest()==EXPECTED_SHA1
    typed=patch_type(raw)
    manifest={
      "schema":"truerecall.scene_object_patch.v1","scene_index":1,
      "free_start":"0x1FC000","free_end":"0x200000",
      "operations":[{"op":"add","stride":6,"type_id":1,"status_flags":"0x7800","x":256,"y":7984}]
    }
    out,report=build_scene(typed,manifest)
    assert out[TS+1]==1 and u32(out,TP+4)==SCRIPT and u32(out,AT+4)==u32(raw,AT+DONOR*4)
    scene=parse_scene(out,1); matches=[p for p in scene.placements if p.type_id==1 and p.x==256 and p.y==7984]
    assert len(matches)==1 and matches[0].stride==6
    assert u32(out,TP+69*4)==u32(raw,TP+69*4)
    assert int.from_bytes(out[CHECK:CHECK+2],"big")==checksum(out)
    digest=hashlib.sha1(out).hexdigest(); assert digest==EXPECTED_OUTPUT_SHA1
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_bytes(out)
    print("M0.6M new-class placement proof OK")
    print(f"type1_script=0x{SCRIPT:06X} placement_scene=1 x=256 y=7984")
    print(f"descriptor={report['new_descriptor']} object_lz={report['new_lz']} placements={report['base_placements']}->{report['new_placements']}")
    print(f"checksum=0x{checksum(out):04X}")
    print(f"output_sha1={digest}")

if __name__=="__main__": main()
