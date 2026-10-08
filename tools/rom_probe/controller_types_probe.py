#!/usr/bin/env python3
"""Validate the retail placement classes whose primary role is invisible/controller logic."""
from __future__ import annotations
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
from level_objects_probe import SCENE_COUNT,SCENE_TABLE,lzbeam_decode,u16,u32
EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TS=0x07A33C;TP=0x07953E

def placements(rom):
 out=defaultdict(list)
 for s in range(SCENE_COUNT):
  scene=u32(rom,SCENE_TABLE+s*4);desc=u32(rom,scene+0xA);n=u16(rom,desc);pos=u16(rom,desc+2);dec=lzbeam_decode(rom,u32(rom,desc+6));rp=desc+0xA;total=0;runs=[]
  while total<n:
   stride,qty=rom[rp],rom[rp+1];rp+=2;assert stride in(6,8) and qty>0;runs.append((stride,qty));total+=qty
  for stride,qty in runs:
   for _ in range(qty):
    status=u16(dec,pos);tid=status&0x03FF;x=u16(dec,pos+2);y=u16(dec,pos+4)
    out[tid].append((s,x,y));pos+=stride
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
 assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
 p=placements(rom)
 # Direct-code paired scene-14 boundary triggers.
 assert rom[TS+10]==0 and u32(rom,TP+10*4)==0x0050F0
 assert rom[TS+101]==0 and u32(rom,TP+101*4)==0x00505A
 assert len(p[10])==7 and len(p[101])==7
 assert {s for s,_,_ in p[10]}=={14} and {s for s,_,_ in p[101]}=={14}
 assert {x for _,x,_ in p[10]}=={208} and {x for _,x,_ in p[101]}=={208}
 # Both routines read FC52 and manipulate global FA00/FC66 fields before object cleanup.
 for off in (0x00505A,0x0050F0):
  blob=rom[off:off+0x100]
  assert bytes.fromhex('3038fc52') in blob
  assert bytes.fromhex('3078fa00') in blob
  assert bytes.fromhex('3078fc66') in blob
  assert bytes.fromhex('4eb900010aca') in blob
 # Scene-14 state controller type34 toggles FC52 0 -> 1 and has no own presentation path.
 assert rom[TS+34]==1 and len(p[34])==3 and {s for s,_,_ in p[34]}=={14}
 s34=u32(rom,TP+34*4);b34=rom[s34:s34+0x80]
 assert bytes.fromhex('001c00000058fffffc52') in b34
 assert bytes.fromhex('001c00010058fffffc52') in b34
 # Type4 is an invisible randomized spawner: it creates runtime/type30 via linked-init and uses RNG native 0x217C.
 assert rom[TS+4]==1 and len(p[4])==1 and p[4][0][0]==13
 s4=u32(rom,TP+4*4);b4=rom[s4:s4+0x100]
 assert bytes.fromhex('001c001e00f000e4000020d8') in b4
 assert bytes.fromhex('00e40000217c') in b4
 # Spawned type30 is a damaging prop class with two presentation branches; the visual barrel label is external-to-probe reconstruction evidence.
 assert rom[0x079E82+30]==4 and rom[0x079D90+30]==7
 s30=u32(rom,TP+30*4);b30=rom[s30:s30+0x100]
 assert bytes.fromhex('001c009a00f0001c000000f000e400001f9a') in b30
 assert bytes.fromhex('001c009c00f0001c000000f000e400001f9a') in b30
 rows={
  'type4':{'role':'randomized_damaging_prop_spawner','placements':p[4]},
  'type10':{'role':'scene14_camera_scroll_boundary_trigger_A','placements':p[10]},
  'type34':{'role':'scene14_scroll_state_controller','placements':p[34]},
  'type101':{'role':'scene14_camera_scroll_boundary_trigger_B','placements':p[101]},
  'spawned_type30':{'role':'damaging_barrel_like_prop','damage_normal_hard':[4,7],'selectors':['0x009A','0x009C']}
 }
 report={'schema':'truerecall.controller_types.v1','base_sha1':digest,'confirmed_or_high_confidence':rows,'notes':{'type10_101':'paired direct-code triggers share X=208 and alternate along the vertical scene-14 corridor; exact upper/lower naming intentionally withheld','type4_30':'spawner mechanics are confirmed; barrel visual identity comes from reconstructed initial frames'}}
 text=json.dumps(report,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
