#!/usr/bin/env python3
"""Validate two retail special-combat actor families (types 41 and 121)."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from level_objects_probe import SCENE_COUNT,SCENE_TABLE,lzbeam_decode,u16,u32
EXPECTED_SIZE=2_097_152
EXPECTED_SHA1='d39174bed46ede85531b86df7ba49123ce2f8411'
TS=0x07A33C;TP=0x07953E

def placement_info(rom):
 c=Counter();sc=defaultdict(set)
 for s in range(SCENE_COUNT):
  rec=u32(rom,SCENE_TABLE+s*4);d=u32(rom,rec+0xA);n=u16(rom,d);pos=u16(rom,d+2);dec=lzbeam_decode(rom,u32(rom,d+6));rp=d+0xA;t=0;r=[]
  while t<n:
   st,q=rom[rp],rom[rp+1];rp+=2;assert st in(6,8) and q>0;r.append((st,q));t+=q
  for st,q in r:
   for _ in range(q):tid=u16(dec,pos)&0x3ff;c[tid]+=1;sc[tid].add(s);pos+=st
 return c,sc

def script_blob(rom,tid,size=0x1200):
 assert rom[TS+tid]==1
 s=u32(rom,TP+tid*4)
 return s,rom[s:min(len(rom),s+size)]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('rom',type=Path);ap.add_argument('--json',type=Path);a=ap.parse_args();rom=a.rom.read_bytes()
 assert len(rom)==EXPECTED_SIZE;digest=hashlib.sha1(rom).hexdigest();assert digest==EXPECTED_SHA1
 counts,scenes=placement_info(rom)
 # Type41: two scene-17 actors; linked-init creates runtime type192.
 assert counts[41]==2 and sorted(scenes[41])==[17]
 s41,b41=script_blob(rom,41)
 assert bytes.fromhex('001c00c000f000e4000020d8') in b41  # 0xC0 = 192
 assert rom[TS+192]==1 and u32(rom,TP+192*4)==0x189E08
 b192=rom[0x189E08:0x18A300]
 assert bytes.fromhex('00840000282200a8006c0034') in b192
 assert bytes.fromhex('008400002b6800a8006c0038') in b192
 assert bytes.fromhex('00e400002038') in b192
 assert rom[0x079E82+192]==4 and rom[0x079D90+192]==6
 # Type121: one scene-4 actor, HP50/75; spawns standard projectile170 and offensive child186.
 assert counts[121]==1 and sorted(scenes[121])==[4]
 assert rom[0x07A066+121]==50 and rom[0x079F74+121]==75
 s121,b121=script_blob(rom,121,0x1800)
 assert bytes.fromhex('001c00aa00f000e4000020d8') in b121
 assert bytes.fromhex('001c00ba00f000e4000020d8') in b121
 assert rom[TS+170]==0 and u32(rom,TP+170*4)==0x00E10E
 assert rom[TS+186]==1 and u32(rom,TP+186*4)==0x16B4B2
 b186=rom[0x16B4B2:0x16B800]
 assert bytes.fromhex('00840000282200a8006c0034') in b186
 assert rom[0x079E82+186]==5 and rom[0x079D90+186]==5
 # Type186 itself creates linked type185, a small owner-following presentation/effect entity.
 assert bytes.fromhex('001c00b900f000e4000020d8') in b186
 report={'schema':'truerecall.special_attack.v1','base_sha1':digest,'families':[
  {'parent_type':41,'classification':'special_directional_projectile_actor','placements':2,'scenes':[17],'runtime_attack_type':192,'attack_actor_collision':'0x002822','attack_world_collision':'0x002B68','attack_damage_normal_hard':[4,6]},
  {'parent_type':121,'classification':'boss_class_composite_ranged_actor','placements':1,'scenes':[4],'hp_normal_hard':[50,75],'standard_projectile_type':170,'offensive_child_type':186,'offensive_child_actor_collision':'0x002822','offensive_child_damage_normal_hard':[5,5],'offensive_child_effect_type':185}
 ]}
 text=json.dumps(report,indent=2,sort_keys=True);print(text)
 if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__':main()
